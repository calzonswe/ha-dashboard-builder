"""Tests for Entity Discovery and Caching with SQLite."""

import pytest
from unittest.mock import MagicMock
from app.services.entity_discovery import (
    EntityCache,
    EntityDiscoveryService,
)


class TestEntityCache:
    """Test suite for the EntityCache class with SQLite persistence."""

    @pytest.fixture
    def cache(self):
        """Create a fresh EntityCache instance."""
        return EntityCache(db_path=":memory:")

    def test_init_creates_tables(self, cache):
        """Test that tables are created on init."""
        entities = cache.get_all_entities()
        assert isinstance(entities, list)

    def test_refresh_populates_cache(self, cache):
        """Test that refresh populates the cache with entities."""
        states = [
            {
                "entity_id": "sensor.temperature",
                "state": "22.5",
                "attributes": {"friendly_name": "Living Room Temp"},
                "device_id": "dev_001",
            },
            {
                "entity_id": "light.lamp",
                "state": "on",
                "attributes": {"friendly_name": "Bedroom Lamp"},
                "device_id": "dev_002",
            },
        ]

        count = cache.refresh(states)
        assert count == 2

        # Verify data is in SQLite
        entities = cache.get_all_entities()
        assert len(entities) == 2
        entity_ids = [e["entity_id"] for e in entities]
        assert "light.lamp" in entity_ids
        assert "sensor.temperature" in entity_ids

    def test_get_by_entity_type(self, cache):
        """Test filtering entities by entity type (the part after the dot)."""
        states = [
            {"entity_id": "sensor.temp", "state": "20.0", "attributes": {}},
            {"entity_id": "binary_sensor.motion", "state": "off", "attributes": {}},
            {"entity_id": "light.lamp", "state": "on", "attributes": {}},
        ]

        cache.refresh(states)

        # Check entity types are correctly parsed (temp, motion, lamp)
        all_entities = cache.get_all_entities()
        entity_types = [e["entity_type"] for e in all_entities]
        assert "temp" in entity_types
        assert "motion" in entity_types
        assert "lamp" in entity_types

        # Also verify domain extraction works correctly
        domains = [e["domain"] for e in all_entities]
        assert "sensor" in domains
        assert "binary_sensor" in domains
        assert "light" in domains

    def test_get_by_domain(self, cache):
        """Test filtering entities by domain."""
        states = [
            {"entity_id": "sensor.temp", "state": "20.0", "attributes": {}},
            {"entity_id": "light.lamp", "state": "on", "attributes": {}},
            {"entity_id": "binary_sensor.motion", "state": "off", "attributes": {}},
        ]

        cache.refresh(states)

        # Get by domain (sensor, light, binary_sensor)
        sensors = cache.get_by_domain("sensor")
        assert len(sensors) == 1

        lights = cache.get_by_domain("light")
        assert len(lights) == 1

        binary_sensors = cache.get_by_domain("binary_sensor")
        assert len(binary_sensors) == 1

    def test_search(self, cache):
        """Test searching entities by name or ID."""
        states = [
            {
                "entity_id": "sensor.living_room_temp",
                "state": "20.0",
                "attributes": {"friendly_name": "Living Room Temp"},
            },
            {
                "entity_id": "sensor.bedroom_temp",
                "state": "18.5",
                "attributes": {"friendly_name": "Bedroom Temp"},
            },
        ]

        cache.refresh(states)

        results = cache.search("living")
        assert len(results) == 1
        assert results[0]["entity_id"] == "sensor.living_room_temp"

    def test_state_change_tracking(self, cache):
        """Test that state changes are tracked in history."""
        states1 = [
            {"entity_id": "sensor.temp", "state": "20.0", "attributes": {}},
        ]

        cache.refresh(states1)

        # Now update with different state
        states2 = [
            {"entity_id": "sensor.temp", "state": "25.0", "attributes": {}},
        ]

        cache.refresh(states2)

        # Check history
        history = cache.get_state_history("sensor.temp")
        assert len(history) == 1
        assert history[0]["old_state"] == "20.0"
        assert history[0]["new_state"] == "25.0"

    def test_get_state_changes_count(self, cache):
        """Test counting state changes."""
        states = [
            {"entity_id": "sensor.temp", "state": "20.0", "attributes": {}},
        ]

        cache.refresh(states)
        assert cache.get_state_changes_count() == 0

        # Update with different state to create a change
        states[0]["state"] = "25.0"
        cache.refresh(states)

        assert cache.get_state_changes_count() == 1

    def test_clear(self, cache):
        """Test clearing the cache."""
        states = [
            {"entity_id": "sensor.temp", "state": "20.0", "attributes": {}},
        ]

        cache.refresh(states)
        assert len(cache.get_all_entities()) == 1

        cache.clear()
        assert len(cache.get_all_entities()) == 0
        assert cache.get_state_changes_count() == 0


class TestEntityDiscoveryService:
    """Test suite for the EntityDiscoveryService class."""

    @pytest.fixture
    def mock_ha_client(self):
        """Create a mocked HA client."""
        client = MagicMock()
        client.test_connection.return_value = {
            "host": "192.168.1.50",
            "port": 8123,
            "entities": 42,
        }
        # States now include device_id for enrichment tests
        client.get_states.return_value = [
            {
                "entity_id": "sensor.temp",
                "state": "20.0",
                "attributes": {},
                "device_id": "dev_001",
            },
            {
                "entity_id": "light.lamp",
                "state": "on",
                "attributes": {},
                "device_id": "dev_002",
            },
        ]
        client.get_devices.return_value = []
        return client

    @pytest.fixture
    def discovery_service(self, mock_ha_client):
        """Create an EntityDiscoveryService with mocked HA client and isolated in-memory cache."""
        from app.services.entity_discovery import EntityCache

        # Use :memory: SQLite so each test gets a fresh, isolated database
        cache = EntityCache(db_path=":memory:")
        return EntityDiscoveryService(ha_client=mock_ha_client, entity_cache=cache)

    def test_discover(self, discovery_service):
        """Test full entity discovery cycle."""
        summary = discovery_service.discover()

        assert summary["status"] == "success"
        assert summary["total_entities"] == 2
        assert "sensor" in summary["domains"]
        assert "light" in summary["domains"]

    def test_get_cached_entities(self, discovery_service):
        """Test retrieving cached entities after discovery."""
        discovery_service.discover()
        entities = discovery_service.get_cached_entities()

        assert len(entities) == 2
        entity_ids = [e["entity_id"] for e in entities]
        assert "light.lamp" in entity_ids
        assert "sensor.temp" in entity_ids

    def test_search_entities(self, discovery_service):
        """Test searching cached entities."""
        discovery_service.discover()
        results = discovery_service.search_entities("light")

        assert len(results) == 1
        assert results[0]["entity_id"] == "light.lamp"

    def test_discover_with_device_enrichment(self, mock_ha_client):
        """Test discovery with device metadata enrichment."""
        # Add devices that map to areas
        mock_ha_client.get_devices.return_value = [
            {"id": "dev_001", "area_id": "living_room"},
            {"id": "dev_002", "area_id": "bedroom"},
        ]

        service = EntityDiscoveryService(
            ha_client=mock_ha_client, entity_cache=EntityCache(db_path=":memory:")
        )
        service.discover()

        entities = service.get_cached_entities()
        assert len(entities) == 2

        # Check that devices got enriched with area metadata
        sensor = next(e for e in entities if e["entity_id"] == "sensor.temp")
        assert sensor["area"] == "living_room"

        lamp = next(e for e in entities if e["entity_id"] == "light.lamp")
        assert lamp["area"] == "bedroom"

    def test_discover_handles_device_fetch_failure(self, mock_ha_client):
        """Test discovery continues even if device fetch fails."""

        # Create a custom exception that will be raised
        class DeviceFetchError(Exception):
            pass

        mock_ha_client.get_devices.side_effect = DeviceFetchError("Device fetch failed")

        service = EntityDiscoveryService(
            ha_client=mock_ha_client, entity_cache=EntityCache(db_path=":memory:")
        )
        summary = service.discover()

        # Status should still be "success" because device enrichment is optional
        assert summary["status"] == "success"

        # But entities should still be cached (without device metadata)
        entities = service.get_cached_entities()
        assert len(entities) == 2

        # Verify no errors in the summary (device fetch failure is handled gracefully)
        assert len(summary["errors"]) == 0
