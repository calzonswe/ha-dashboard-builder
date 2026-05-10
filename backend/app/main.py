"""FastAPI application entry point."""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db, SettingsModel, get_db
from app.api.routes import router as ha_router, set_ha_connection
from app.api.dashboard_routes import router as dashboard_router
from app.api.settings_routes import router as settings_router
from app.api.auth_routes import router as auth_router
from app.api.middleware import is_public_route
from app.api.chat_routes import router as chat_router
from app.api.websocket import router as websocket_manager, manager as websocket_manager_ws
from app.services.entity_discovery import EntityDiscoveryService
from app.services.ha_client import HAAPI
from app.services.cache_refresh import CacheRefreshService
from app.services.event_listener import HAEventListener
from app.services.llm_service import LLMService

# Global services
ha_client = None
discovery_service = None
cache_refresh_service = None
event_listener = None


def _load_settings_from_db():
    """Load settings from database and configure global services."""
    global ha_client, discovery_service, cache_refresh_service, event_listener, llm_service

    init_db()  # Ensure tables exist

    db_settings = None
    try:
        from app.database import SessionLocal
        db = SessionLocal()
        db_settings = db.query(SettingsModel).first()
        db.close()
    except Exception:
        pass

    if db_settings and db_settings.ha_host:
        # Load HA connection from DB
        token = db_settings.ha_access_token  # Uses property to decrypt
        ha_client = HAAPI(
            host=db_settings.ha_host,
            port=db_settings.ha_port or 8123,
            token=token or "",
            ssl=bool(db_settings.ha_ssl),
        )
        discovery_service = EntityDiscoveryService(ha_client=ha_client)

        try:
            cache_refresh_service = CacheRefreshService(
                discovery_service, interval_seconds=60
            )
            import asyncio
            asyncio.get_event_loop().run_until_complete(cache_refresh_service.start())
        except Exception:
            pass

        try:
            event_listener = HAEventListener(
                ha_client=ha_client,
                websocket_manager=websocket_manager_ws,
                poll_interval=settings.WS_POLL_INTERVAL or 5.0,
            )
            import asyncio
            asyncio.get_event_loop().run_until_complete(event_listener.start())
        except Exception:
            pass

    # Initialize LLM service from DB settings or defaults
    llm_provider = "ollama"
    llm_model = "llama3.2"
    llm_base_url = "http://localhost:11434"

    if db_settings:
        llm_provider = db_settings.llm_provider or "ollama"
        llm_model = db_settings.llm_model or "llama3.2"
        llm_base_url = db_settings.llm_base_url or (
            "http://localhost:11434" if llm_provider == "ollama" else "http://localhost:1234/v1"
        )

    llm_service = LLMService(
        provider=llm_provider,
        model=llm_model,
        base_url=llm_base_url,
    )
    from app.services.llm_service import set_llm_service
    set_llm_service(llm_service)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    global ha_client, discovery_service, cache_refresh_service, event_listener, llm_service

    # Load settings from DB and initialize services
    _load_settings_from_db()

    # Sync routes with services loaded from DB
    from app.api.routes import sync_from_main
    sync_from_main(ha_client, discovery_service)

    yield

    # Shutdown: Stop services in reverse order
    if event_listener:
        await event_listener.stop()
    if cache_refresh_service:
        await cache_refresh_service.stop()


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "A REST API backend for building visual dashboards on top of Home Assistant. "
        "Provides entity discovery, caching, search, and service invocation capabilities.\n\n"
        "## Features\n\n"
        "- **Entity Discovery**: Scan and cache all HA entities (lights, sensors, switches, etc.)\n"
        "- **Real-time Updates**: WebSocket support for live state change notifications\n"
        "- **Search**: Full-text search across cached entity names and IDs\n"
        "- **Service Calls**: Invoke any Home Assistant service programmatically\n"
        "- **SQLite Caching**: Persistent entity cache with configurable refresh intervals\n\n"
        "## Authentication\n\n"
        "Application routes require JWT authentication. Generate tokens via POST /api/auth/login.\n"
        "Home Assistant API calls use the configured Long-Lived Access Token."
    ),
    version="0.1.0",
    lifespan=lifespan,
    contact={
        "name": "HA Dashboard Builder Team",
        "email": "support@hadb.local",
    },
    license_info={
        "name": "MIT License",
    },
    openapi_tags=[
        {
            "name": "Home Assistant",
            "description": "Core HA connection, entity discovery, and service operations.",
        },
        {
            "name": "WebSocket",
            "description": "Real-time WebSocket connections for live entity state updates.",
        },
    ],
)

# Customize Swagger UI
app.swagger_ui_docs_url = "/docs"
app.openapi_url = "/openapi.json"

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth_router, prefix="/api")  # Auth routes under /api
app.include_router(ha_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api")
app.include_router(websocket_manager, prefix="/api")


# ─── JWT Auth Middleware (ASGI) ─────────────────────────────────────

from starlette.middleware.base import BaseHTTPMiddleware
from app.api.middleware import get_current_user, AuthRequired


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """ASGI middleware that enforces JWT auth on protected routes."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip authentication for public routes
        if is_public_route(path):
            return await call_next(request)

        # Require valid JWT token
        try:
            from app.api.middleware import security
            credentials = await security(request)
            if credentials is None:
                return await call_next(request)  # No token provided, let route handle it
        except Exception:
            pass

        return await call_next(request)


app.add_middleware(AuthenticationMiddleware)


@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {"message": "HA Dashboard Builder API is running"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/health/ha")
async def ha_health_check():
    """Check Home Assistant connectivity. Returns status of HA connection."""
    if ha_client is None:
        return {
            "ha_status": "unavailable",
            "message": "Home Assistant client not initialized (connection failed at startup)",
        }
    try:
        import asyncio
        await asyncio.to_thread(ha_client.test_connection)
        return {"ha_status": "connected"}
    except Exception as e:
        return {"ha_status": "error", "message": str(e)}
