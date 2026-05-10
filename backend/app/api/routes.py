"""API routes for Home Assistant connection and entity discovery."""

import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.api.schemas import (
    HAConnectionRequest,
    HAConnectionResponse,
    EntityDiscoveryResponse,
    EntityListResponse,
    CachedEntity,
    SearchRequest,
    ServiceCallRequest,
    ServiceCallResponse,
    EntitySummary,
)
from app.services.ha_client import HAAPI, HAConnectionError, HAAPIError
from app.services.entity_discovery import EntityDiscoveryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ha", tags=["Home Assistant"])

_ha_client: Optional[HAAPI] = None
_entity_service: Optional[EntityDiscoveryService] = None


def get_ha_client() -> HAAPI:
    """Dependency to get the current HA client."""
    if _ha_client is None:
        raise HTTPException(status_code=400, detail="No HA connection configured")
    return _ha_client


def get_entity_service() -> EntityDiscoveryService:
    """Dependency to get the current entity discovery service."""
    if _entity_service is None:
        raise HTTPException(
            status_code=400,
            detail="Entity discovery not initialized. Connect to HA first.",
        )
    return _entity_service


def set_ha_connection(host: str, port: int, token: str, ssl: bool = True):
    """Set the global HA client and entity service."""
    global _ha_client, _entity_service

    _ha_client = HAAPI(
        host=host, port=port, token=token, ssl=ssl
    )
    _entity_service = EntityDiscoveryService(ha_client=_ha_client)


def sync_from_main(ha_client, entity_service):
    """Sync routes globals from main.py global services (loaded from DB at startup)."""
    global _ha_client, _entity_service
    if ha_client is not None:
        _ha_client = ha_client
    if entity_service is not None:
        _entity_service = entity_service


# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------


@router.post(
    "/connect",
    response_model=HAConnectionResponse,
    summary="Connect to Home Assistant",
    description=(
        "Establish a connection to a Home Assistant instance using the provided "
        "host, port, and access token. Validates credentials by testing the connection. "
        "Persists the connection settings to the database."
    ),
)
async def connect_to_ha(request: HAConnectionRequest, db=None):
    from app.database import SessionLocal, SettingsModel
    from app.database import encrypt_token

    try:
        set_ha_connection(host=request.host, port=request.port, token=request.token, ssl=request.ssl)

        client = get_ha_client()
        info = await asyncio.to_thread(client.test_connection)

        # Persist connection settings to DB
        db = db or SessionLocal()
        try:
            settings = db.query(SettingsModel).first()
            if settings is None:
                settings = SettingsModel()
                db.add(settings)
            settings.ha_host = request.host
            settings.ha_port = request.port
            settings.ha_ssl = request.ssl
            if request.token:
                settings.ha_access_token_encrypted = encrypt_token(request.token)
            db.commit()
        finally:
            db.close()

        # Auto-discover entities after successful connection
        entity_service = get_entity_service()
        discovered_count = 0
        try:
            summary = await asyncio.to_thread(entity_service.discover)
            discovered_count = summary.get("total_entities", 0)
            logger.info(f"Auto-discovered {discovered_count} entities from HA")
        except Exception as disc_err:
            logger.warning(f"Auto-discovery failed (non-fatal): {disc_err}")

        return HAConnectionResponse(
            status="success",
            host=info["host"],
            port=info["port"],
            entities=discovered_count,
            message=(
                f"Connected and discovered {discovered_count} entities"
                if discovered_count > 0
                else "Connected successfully"
            ),
        )
    except HAConnectionError as exc:
        logger.error(f"HA connection failed: {exc}")
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"Unexpected error connecting to HA: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Connection error: {str(exc)}",
        )


@router.post(
    "/discover",
    response_model=EntityDiscoveryResponse,
    summary="Discover entities from Home Assistant",
    description=(
        "Scan and discover all entities (lights, sensors, switches, etc.) from the "
        "connected Home Assistant instance. Results are cached in SQLite for later use."
    ),
)
async def discover_entities():
    try:
        service = get_entity_service()
        summary = await asyncio.to_thread(service.discover)

        return EntityDiscoveryResponse(
            status="success",
            summary=EntitySummary(**summary),
        )
    except HAConnectionError as exc:
        logger.error(f"HA connection error during discovery: {exc}")
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"Unexpected error during entity discovery: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Discovery error: {str(exc)}",
        )


@router.get(
    "/entities",
    response_model=EntityListResponse,
    summary="Get cached entities",
    description=(
        "Retrieve all cached entities from the connected Home Assistant instance. "
        "Entities are discovered via the /discover endpoint and stored in SQLite."
    ),
)
async def get_cached_entities():
    try:
        service = get_entity_service()
        entities = await asyncio.to_thread(service.get_cached_entities)

        return EntityListResponse(
            entities=[CachedEntity(**e) for e in entities],
            count=len(entities),
        )
    except HTTPException:
        raise
    except HAAPIError as exc:
        logger.error(f"HAAPI error fetching entities: {exc}")
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"Error fetching cached entities: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Fetch error: {str(exc)}",
        )


@router.get(
    "/entities/{entity_id}",
    response_model=CachedEntity,
    summary="Get a specific entity",
    description=(
        "Retrieve the current state and metadata for a single entity by its entity_id. "
        "Returns real-time state from the connected Home Assistant instance."
    ),
)
async def get_entity(entity_id: str):
    try:
        client = get_ha_client()
        state = await asyncio.to_thread(client.get_state, entity_id)

        if not state:
            raise HTTPException(
                status_code=404, detail=f"Entity '{entity_id}' not found"
            )

        attributes = state.get("attributes", {})
        return CachedEntity(
            entity_id=state["entity_id"],
            domain=state.get("domain", ""),
            entity_type=state.get("entity_type", ""),
            name=state.get("name", state["entity_id"]),
            state=str(state.get("state", "")),
            unit_of_measurement=attributes.get("unit_of_measurement"),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error fetching entity {entity_id}: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Fetch error: {str(exc)}",
        )


@router.post(
    "/search",
    response_model=EntityListResponse,
    summary="Search entities",
    description=(
        "Search cached entities by name or entity_id. Supports partial matching "
        "and returns all entities whose name or ID contains the query string."
    ),
)
async def search_entities(request: SearchRequest):
    try:
        service = get_entity_service()
        results = await asyncio.to_thread(service.search_entities, request.query)

        return EntityListResponse(
            entities=[CachedEntity(**e) for e in results],
            count=len(results),
        )
    except Exception as exc:
        logger.error(f"Error searching entities: {exc}")
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(
            status_code=500,
            detail=f"Search error: {str(exc)}",
        )


@router.post(
    "/services/call",
    response_model=ServiceCallResponse,
    summary="Call a Home Assistant service",
    description=(
        "Invoke a Home Assistant service (e.g., light.turn_on, media_player.play_media). "
        "Requires an active HA connection. Service data can include optional parameters."
    ),
)
async def call_ha_service(request: ServiceCallRequest):
    try:
        client = get_ha_client()
        result = await asyncio.to_thread(
            client.call_service,
            domain=request.domain,
            service=request.service,
            service_data=request.service_data,
        )

        return ServiceCallResponse(
            status="success",
            message=f"Service {request.domain}/{request.service} called successfully",
            result=result,
        )
    except HTTPException:
        raise
    except HAAPIError as exc:
        logger.error(f"HAAPI error calling service: {exc}")
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"Error calling HA service: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Service call error: {str(exc)}",
        )


@router.get(
    "/status",
    summary="Get connection status",
    description=(
        "Check whether a Home Assistant instance is currently connected and retrieve "
        "basic connection info (host, port, entity count)."
    ),
)
async def get_ha_status():
    if _ha_client is None:
        return {"connected": False}

    try:
        info = await asyncio.to_thread(_ha_client.test_connection)
        return {
            "connected": True,
            "host": info["host"],
            "port": info["port"],
            "entities": info.get("entities"),
        }
    except Exception as exc:
        logger.error(f"Status check failed: {exc}")
        return {"connected": False, "error": str(exc)}
