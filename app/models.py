"""Pydantic models for HA Integration API."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class EntityType(str, Enum):
    """Entity type categories."""

    BINARY_SENSOR = "binary_sensor"
    SENSOR = "sensor"
    SWITCH = "switch"
    LIGHT = "light"
    COVER = "cover"
    FAN = "fan"
    CLIMATE = "climate"
    MEDIA_PLAYER = "media_player"
    LOCK = "lock"
    CAMERA = "camera"
    VACUUM = "vacuum"
    DOOR_SENSOR = "door"
    WINDOW_SENSOR = "window"


class Entity(BaseModel):
    """Represents a Home Assistant entity."""

    entity_id: str
    state: str
    attributes: Dict[str, Any]
    last_changed: datetime
    last_updated: datetime
    context: Optional[Dict[str, Any]] = None
    device_info: Optional[Dict[str, Any]] = None
    area_name: Optional[str] = None
    domain: str
    entity_type: EntityType

    @classmethod
    def from_ha_state(cls, state_obj: dict) -> "Entity":
        """Create Entity from Home Assistant state object."""
        attrs = state_obj.get("attributes", {})
        last_changed = datetime.fromisoformat(state_obj["last_changed"])
        last_updated = datetime.fromisoformat(state_obj["last_updated"])

        # Extract domain and entity type
        parts = state_obj["entity_id"].split(".")
        domain = parts[0] if len(parts) >= 2 else "unknown"
        try:
            entity_type = EntityType(domain)
        except ValueError:
            entity_type = EntityType.SENSOR

        return cls(
            entity_id=state_obj["entity_id"],
            state=str(state_obj.get("state", "")),
            attributes=attrs,
            last_changed=last_changed,
            last_updated=last_updated,
            context=state_obj.get("context"),
            domain=domain,
            entity_type=entity_type,
        )


class EntityFilter(BaseModel):
    """Filters for querying entities."""

    domains: Optional[List[str]] = None
    types: Optional[List[EntityType]] = None
    areas: Optional[List[str]] = None
    device_ids: Optional[List[str]] = None
    search: Optional[str] = None


class StateChange(BaseModel):
    """Tracks a state change event."""

    entity_id: str
    old_state: str
    new_state: str
    changed_at: datetime
    area_name: Optional[str] = None


class DiscoveryResult(BaseModel):
    """Result of entity discovery."""

    total_entities: int
    entities: List[Entity]
    errors: List[str]
    warnings: List[str]
    discovered_at: datetime


class HealthStatus(BaseModel):
    """Health status of the HA connection."""

    connected: bool
    ha_url: str
    last_check: Optional[datetime] = None
    error: Optional[str] = None


class WebSocketMessage(BaseModel):
    """WebSocket message format."""

    type: str  # state_changed, entity_list, error, ping, pong
    payload: Any = None
