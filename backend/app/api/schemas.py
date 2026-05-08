"""API schemas for Home Assistant connection and entity discovery."""

from typing import List, Optional, Dict, Any, Literal, Union
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
        description=(
            "Optional data payload for the service call. Structure depends on the specific service."
        ),
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
    height: int = Field(
        default=1, ge=1, le=10, description="Widget height in grid units"
    )


class WidgetResponse(BaseModel):
    """Response containing a single widget.

    Returns the widget ID, type, entity association, position, and configuration.
    """

    id: int = Field(..., description="Unique widget identifier")
    page_id: int = Field(..., description="Dashboard (page) ID this widget belongs to")
    card_type: str = Field(..., description="Widget type")
    entity_id: Optional[str] = Field(None, description="Associated HA entity ID")
    title: Optional[str] = Field(None, description="Display label")
    config: Dict[str, Any] = Field(
        default_factory=dict, description="Widget configuration JSON"
    )
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


class LiveEntityState(BaseModel):
    """Current state of a Home Assistant entity."""

    entity_id: str = Field(..., description="Home Assistant entity ID")
    state: str = Field(..., description="Current state value")
    attributes: Dict[str, Any] = Field(
        default_factory=dict, description="Entity attributes"
    )


class DashboardPreviewResponse(BaseModel):
    """Dashboard preview with live entity states.

    Returns the dashboard definition along with current entity states
    from Home Assistant for all widgets that reference entities.
    """

    id: int = Field(..., description="Unique dashboard identifier")
    name: str = Field(..., description="Name of the dashboard")
    description: Optional[str] = Field(None, description="Optional description")
    cards: List[WidgetResponse] = Field(
        default_factory=list,
        description="All widgets on this dashboard",
    )
    entity_states: Dict[str, LiveEntityState] = Field(
        default_factory=dict,
        description="Current live states for all referenced entities",
    )


class CardUpdateRequest(BaseModel):
    """Request to update a single widget (card) on a dashboard.

    All fields are optional — only provided fields will be updated.
    This enables partial updates (e.g., changing just x/y position).
    """

    card_type: Optional[str] = Field(
        default=None,
        description="Widget type (e.g., 'switch', 'light')",
        examples=["switch"],
    )
    entity_id: Optional[str] = Field(
        default=None,
        description="Home Assistant entity ID this widget controls",
        examples=["switch.living_room_light"],
    )
    title: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Display label for the widget",
        examples=["Living Room Light"],
    )
    config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Widget-specific configuration as JSON",
        examples=[{"color": "blue"}],
    )
    x: Optional[int] = Field(
        default=None, ge=0, le=12, description="X position on grid (0-12)"
    )
    y: Optional[int] = Field(
        default=None, ge=0, le=50, description="Y position on grid"
    )
    width: Optional[int] = Field(
        default=None, ge=1, le=12, description="Widget width in grid units"
    )
    height: Optional[int] = Field(
        default=None, ge=1, le=10, description="Widget height in grid units"
    )


class CardConfigRequest(BaseModel):
    """A card (widget) with its ID and configuration for bulk update.

    Used when replacing all cards on a dashboard at once. The `id` field
    is used to match existing widgets; new cards without an id will be created.
    """

    id: Optional[int] = Field(
        default=None,
        description="Existing widget ID (for updates); omit for new cards",
        examples=[1],
    )
    card_type: str = Field(
        ...,
        description="Widget type (e.g., 'switch', 'light')",
        examples=["switch"],
    )
    entity_id: Optional[str] = Field(
        default=None,
        description="Home Assistant entity ID this widget controls",
        examples=["switch.living_room_light"],
    )
    title: Optional[str] = Field(
        default=None,
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
    height: int = Field(
        default=1, ge=1, le=10, description="Widget height in grid units"
    )


class CardsBulkUpdateRequest(BaseModel):
    """Request to replace all cards on a dashboard.

    Accepts an array of card configurations that completely replaces the
    existing set of widgets for this dashboard. Used by the frontend
    saveCards() hook after drag-and-drop layout changes.
    """

    cards: List[CardConfigRequest] = Field(
        ...,
        description="Complete list of cards (widgets) for this dashboard",
        examples=[
            [
                {
                    "id": 1,
                    "card_type": "switch",
                    "entity_id": "switch.light_1",
                    "x": 0,
                    "y": 0,
                    "width": 2,
                    "height": 1,
                },
                {
                    "card_type": "sensor",
                    "entity_id": "sensor.temp_1",
                    "x": 2,
                    "y": 0,
                    "width": 3,
                    "height": 1,
                },
            ]
        ],
    )


class CardsBulkUpdateResponse(BaseModel):
    """Response confirming bulk card update.

    Returns the updated list of widgets with their server-assigned IDs.
    """

    cards: List[WidgetResponse] = Field(
        ...,
        description="Updated widget records with server-assigned IDs",
    )


# ------------------------------------------------------------------
# Lovelace Card Type Schemas (Phase 5)
# ------------------------------------------------------------------

# Supported Lovelace card types
LOVELACE_CARD_TYPES = [
    "entities",
    "entity",
    "glance",
    "grid",
    "horizontal-stack",
    "vertical-stack",
    "picture-entity",
    "picture",
    "cover",
    "thermostat",
    "climate",
    "weather",
    "scene",
    "script",
    "button",
    "input-button",
    "light",
    "switch",
    "automation",
    "logbook",
    "history",
    "statistics",
    "gauge",
    "markdown",
    "iframe",
    "webpage",
    "camera",
    "plant",
    "todo",
]


class LovelaceEntitiesCard(BaseModel):
    """Entities card - shows a list of entity buttons."""

    type: Literal["entities"] = "entities"
    title: Optional[str] = None
    show_header_toggle: bool = True
    entities: List[Union[str, Dict[str, Any]]] = Field(
        default_factory=list, description="List of entity IDs or entity objects"
    )


class LovelaceGlanceCard(BaseModel):
    """Glance card - shows a group of entities in a compact grid."""

    type: Literal["glance"] = "glance"
    title: Optional[str] = None
    columns: Optional[int] = Field(None, ge=1, le=6)
    entities: List[Union[str, Dict[str, Any]]] = Field(
        ..., description="List of entity IDs or entity objects"
    )
    show_name: bool = True
    show_icon: bool = True
    state_color: bool = False


class LovelaceEntityCard(BaseModel):
    """Entity card - displays a single entity."""

    type: Literal["entity"] = "entity"
    entity: str = Field(..., description="Entity ID to display")
    name: Optional[str] = None
    icon: Optional[str] = None
    attribute: Optional[str] = None
    unit: Optional[str] = None
    secondary_info: Optional[str] = None
    state_color: bool = True


class LovelacePictureEntityCard(BaseModel):
    """Picture Entity card - shows entity state on a background image."""

    type: Literal["picture-entity"] = "picture-entity"
    entity: str = Field(..., description="Entity ID to display")
    image: Optional[str] = None
    aspect_ratio: Optional[str] = None
    show_name: bool = True
    show_state: bool = True
    theme: Optional[str] = None


class LovelaceThermostatCard(BaseModel):
    """Thermostat card - shows a climate entity with controls."""

    type: Literal["thermostat"] = "thermostat"
    entity: str = Field(..., description="Climate entity ID")
    title: Optional[str] = None
    theme: Optional[str] = None
    show_current_temperature: bool = True


class LovelaceGaugeCard(BaseModel):
    """Gauge card - shows a sensor value as a gauge."""

    type: Literal["gauge"] = "gauge"
    entity: str = Field(..., description="Sensor entity ID")
    title: Optional[str] = None
    min: float = 0
    max: float = 100
    unit: Optional[str] = None
    theme: Optional[str] = None
    severity: Optional[Dict[str, Any]] = None


class LovelaceGridCard(BaseModel):
    """Grid card - shows multiple cards in a grid layout."""

    type: Literal["grid"] = "grid"
    title: Optional[str] = None
    columns: Optional[int] = Field(None, ge=1, le=6)
    cards: List[Dict[str, Any]] = Field(
        default_factory=list, description="Nested card configurations"
    )


class LovelaceVerticalStackCard(BaseModel):
    """Vertical Stack card - stacks cards vertically."""

    type: Literal["vertical-stack"] = "vertical-stack"
    title: Optional[str] = None
    cards: List[Dict[str, Any]] = Field(
        default_factory=list, description="Nested card configurations"
    )


class LovelaceHorizontalStackCard(BaseModel):
    """Horizontal Stack card - stacks cards horizontally."""

    type: Literal["horizontal-stack"] = "horizontal-stack"
    title: Optional[str] = None
    cards: List[Dict[str, Any]] = Field(
        default_factory=list, description="Nested card configurations"
    )


class LovelaceButtonCard(BaseModel):
    """Button card - shows a clickable button."""

    type: Literal["button"] = "button"
    entity: Optional[str] = None
    name: Optional[str] = None
    icon: Optional[str] = None
    show_icon: bool = True
    show_name: bool = True
    hold_action: Optional[Dict[str, Any]] = None
    tap_action: Optional[Dict[str, Any]] = None


class LovelaceMarkdownCard(BaseModel):
    """Markdown card - displays Markdown content."""

    type: Literal["markdown"] = "markdown"
    content: str = Field(..., description="Markdown content")
    title: Optional[str] = None
    card_mod: Optional[Dict[str, Any]] = None


class LovelaceCameraCard(BaseModel):
    """Camera card - displays a camera feed or thumbnail."""

    type: Literal["camera"] = "camera"
    entity: str = Field(..., description="Camera entity ID")
    title: Optional[str] = None
    aspect_ratio: Optional[str] = None
    show_controls: bool = False
    show_timestamp: bool = False


class LovelaceHistoryCard(BaseModel):
    """History card - shows entity state history."""

    type: Literal["history"] = "history"
    title: Optional[str] = None
    entities: List[str] = Field(..., description="List of entity IDs")
    days_to_show: int = Field(default=7, ge=1, le=365)
    refresh_interval: Optional[int] = None


class LovelaceLogbookCard(BaseModel):
    """Logbook card - shows logbook entries."""

    type: Literal["logbook"] = "logbook"
    title: Optional[str] = None
    entities: List[str] = Field(default_factory=list, description="List of entity IDs")
    hours_to_show: int = Field(default=24, ge=1, le=168)


class LovelaceCardValidator:
    """Validator for Lovelace card configurations.

    Validates card type and required fields based on Lovelace card schema.
    """

    @staticmethod
    def validate_card_type(card_type: str) -> bool:
        """Check if card type is a valid Lovelace card type."""
        return card_type in LOVELACE_CARD_TYPES

    @staticmethod
    def validate_entity(entity_id: str) -> bool:
        """Validate entity ID format (domain.name)."""
        if not entity_id or "." not in entity_id:
            return False
        parts = entity_id.split(".")
        return len(parts) == 2 and parts[0] and parts[1]

    @staticmethod
    def validate_card(card_config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate a card configuration.

        Returns (is_valid, error_message).
        """
        card_type = card_config.get("type")
        if not card_type:
            return False, "Card type is required"

        if not LovelaceCardValidator.validate_card_type(card_type):
            return False, f"Unknown card type: {card_type}"

        # Validate entity cards have entity field
        entity_cards = ["entity", "picture-entity", "thermostat", "gauge", "button", "camera"]
        if card_type in entity_cards:
            entity = card_config.get("entity")
            if not entity:
                return False, f"Card type '{card_type}' requires 'entity' field"
            if not LovelaceCardValidator.validate_entity(entity):
                return False, f"Invalid entity ID: {entity}"

        # Validate stack cards have cards array
        stack_cards = ["grid", "vertical-stack", "horizontal-stack"]
        if card_type in stack_cards:
            cards = card_config.get("cards", [])
            if not isinstance(cards, list):
                return False, f"Card type '{card_type}' requires 'cards' array"

        return True, None


# Pydantic model for validating any Lovelace card
LovelaceCardConfig = Union[
    LovelaceEntitiesCard,
    LovelaceGlanceCard,
    LovelaceEntityCard,
    LovelacePictureEntityCard,
    LovelaceThermostatCard,
    LovelaceGaugeCard,
    LovelaceGridCard,
    LovelaceVerticalStackCard,
    LovelaceHorizontalStackCard,
    LovelaceButtonCard,
    LovelaceMarkdownCard,
    LovelaceCameraCard,
    LovelaceHistoryCard,
    LovelaceLogbookCard,
]
