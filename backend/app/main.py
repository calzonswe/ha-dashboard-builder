"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.api.routes import router as ha_router
from app.api.dashboard_routes import router as dashboard_router
from app.api.websocket import router as websocket_router, manager as websocket_manager
from app.services.entity_discovery import EntityDiscoveryService
from app.services.ha_client import HAAPI
from app.services.cache_refresh import CacheRefreshService
from app.services.event_listener import HAEventListener


# Global services
ha_client = None
discovery_service = None
cache_refresh_service = None
event_listener = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    global ha_client, discovery_service, cache_refresh_service, event_listener

    # Startup: Initialize database and services
    init_db()

    # Initialize HA client and discovery service
    ha_client = HAAPI(
        host=settings.HA_HOST,
        port=settings.HA_PORT,
        token=settings.HA_ACCESS_TOKEN,
    )
    discovery_service = EntityDiscoveryService(ha_client=ha_client)

    # Start cache refresh service
    cache_refresh_service = CacheRefreshService(discovery_service, interval_seconds=60)
    await cache_refresh_service.start()

    # Start HA event listener for real-time state updates
    event_listener = HAEventListener(
        ha_client=ha_client,
        websocket_manager=websocket_manager,
        poll_interval=settings.WS_POLL_INTERVAL or 5.0,
    )
    await event_listener.start()

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
        "All endpoints require a valid Long-Lived Access Token from your Home Assistant instance. "
        "Generate tokens in HA Settings → Security → Long-Lived Access Tokens."
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
app.include_router(ha_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(websocket_router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {"message": "HA Dashboard Builder API is running"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
