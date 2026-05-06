"""FastAPI application with WebSocket and SSE endpoints for real-time HA state updates."""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Callable, Dict, List, Literal, Optional, Set

import aiohttp
import uvicorn
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.config import settings
from app.ha_client import HAClient, HAConnectionError, HATimeoutError
from app.models import Entity, EntityType, StateChange, WebSocketMessage

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic models for WebSocket / SSE messages
# ---------------------------------------------------------------------------


class EntityStateUpdate(BaseModel):
    """A single entity state change broadcast to connected clients."""

    type: Literal["state_changed"] = "state_changed"  # type: ignore[assignment]
    entity_id: str
    old_state: Optional[str] = None
    new_state: str
    attributes: Dict[str, Any] = Field(default_factory=dict)
    changed_at: datetime
    area_name: Optional[str] = None


class EntityListUpdate(BaseModel):
    """Full entity list snapshot broadcast on connect."""

    type: Literal["entity_list"] = "entity_list"  # type: ignore[assignment]
    entities: List[Dict[str, Any]]
    total_count: int
    received_at: datetime


class ServerPing(BaseModel):
    """Server-side ping to keep connections alive."""

    type: Literal["ping"] = "ping"  # type: ignore[assignment]
    timestamp: datetime


class ServerPongResponse(BaseModel):
    """Client pong response (for health checks)."""

    type: Literal["pong"] = "pong"  # type: ignore[assignment]
    timestamp: datetime


class ErrorMessage(BaseModel):
    """Error message sent to clients."""

    type: Literal["error"] = "error"  # type: ignore[assignment]
    code: int
    detail: str


# ---------------------------------------------------------------------------
# HA Event Subscriber – subscribes to Home Assistant events via aiohttp
# ---------------------------------------------------------------------------


class HAEventSubscriber:
    """Subscribes to Home Assistant's event stream and broadcasts state changes.

    Uses the WebSocket API /api/events as the primary subscription mechanism,
    with graceful fallback when unavailable.
    """

    def __init__(
        self,
        ha_url: str = "http://localhost:8123",
        token: str = "",
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        self.ha_url = ha_url.rstrip("/")
        self.token = token
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._session: Optional[aiohttp.ClientSession] = None
        self._running = False

    # -- session management --------------------------------------------------

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp ClientSession for event streaming."""
        if self._session is None or self._session.closed:
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
                headers["X-HA-access"] = self.token

            connector = aiohttp.TCPConnector(verify_ssl=False)
            self._session = aiohttp.ClientSession(
                base_url=f"{self.ha_url}/api/",
                headers=headers,
                connector=connector,
            )
        return self._session

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    # -- event subscription --------------------------------------------------

    async def subscribe(
        self, on_state_change: Callable[[Dict[str, Any]], "Any"]
    ) -> None:
        """Start subscribing to HA events.

        Parameters
        ----------
        on_state_change : callable
            Async callback invoked with each state_changed event dict.
        """
        self._running = True
        self._on_state_change = on_state_change  # type: ignore[attr-defined]
        logger.info("HAEventSubscriber starting subscription")

        while self._running:
            try:
                session = await self._get_session()
                url = "events"  # resolves to {base_url}/events

                async with session.ws_connect(
                    url, heartbeat=30.0, compress=False
                ) as ws:
                    logger.info("Connected to HA event stream")
                    async for msg in ws:
                        if not self._running:
                            break
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            try:
                                data = json.loads(msg.data)
                                await on_state_change(data)
                            except (json.JSONDecodeError, KeyError) as e:
                                logger.warning(f"Invalid event message: {e}")
                        elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                            logger.warning(
                                f"Event stream closed ({msg.type}), reconnecting..."
                            )
                            break

            except Exception as e:
                logger.error(f"Event subscription error: {e}")
                if self._running:
                    await asyncio.sleep(self.retry_delay)

    async def stop(self) -> None:
        """Signal the subscriber to stop."""
        self._running = False


# ---------------------------------------------------------------------------
# WebSocket Manager – tracks connected clients and broadcasts messages
# ---------------------------------------------------------------------------


class WebSocketManager:
    """Manages active WebSocket connections and broadcasts updates."""

    def __init__(self) -> None:
        self._connections: Dict[WebSocket, Set[str]] = {}  # ws -> {room}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, room: str = "default") -> None:
        """Accept and register a WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            if websocket not in self._connections:
                self._connections[websocket] = set()
            self._connections[websocket].add(room)

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        async with self._lock:
            self._connections.pop(websocket, None)

    async def broadcast(self, message: str, room: Optional[str] = None) -> None:
        """Send a message to all matching connections."""
        async with self._lock:
            targets = {ws for ws, rooms in self._connections.items() if room is None or room in rooms}

        for ws in targets:
            try:
                await ws.send_text(message)
            except Exception as e:
                logger.warning(f"Broadcast error to {ws}: {e}")

    async def send(self, websocket: WebSocket, message: str) -> None:
        """Send a single message to one connection."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.warning(f"Send error to client: {e}")


# ---------------------------------------------------------------------------
# Authentication Middleware – Bearer token check (only active if API key is set)
# ---------------------------------------------------------------------------


class AuthMiddleware:
    """Simple Bearer token authentication middleware.

    Only enforces auth when HA_INTEGRATION_API_KEY environment variable is set.
    Health endpoint (/api/health and /health) is always exempt.
    """

    def __init__(self, app: FastAPI) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        # Always allow health checks through
        if scope["type"] == "http":
            path = scope.get("path", "")
            if path.startswith("/health") or path.startswith("/api/health"):
                await self.app(scope, receive, send)
                return

        api_key = os.getenv("HA_INTEGRATION_API_KEY")
        if not api_key:
            # No API key configured — allow all requests through
            await self.app(scope, receive, send)
            return

        # Check Authorization header from scope headers
        headers = {}
        for key, value in scope.get("headers", []):
            if isinstance(key, bytes):
                key = key.decode()
            if isinstance(value, bytes):
                value = value.decode()
            headers[key.lower()] = value

        auth_header = headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            response_body = json.dumps(
                {"detail": "Missing or invalid authorization header"}
            ).encode()
            await send(
                {
                    "type": "http.response.start",
                    "status": 401,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"content-length", str(len(response_body)).encode()),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": response_body})
            return

        token = auth_header[7:]  # Remove "Bearer " prefix
        if token != api_key:
            response_body = json.dumps(
                {"detail": "Invalid API key"}
            ).encode()
            await send(
                {
                    "type": "http.response.start",
                    "status": 403,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"content-length", str(len(response_body)).encode()),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": response_body})
            return

        # Auth passed — forward to the app
        await self.app(scope, receive, send)


# ---------------------------------------------------------------------------
# Module-level state for the event pipeline
# ---------------------------------------------------------------------------

_ws_manager: Optional[WebSocketManager] = None
_ha_client_ref: Optional[HAClient] = None
_sse_queues: List["asyncio.Queue"] = []  # type: ignore[type-arg]
_sse_stop_event: Optional[asyncio.Event] = None


def _get_ws_manager() -> WebSocketManager:
    """Lazy accessor for the WS manager (set during app creation)."""
    if _ws_manager is not None:
        return _ws_manager
    return WebSocketManager()


def get_sse_stop_event() -> asyncio.Event:
    """Get or create the SSE stop event."""
    global _sse_stop_event
    if _sse_stop_event is None:
        _sse_stop_event = asyncio.Event()
    return _sse_stop_event


# ---------------------------------------------------------------------------
# FastAPI Application Factory
# ---------------------------------------------------------------------------


def create_app(
    ha_client: Optional[HAClient] = None,
    event_subscriber: Optional[HAEventSubscriber] = None,
) -> FastAPI:
    """Create and configure the FastAPI application.

    Parameters
    ----------
    ha_client : HAClient, optional
        Pre-configured HAClient instance.  If not provided, one is created
        from settings.
    event_subscriber : HAEventSubscriber, optional
        Pre-configured subscriber.  If not provided, one is created from
        settings.

    Returns
    -------
    FastAPI
        Configured application instance.
    """
    global _ws_manager, _ha_client_ref

    app = FastAPI(
        title="HA Integration API",
        description="Real-time Home Assistant state updates via WebSocket and SSE.",
        version="0.1.0",
    )

    # Shared state – initialised once on startup
    ha_client: HAClient = ha_client or HAClient(
        base_url=settings.ha_url,
        token=settings.ha_token,
        timeout=settings.ha_timeout,
        max_retries=settings.ha_max_retries,
        retry_delay=settings.ha_retry_delay,
    )

    event_subscriber: HAEventSubscriber = event_subscriber or HAEventSubscriber(
        ha_url=settings.ha_url,
        token=settings.ha_token,
        max_retries=settings.ha_max_retries,
        retry_delay=settings.ha_retry_delay,
    )

    _ws_manager = WebSocketManager()
    _ha_client_ref = ha_client

    # ------------------------------------------------------------------
    # Startup / shutdown hooks
    # ------------------------------------------------------------------

    @app.on_event("startup")
    async def startup_event() -> None:
        """Start the HA event subscriber on application startup."""
        logger.info("Starting HA Integration API")
        try:
            await event_subscriber.subscribe(on_state_change=_handle_ha_event)
            logger.info("HA event subscription started successfully")
        except Exception as e:
            logger.error(f"Failed to start HA event subscription: {e}")

    @app.on_event("shutdown")
    async def shutdown_event() -> None:
        """Stop the subscriber, close client, and signal SSE streams to stop."""
        # Signal all SSE generators to stop
        if _sse_stop_event is not None:
            _sse_stop_event.set()
        await event_subscriber.stop()
        await ha_client.close()

    # ------------------------------------------------------------------
    # Global exception handlers – return clean JSON errors instead of 500 traces
    # ------------------------------------------------------------------

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc):  # type: ignore[asyncio]
        """Handle HTTP exceptions and preserve the original status code."""
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):  # type: ignore[asyncio]
        """Catch raw exceptions and return a clean JSON error response."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "type": "internal_error"},
        )

    # ------------------------------------------------------------------
    # REST endpoints (health, states)
    # ------------------------------------------------------------------

    @app.get("/api/health", tags=["health"])
    async def health_check() -> Dict[str, Any]:
        """Health check endpoint."""
        try:
            status = await ha_client.check_health()
            return {
                "status": status["status"],
                "ha_url": settings.ha_url,
                "connected": status.get("status") == "ok",
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "error", "ha_url": settings.ha_url, "connected": False}

    @app.get("/api/states", tags=["states"])
    async def get_states() -> List[Dict[str, Any]]:
        """Get current states of all entities."""
        try:
            return await ha_client.get_states()
        except Exception as e:
            logger.error(f"Failed to fetch states: {e}")
            raise

    @app.get("/api/states/{entity_id}", tags=["states"])
    async def get_state(entity_id: str) -> Dict[str, Any]:
        """Get the state of a single entity."""
        try:
            return await ha_client.get_state(entity_id)
        except Exception as e:
            logger.error(f"Failed to fetch state for {entity_id}: {e}")
            raise

    # ------------------------------------------------------------------
    # WebSocket endpoint – real-time state updates
    # ------------------------------------------------------------------

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        """WebSocket endpoint for real-time HA state changes.

        Clients connect here and receive state_changed events as they occur.
        On connection, a full entity list snapshot is also sent.
        """
        room = "default"  # Could be extended to support rooms/areas
        await _ws_manager.connect(websocket, room)

        # Send initial entity list snapshot
        try:
            states = await ha_client.get_states()
            entities_data = [
                {
                    "entity_id": s["entity_id"],
                    "state": str(s.get("state", "")),
                    "attributes": s.get("attributes", {}),
                    "last_changed": s.get("last_changed"),
                    "area_name": None,
                }
                for s in states
            ]
            snapshot = EntityListUpdate(
                entities=entities_data,
                total_count=len(entities_data),
                received_at=datetime.now(),
            )
            await _ws_manager.send(websocket, snapshot.model_dump_json())
        except Exception as e:
            logger.error(f"Failed to send initial entity list: {e}")

        # Listen for client messages (ping/pong)
        try:
            while True:
                data = await websocket.receive_text()
                try:
                    msg = json.loads(data)
                    if msg.get("type") == "pong":
                        pass  # Keep alive acknowledged
                except (json.JSONDecodeError, KeyError):
                    pass  # Ignore non-JSON or unrecognised messages
        except WebSocketDisconnect:
            logger.info("WebSocket client disconnected")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            await _ws_manager.disconnect(websocket)

    # ------------------------------------------------------------------
    # SSE fallback endpoint – Server-Sent Events
    # ------------------------------------------------------------------

    @app.get("/api/events/stream", response_class=None, tags=["sse"])
    async def sse_endpoint(
        area_name: Optional[str] = Query(None, description="Filter by area name"),
        entity_type: Optional[List[EntityType]] = Query(None),
    ):
        """SSE fallback for clients that don't support WebSockets.

        Streams state_changed events as Server-Sent Events.  Supports
        optional filtering by area and entity type.
        """
        from fastapi.responses import StreamingResponse

        async def event_generator():
            """Generate SSE-formatted events."""
            # Send initial snapshot
            try:
                states = await ha_client.get_states()
                entities_data = [
                    {
                        "entity_id": s["entity_id"],
                        "state": str(s.get("state", "")),
                        "attributes": s.get("attributes", {}),
                        "last_changed": s.get("last_changed"),
                        "area_name": None,
                    }
                    for s in states
                ]

                # Filter by area if requested
                if area_name:
                    entities_data = [
                        e for e in entities_data
                        if e["area_name"] == area_name or not area_name
                    ]

                snapshot = EntityListUpdate(
                    entities=entities_data,
                    total_count=len(entities_data),
                    received_at=datetime.now(),
                )
                yield f"event: entity_list\ndata: {snapshot.model_dump_json()}\n\n"
            except Exception as e:
                logger.error(f"SSE snapshot error: {e}")

            # Stream live events via a local queue
            event_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
            _sse_queues.append(event_queue)

            try:
                while True:
                    # Check if we should stop (set by shutdown hook)
                    if _sse_stop_event and _sse_stop_event.is_set():
                        break

                    try:
                        event_data = await asyncio.wait_for(
                            event_queue.get(), timeout=settings.ws_ping_interval * 2
                        )
                        if isinstance(event_data, dict):
                            data = event_data.get("event", {}).get("data", {})
                            entity_id = data.get("entity_id")
                            new_state_obj = data.get("new_state", {})

                            # Apply filters
                            if area_name and not (
                                data.get("area_name") == area_name or not area_name
                            ):
                                continue
                            if entity_type:
                                parts = entity_id.split(".")
                                domain = parts[0] if len(parts) >= 2 else "unknown"
                                try:
                                    et = EntityType(domain)
                                    if et not in entity_type:
                                        continue
                                except ValueError:
                                    continue

                            update = EntityStateUpdate(
                                type="state_changed",
                                entity_id=entity_id,
                                old_state=str(data.get("old_state")),
                                new_state=str(new_state_obj.get("state", "")),
                                attributes=new_state_obj.get("attributes", {}),
                                changed_at=datetime.now(),
                                area_name=data.get("area_name"),
                            )
                            yield f"event: state_changed\ndata: {update.model_dump_json()}\n\n"
                    except asyncio.TimeoutError:
                        # Send a keep-alive ping
                        ping = ServerPing(timestamp=datetime.now())
                        yield f":keepalive\nevent: ping\ndata: {ping.model_dump_json()}\n\n"
            finally:
                _sse_queues.remove(event_queue)

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # ------------------------------------------------------------------
    # Authentication middleware – Bearer token check (only active if API key is set)
    # ------------------------------------------------------------------

    app.add_middleware(AuthMiddleware)

    return app


# ---------------------------------------------------------------------------
# Module-level event handler – invoked by HAEventSubscriber callbacks
# ---------------------------------------------------------------------------


async def _handle_ha_event(event_data: Dict[str, Any]) -> None:
    """Callback invoked when HA publishes a state_changed event.

    Broadcasts to all WebSocket clients and pushes to SSE queues.
    """
    try:
        data = event_data.get("event", {}).get("data", {})
        entity_id = data.get("entity_id")
        new_state_obj = data.get("new_state", {})

        # Build the broadcast message
        update = EntityStateUpdate(
            type="state_changed",
            entity_id=entity_id,
            old_state=str(data.get("old_state")),
            new_state=str(new_state_obj.get("state", "")),
            attributes=new_state_obj.get("attributes", {}),
            changed_at=datetime.now(),
        )

        # Broadcast to WebSocket clients
        ws_mgr = _get_ws_manager()
        await ws_mgr.broadcast(update.model_dump_json())

        # Push to SSE event queues
        for queue in list(_sse_queues):
            try:
                await queue.put(event_data)
            except Exception as e:
                logger.warning(f"SSE queue push error: {e}")

    except Exception as e:
        logger.error(f"Error handling HA event: {e}")


# ---------------------------------------------------------------------------
# Module-level app instance (for uvicorn)
# ---------------------------------------------------------------------------

app = create_app()


# ---------------------------------------------------------------------------
# Run with uvicorn (when executed directly)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "app.api:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info",
    )
