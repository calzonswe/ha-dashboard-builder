"""Entity metadata enrichment with device/area info."""

import logging
from typing import Any, Dict, List, Optional

from app.ha_client import HAClient
from app.models import Entity

logger = logging.getLogger(__name__)


class MetadataEnricher:
    """Enrich entities with device info and area names from HA registries."""

    def __init__(self, client: HAClient) -> None:
        self.client = client
        self._registry_cache: Optional[Dict[str, Any]] = None
        self._device_cache: Optional[Dict[str, Dict[str, Any]]] = None
        self._area_cache: Optional[Dict[str, str]] = None

    async def fetch_registries(self) -> Dict[str, Any]:
        """Fetch all registries from HA (entity, device, area)."""
        if self._registry_cache is not None:
            return self._registry_cache

        entities_data: List[Dict] = []
        devices_data: List[Dict] = []
        areas_data: List[Dict] = []

        # Fetch entity registry
        try:
            entities_data = await self.client._request("GET", "config/entity_registry")  # noqa: SLF001
        except Exception as e:
            logger.warning(f"Failed to fetch entity registry: {e}")

        # Fetch device registry
        try:
            devices_data = await self.client._request("GET", "config/device_registry")  # noqa: SLF001
        except Exception as e:
            logger.warning(f"Failed to fetch device registry: {e}")

        # Fetch area registry
        try:
            areas_data = await self.client._request("GET", "config/area_registry")  # noqa: SLF001
        except Exception as e:
            logger.warning(f"Failed to fetch area registry: {e}")

        self._registry_cache = {"entities": entities_data, "devices": devices_data, "areas": areas_data}
        self._build_caches(entities_data, devices_data, areas_data)

        return self._registry_cache

    def _build_caches(
        self,
        entities: List[Dict],
        devices: List[Dict],
        areas: List[Dict],
    ) -> None:
        """Build lookup caches from registry data."""
        # Device ID -> device info map
        self._device_cache = {}
        for device in devices:
            if isinstance(device, dict) and "id" in device:
                self._device_cache[device["id"]] = device

        # Area ID -> area name map
        self._area_cache = {}
        for area in areas:
            if isinstance(area, dict) and "area_id" in area or "id" in area:
                area_id = area.get("area_id", area.get("id"))
                name = area.get("name", "Unknown")
                self._area_cache[area_id] = name

        # Entity ID -> device/area mapping
        self._entity_mapping: Dict[str, Dict[str, Any]] = {}
        for entity in entities:
            if isinstance(entity, dict) and "entity_id" in entity:
                entity_id = entity["entity_id"]
                mapping: Dict[str, Any] = {}

                device_id = entity.get("device_id") or entity.get("device_id_in_registry")
                if device_id:
                    mapping["device_id"] = device_id
                    device_info = self._device_cache.get(device_id)
                    if device_info:
                        mapping["device_name"] = device_info.get("name_by_user", device_info.get("name", "Unknown"))
                        area_id = device_info.get("area_id")
                        if area_id and area_id in self._area_cache:
                            mapping["area_name"] = self._area_cache[area_id]

                entity_area_id = entity.get("area_id")
                if entity_area_id and entity_area_id not in (mapping.get("area_name"), ""):
                    if entity_area_id in self._area_cache:
                        mapping.setdefault("area_name", self._area_cache[entity_area_id])

                self._entity_mapping[entity_id] = mapping

    def enrich_entity(self, entity: Entity) -> Entity:
        """Enrich a single entity with device and area metadata."""
        if self._entity_mapping is None or entity.entity_id not in self._entity_mapping:
            return entity

        mapping = self._entity_mapping[entity.entity_id]

        # Set device info
        if "device_id" in mapping:
            entity.device_info = {
                "device_id": mapping["device_id"],
                "device_name": mapping.get("device_name"),
            }

        # Set area name
        if "area_name" in mapping and not entity.area_name:
            entity.area_name = mapping["area_name"]

        return entity

    def enrich_entities(self, entities: List[Entity]) -> List[Entity]:
        """Enrich a list of entities with metadata."""
        enriched = []
        for entity in entities:
            enriched.append(self.enrich_entity(entity))
        return enriched

    async def get_device_entities(self, device_id: str) -> List[str]:
        """Get all entity IDs belonging to a device."""
        await self.fetch_registries()

        if self._entity_mapping is None:
            return []

        result = [eid for eid, mapping in self._entity_mapping.items() if mapping.get("device_id") == device_id]
        return result

    async def get_area_entities(self, area_name: str) -> List[str]:
        """Get all entity IDs belonging to an area."""
        await self.fetch_registries()

        if self._entity_mapping is None:
            return []

        result = [eid for eid, mapping in self._entity_mapping.items() if mapping.get("area_name") == area_name]
        return result

    async def get_all_areas(self) -> List[Dict[str, Any]]:
        """Get all areas with their entity counts."""
        await self.fetch_registries()

        areas: Dict[str, int] = {}
        if self._entity_mapping:
            for mapping in self._entity_mapping.values():
                area = mapping.get("area_name", "Unassigned") or "Unassigned"
                areas[area] = areas.get(area, 0) + 1

        return [{"name": name, "entity_count": count} for name, count in sorted(areas.items())]

    async def get_all_devices(self) -> List[Dict[str, Any]]:
        """Get all devices with their entity counts."""
        await self.fetch_registries()

        if self._device_cache is None or self._entity_mapping is None:
            return []

        device_counts: Dict[str, int] = {}
        for mapping in self._entity_mapping.values():
            device_id = mapping.get("device_id")
            if device_id:
                device_counts[device_id] = device_counts.get(device_id, 0) + 1

        result = []
        for device_id, count in device_counts.items():
            device_info = self._device_cache.get(device_id, {})
            result.append({
                "id": device_id,
                "name": device_info.get("name_by_user", device_info.get("name", "Unknown")),
                "entity_count": count,
            })

        return sorted(result, key=lambda d: d["name"])


# Convenience instance
enricher = MetadataEnricher(HAClient())
