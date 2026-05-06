"""Entity discovery with filtering and graceful partial failure handling."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from app.ha_client import HAClient, HAConnectionError
from app.models import Entity, EntityType

logger = logging.getLogger(__name__)


class PartialDiscoveryError(Exception):
    """Raised when discovery partially succeeds but some entities failed."""

    def __init__(self, successful: int, failed: int, errors: List[str]) -> None:
        self.successful = successful
        self.failed = failed
        self.errors = errors
        super().__init__(f"Partial success: {successful} entities discovered, {failed} failed")


class EntityDiscovery:
    """Discover and filter Home Assistant entities with graceful error handling."""

    def __init__(self, client: HAClient) -> None:
        self.client = client

    async def discover_all(self) -> Dict[str, Any]:
        """Discover all entities from HA with detailed partial failure reporting."""
        errors: List[str] = []
        warnings: List[str] = []
        entity_errors: List[Dict[str, Any]] = []  # Detailed per-entity errors
        entities: List[Entity] = []

        # Fetch states
        states_data: List[Dict[str, Any]] = []
        try:
            states_data = await self.client.get_states()
        except Exception as e:
            logger.error(f"Failed to fetch entity states: {e}")
            errors.append(f"Failed to fetch states: {e}")
            return {
                "total_entities": 0,
                "entities": [],
                "errors": errors,
                "warnings": warnings,
                "entity_errors": entity_errors,
                "discovered_at": datetime.now(),
            }

        # Fetch registries (may fail gracefully)
        registry: List[Dict[str, Any]] = []
        try:
            registry = await self.client._request("GET", "config/entity_registry")  # noqa: SLF001
        except Exception as e:
            warnings.append(f"Could not fetch entity registry: {e}")

        device_registry: List[Dict[str, Any]] = []
        try:
            device_registry = await self.client._request("GET", "config/device_registry")  # noqa: SLF001
        except Exception as e:
            warnings.append(f"Could not fetch device registry: {e}")

        area_registry: List[Dict[str, Any]] = []
        try:
            area_registry = await self.client._request("GET", "config/area_registry")  # noqa: SLF001
        except Exception as e:
            warnings.append(f"Could not fetch area registry: {e}")

        # Build registries lookup maps
        device_map: Dict[str, Dict[str, Any]] = {}
        for d in device_registry:
            if isinstance(d, dict) and "id" in d:
                device_map[d["id"]] = d

        area_map: Dict[str, str] = {}
        for a in area_registry:
            if isinstance(a, dict):
                aid = a.get("area_id", a.get("id"))
                name = a.get("name", "Unknown")
                if aid:
                    area_map[aid] = name

        entity_reg_map: Dict[str, Dict[str, Any]] = {}
        for e in registry:
            if isinstance(e, dict) and "entity_id" in e:
                entity_reg_map[e["entity_id"]] = e

        # Process each state item individually with error handling
        total_states = len(states_data)
        failed_count = 0

        for i, state_item in enumerate(states_data):
            try:
                entity = Entity.from_ha_state(state_item)

                # Enrich with registry data
                reg_entry = entity_reg_map.get(entity.entity_id, {})
                if reg_entry:
                    device_id = reg_entry.get("device_id") or reg_entry.get("device_id_in_registry")
                    area_id = reg_entry.get("area_id")

                    if device_id and device_id in device_map:
                        device_info = device_map[device_id]
                        entity.device_info = {
                            "device_id": device_id,
                            "device_name": device_info.get("name_by_user", device_info.get("name")),
                        }

                    # Resolve area name from device or direct area_id
                    if not entity.area_name:
                        if device_id and device_id in device_map:
                            dev_area_id = device_map[device_id].get("area_id")
                            if dev_area_id and dev_area_id in area_map:
                                entity.area_name = area_map[dev_area_id]
                        elif area_id and area_id in area_map:
                            entity.area_name = area_map[area_id]

                entities.append(entity)

            except Exception as e:
                failed_count += 1
                error_detail = {
                    "entity_id": state_item.get("entity_id", "unknown"),
                    "error": str(e),
                    "index": i,
                }
                entity_errors.append(error_detail)
                warnings.append(f"Could not parse state for {state_item.get('entity_id', 'unknown')}: {e}")

        # Check if we had significant failures
        if failed_count > 0:
            logger.warning(
                f"Partial discovery: {len(entities)}/{total_states} entities, "
                f"{failed_count} errors"
            )

        return {
            "total_entities": len(states_data),
            "entities": entities,
            "errors": errors,
            "warnings": warnings,
            "entity_errors": entity_errors,
            "discovered_at": datetime.now(),
        }

    def _get_area_from_registry(
        self, registry: List[Dict[str, Any]], device_id: str
    ) -> Optional[str]:
        """Extract area name from entity registry for a given device."""
        for entry in registry:
            if not isinstance(entry, dict):
                continue
            dev_info = entry.get("device_id") or entry.get("device_id_in_registry")
            if dev_info == device_id and "area_id" in entry:
                for area_entry in registry:
                    if isinstance(area_entry, dict) and area_entry.get("id") == entry["area_id"]:
                        return area_entry.get("name")
        return None

    def filter_entities(
        self,
        entities: List[Entity],
        domains: Optional[List[str]] = None,
        types: Optional[List[EntityType]] = None,
        areas: Optional[List[str]] = None,
        device_ids: Optional[List[str]] = None,
        search: Optional[str] = None,
    ) -> List[Entity]:
        """Filter entities by multiple criteria."""
        result = list(entities)

        if domains:
            domain_set: Set[str] = set(domains)
            result = [e for e in result if e.domain in domain_set]

        if types:
            type_set: Set[EntityType] = set(types)
            result = [e for e in result if e.entity_type in type_set]

        if areas:
            area_set: Set[str] = set(areas)
            result = [e for e in result if e.area_name and e.area_name in area_set]

        if device_ids:
            device_set: Set[str] = set(device_ids)
            result = [e for e in result if e.device_info and e.device_info.get("device_id") in device_set]

        if search:
            search_lower = search.lower()
            result = [
                e
                for e in result
                if (
                    search_lower in e.entity_id.lower()
                    or search_lower in str(e.state).lower()
                    or any(search_lower in k.lower() for k in e.attributes.keys())
                )
            ]

        return result

    async def get_filtered_entities(
        self,
        domains: Optional[List[str]] = None,
        types: Optional[List[EntityType]] = None,
        areas: Optional[List[str]] = None,
        device_ids: Optional[List[str]] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Discover and filter entities in one call."""
        discovery = await self.discover_all()

        if not discovery["entities"]:
            return {
                "total_entities": 0,
                "filtered_count": 0,
                "entities": [],
                "errors": discovery["errors"],
                "warnings": discovery["warnings"],
                "entity_errors": discovery.get("entity_errors", []),
                "discovered_at": discovery["discovered_at"],
            }

        filtered = self.filter_entities(
            discovery["entities"],
            domains=domains,
            types=types,
            areas=areas,
            device_ids=device_ids,
            search=search,
        )

        return {
            "total_entities": len(discovery["entities"]),
            "filtered_count": len(filtered),
            "entities": filtered,
            "errors": discovery["errors"],
            "warnings": discovery.get("warnings", []),
            "entity_errors": discovery.get("entity_errors", []),
            "discovered_at": discovery["discovered_at"],
        }

    def group_by_area(self, entities: List[Entity]) -> Dict[str, List[Entity]]:
        """Group entities by their area name."""
        groups: Dict[str, List[Entity]] = {}
        for entity in entities:
            area = entity.area_name or "Unassigned"
            if area not in groups:
                groups[area] = []
            groups[area].append(entity)
        return dict(sorted(groups.items()))

    def group_by_device(self, entities: List[Entity]) -> Dict[str, List[Entity]]:
        """Group entities by device ID."""
        groups: Dict[str, List[Entity]] = {}
        for entity in entities:
            if entity.device_info and entity.device_info.get("device_id"):
                key = f"Device {entity.device_info['device_id']}"
            else:
                key = "No Device"
            if key not in groups:
                groups[key] = []
            groups[key].append(entity)
        return dict(sorted(groups.items()))

    def get_summary(self, entities: List[Entity]) -> Dict[str, Any]:
        """Get a summary of entity counts by domain and area."""
        domains: Dict[str, int] = {}
        areas: Dict[str, int] = {}
        for e in entities:
            domains[e.domain] = domains.get(e.domain, 0) + 1
            area = e.area_name or "Unassigned"
            areas[area] = areas.get(area, 0) + 1

        return {
            "total": len(entities),
            "by_domain": dict(sorted(domains.items())),
            "by_area": dict(sorted(areas.items())),
        }


# Convenience instance
discovery = EntityDiscovery(HAClient())
