"""WebSocket endpoints for real-time entity state updates."""

import json
import re
from typing import Dict, Any, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Strict Home Assistant entity_id format: domain.object_name
# Only lowercase letters, digits, underscores, and hyphens allowed.
# Domain must be 1-32 chars, object name up to 64 chars.
ENTITY_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{0,32}\.[a-z_][a-z0-9_-]{0,64}$")


def validate_entity_id(entity_id: str) -> bool:
    """Validate that an entity_id matches Home Assistant format.

    Returns True if valid, False otherwise.
    Prevents injection attacks via malformed entity IDs.
    """
    return bool(ENTITY_ID_PATTERN.match(entity_id))


class ConnectionManager:
    """Manage active WebSocket connections and broadcast messages."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []
        # Track which entity IDs each connection cares about
        self.subscriptions: Dict[WebSocket, set[str]] = {}

    async def connect(self, websocket: WebSocket):
        """Accept a WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.subscriptions[websocket] = set()
        logger.info(
            f"WebSocket connected. Total connections: {len(self.active_connections)}"
        )

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        self.subscriptions.pop(websocket, None)
        logger.info(
            f"WebSocket disconnected. Total connections: {len(self.active_connections)}"
        )

    async def broadcast(self, message: str):
        """Send a message to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")

    async def broadcast_changes(self, changes: List[Dict[str, Any]]):
        """Broadcast entity state changes to subscribed clients.

        Only sends changes for entities the client has subscribed to.
        If a client hasn't subscribed (empty set), send all changes.
        """
        message = json.dumps({"type": "state_changed", "changes": changes})

        for connection in self.active_connections:
            try:
                subs = self.subscriptions.get(connection, set())
                if not subs or any(c["entity_id"] in subs for c in changes):
                    await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting state change to client: {e}")


# Global manager instance
manager = ConnectionManager()


@router.websocket("/ws/entities")
async def websocket_entities(websocket: WebSocket):
    """WebSocket endpoint for real-time entity state updates.

    Real-time WebSocket connection for receiving live entity state changes from Home Assistant.
    Supports subscribe commands (e.g., 'subscribe:light.living_room') and ping/pong keepalive.
    """
    await manager.connect(websocket)

    try:
        # Send initial connection message
        await websocket.send_json(
            {"type": "connected", "message": "Connected to HA Dashboard WebSocket"}
        )

        # Keep the connection open and listen for messages
        while True:
            data = await websocket.receive_text()

            # Handle different message types from clients
            if data == "ping":
                await websocket.send_json({"type": "pong"})
            elif data.startswith("subscribe:"):
                # Client can subscribe to specific entity updates
                raw_entity_id = data.split(":")[1]
                if not validate_entity_id(raw_entity_id):
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": f"Invalid entity_id format: {raw_entity_id}",
                        }
                    )
                    continue
                manager.subscriptions[websocket].add(raw_entity_id)
                logger.info(f"Client subscribed to {raw_entity_id}")
                await websocket.send_json(
                    {"type": "subscribed", "entity_id": raw_entity_id}
                )
            elif data.startswith("unsubscribe:"):
                # Client can unsubscribe from specific entities
                raw_entity_id = data.split(":")[1]
                if not validate_entity_id(raw_entity_id):
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": f"Invalid entity_id format: {raw_entity_id}",
                        }
                    )
                    continue
                manager.subscriptions[websocket].discard(raw_entity_id)
                logger.info(f"Client unsubscribed from {raw_entity_id}")
                await websocket.send_json(
                    {"type": "unsubscribed", "entity_id": raw_entity_id}
                )
            else:
                # Echo back for now (can be extended for other commands)
                await websocket.send_text(f"Received: {data}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        manager.disconnect(websocket)
        logger.error(f"WebSocket error: {e}")


@router.get(
    "/ws/status",
    summary="WebSocket connection status",
    description="Returns the current number of active WebSocket connections and overall status.",
)
async def websocket_status():
    return {
        "active_connections": len(manager.active_connections),
        "status": "running" if manager.active_connections else "idle",
    }
