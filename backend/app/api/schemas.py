"""API schemas for Home Assistant connection and entity discovery."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class HAConnectionRequest(BaseModel):
    """Request to connect to a Home Assistant instance.

    Provides the host address, port number, and authentication token needed
    to establish a secure connection to your Home Assistant instance.
    """

    host: str = Field(
        ...,
        description="Home Assistant hostname or IP address (e.g., 'homeassistant.local' or '192.168.1.50')",
        examples=["homeassistant.local", "192.168.1.50"],
    )
    port: int = Field(
        default=8123,
        ge=1,
        le=65535,
        description="Home Assistant web UI port (default: 8123)",
        examples=[8123],
    )
    token: str = Field(
        ...,
        description=(
            "Long-lived access token for Home Assistant API authentication. "
            "Generate in HA Settings → Security → Long-Lived Access Tokens."
        ),
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
    )


class HAConnectionResponse(BaseModel):
    """Response after connecting to Home Assistant.

    Returns connection status, host details, and the number of discovered entities.
    """

    status: str = Field(
        ...,
        description="Connection status: 'success' or an error message",
        examples=["success"],
    )
    host: str = Field(..., description="The connected Home Assistant hostname")
    port: int = Field(..., description="The connected Home Assistant port number")
    entities: Optional[int] = Field(
        None,
        description="Total number of entities found on the connected instance",
        examples=[42],
    )
    message: Optional[str] = Field(
        None,
        description="Additional status or error message",
        examples=["Connected successfully"],
    )


class EntitySummary(BaseModel):
    """Summary of discovered entities.

    Provides a high-level overview of all entities found during discovery,
    including counts by domain and area.
    """

    total_entities: int = Field(
        ...,
        description="Total number of entities discovered",
        examples=[42],
    )
    domains: List[str] = Field(
        ...,
        description="List of unique entity domains (e.g., 'light', 'sensor', 'switch')",
        examples=[["light", "sensor", "switch", "climate"]],
    )
    areas: List[str] = Field(
        ...,
        description="List of unique areas/rooms where entities are located",
        examples=[["Living Room", "Kitchen", "Bedroom"]],
    )
    cached_at: Optional[str] = Field(
        None,
        description="ISO 8601 timestamp when the cache was last updated",
        examples=["2024-05-06T10:30:00Z"],
    )


class EntityDiscoveryResponse(BaseModel):
    """Response from entity discovery.

    Returns the discovery status and a summary of all discovered entities.
    """

    status: str = Field(
        ...,
        description="Discovery status: 'success' or an error message",
        examples=["success"],
    )
    summary: Optional[EntitySummary] = Field(
        None,
        description="Summary object containing entity counts and categorization",
    )
    message: Optional[str] = Field(
        None,
        description="Additional status or error message",
        examples=["Discovered 42 entities across 5 areas"],
    )


class CachedEntity(BaseModel):
    """A single cached entity with metadata.

    Represents a Home Assistant entity (light, sensor, switch, etc.) with its
    current state and associated metadata like device and area information.
    """

    entity_id: str = Field(
        ...,
        description="Unique identifier for the entity (e.g., 'light.living_room')",
        examples=["light.living_room"],
    )
    domain: str = Field(
        ...,
        description="Entity domain type (e.g., 'light', 'sensor', 'switch', 'climate')",
        examples=["light"],
    )
    entity_type: str = Field(
        ...,
        description="Specific entity subtype within the domain",
        examples=["bulb"],
    )
    name: str = Field(
        ...,
        description="Human-readable name of the entity",
        examples=["Living Room Light"],
    )
    state: str = Field(
        ...,
        description="Current state value (e.g., 'on', 'off', '23.5')",
        examples=["on"],
    )
    unit_of_measurement: Optional[str] = Field(
        None,
        description="Unit of measurement for sensor entities (e.g., '°C', '%')",
        examples=["°C"],
    )
    device_id: Optional[str] = Field(
        None,
        description="Associated Home Assistant device ID",
        examples=["1234567890abcdef"],
    )
    area: Optional[str] = Field(
        None,
        description="Room or area where the entity is located",
        examples=["Living Room"],
    )
    last_changed: Optional[str] = Field(
        None,
        description="ISO 8601 timestamp of when the state was last changed",
        examples=["2024-05-06T10:30:00Z"],
    )


class EntityListResponse(BaseModel):
    """Response containing a list of cached entities.

    Wraps an array of CachedEntity objects with a total count for pagination support.
    """

    entities: List[CachedEntity] = Field(
        ...,
        description="Array of discovered and cached entity records",
    )
    count: int = Field(
        ...,
        description="Total number of entities in the response array",
        examples=[42],
    )


class SearchRequest(BaseModel):
    """Search request for entities.

    Used to search cached entities by name or entity_id using partial matching.
    """

    query: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Search term to match against entity names and IDs",
        examples=["Living Room"],
    )


class ServiceCallRequest(BaseModel):
    """Request to call a Home Assistant service.

    Specifies the service domain, service name, and optional data payload
    for invoking HA services like light.turn_on or media_player.play_media.
    """

    domain: str = Field(
        ...,
        description="Service domain (e.g., 'light', 'switch', 'media_player')",
        examples=["light"],
    )
    service: str = Field(
        ...,
        description="Service name within the domain (e.g., 'turn_on', 'turn_off', 'play_media')",
        examples=["turn_on"],
    )
    service_data: Optional[Dict[str, Any]] = Field(
        None,
        description=("Optional data payload for the service call. Structure depends on the specific service."),
        examples=[{"brightness": 200, "transition": 1}],
    )


class ServiceCallResponse(BaseModel):
    """Response from a service call.

    Returns the status of the service invocation and any result data returned by HA.
    """

    status: str = Field(
        ...,
        description="Service call status: 'success' or an error message",
        examples=["success"],
    )
    message: str = Field(
        ...,
        description="Human-readable description of the service call result",
        examples=["Service light/turn_on called successfully"],
    )
    result: Optional[Dict[str, Any]] = Field(
        None,
        description="Result data returned by the Home Assistant service (if any)",
    )


class DeviceInfo(BaseModel):
    """Information about a Home Assistant device.

    Contains identifying details and metadata for a physical or virtual device
    registered in Home Assistant.
    """

    id: str = Field(
        ...,
        description="Unique device identifier",
        examples=["01HZ5ABCDEF1234567890"],
    )
    name: str = Field(
        ...,
        description="Human-readable device name",
        examples=["Living Room Thermostat"],
    )
    area_id: Optional[str] = Field(
        None,
        description="ID of the area/room where this device is located",
        examples=["living_room"],
    )
    manufacturer: Optional[str] = Field(
        None,
        description="Device manufacturer name",
        examples=["Ecobee"],
    )
    model: Optional[str] = Field(
        None,
        description="Device model identifier",
        examples=["ecobee5"],
    )


class AreaInfo(BaseModel):
    """Information about a Home Assistant area/room.

    Contains details about a named area (room) in your Home Assistant setup.
    Areas are used to organize devices and entities into logical groups.
    """

    id: str = Field(
        ...,
        description="Unique area identifier",
        examples=["living_room"],
    )
    name: str = Field(
        ...,
        description="Human-readable area/room name",
        examples=["Living Room"],
    )
    picture: Optional[str] = Field(
        None,
        description="URL to a custom picture for the area (e.g., floor plan)",
        examples=["https://example.com/floorplan.png"],
    )


# ------------------------------------------------------------------
# Dashboard & Widget Schemas (Phase 4)
# ------------------------------------------------------------------


class DashboardCreateRequest(BaseModel):
    """Request to create a new dashboard.

    Provides the name and optional description for a new dashboard page.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name of the dashboard (e.g., 'Living Room', 'Kitchen')",
        examples=["Living Room"],
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional description for this dashboard",
        examples=["Main living area controls"],
    )


class DashboardUpdateRequest(BaseModel):
    """Request to update an existing dashboard.

    Provides the name and optional description fields that can be updated.
    Only provided fields will be changed; omitted fields remain unchanged.
    """

    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="New name for the dashboard",
        examples=["Updated Living Room"],
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional updated description for this dashboard",
        examples=["Main living area controls - updated"],
    )


class DashboardResponse(BaseModel):
    """Response containing a single dashboard.

    Returns the dashboard ID, name, description, and creation metadata.
    """

    id: int = Field(..., description="Unique dashboard identifier")
    name: str = Field(..., description="Name of the dashboard")
    description: Optional[str] = Field(None, description="Optional description")


class DashboardListResponse(BaseModel):
    """Response containing a list of dashboards.

    Wraps an array of DashboardResponse objects with a total count.
    """

    dashboards: List[DashboardResponse] = Field(
        ...,
        description="Array of dashboard records",
    )
    count: int = Field(..., description="Total number of dashboards")


class WidgetCreateRequest(BaseModel):
    """Request to create a new widget on a dashboard.

    Specifies the widget type, associated entity, position, and configuration.
    The page_id is derived from the URL path (not sent in body).
    """

    card_type: str = Field(
        ...,
        description="Widget type (e.g., 'switch', 'light')",
        examples=["switch"],
    )
    entity_id: Optional[str] = Field(
        None,
        description="Home Assistant entity ID this widget controls",
        examples=["switch.living_room_light"],
    )
    title: Optional[str] = Field(
        None,
        max_length=100,
        description="Display label for the widget",
        examples=["Living Room Light"],
    )
    config: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Widget-specific configuration as JSON",
        examples=[{"color": "blue"}],
    )
    x: int = Field(default=0, ge=0, le=12, description="X position on grid (0-12)")
    y: int = Field(default=0, ge=0, le=50, description="Y position on grid")
    width: int = Field(default=2, ge=1, le=12, description="Widget width in grid units")
    height: int = Field(default=1, ge=1, le=10, description="Widget height in grid units")


class WidgetResponse(BaseModel):
    """Response containing a single widget.

    Returns the widget ID, type, entity association, position, and configuration.
    """

    id: int = Field(..., description="Unique widget identifier")
    page_id: int = Field(..., description="Dashboard (page) ID this widget belongs to")
    card_type: str = Field(..., description="Widget type")
    entity_id: Optional[str] = Field(None, description="Associated HA entity ID")
    title: Optional[str] = Field(None, description="Display label")
    config: Dict[str, Any] = Field(default_factory=dict, description="Widget configuration JSON")
    x: int = Field(..., description="X position on grid")
    y: int = Field(..., description="Y position on grid")
    width: int = Field(..., description="Width in grid units")
    height: int = Field(..., description="Height in grid units")


class WidgetListResponse(BaseModel):
    """Response containing a list of widgets.

    Wraps an array of WidgetResponse objects with a total count.
    """

    widgets: List[WidgetResponse] = Field(
        ...,
        description="Array of widget records",
    )
    count: int = Field(..., description="Total number of widgets")


class FullDashboardResponse(BaseModel):
    """Complete dashboard response with all widgets and entity data.

    Returns the full dashboard definition including all associated widgets
    and their current entity states from Home Assistant.
    """

    id: int = Field(..., description="Unique dashboard identifier")
    name: str = Field(..., description="Name of the dashboard")
    description: Optional[str] = Field(None, description="Optional description")
    cards: List[WidgetResponse] = Field(
        default_factory=list,
        description="All widgets on this dashboard",
    )
