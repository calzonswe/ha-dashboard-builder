"""Unit tests for entity discovery module."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.entity_discovery import EntityDiscovery
from app.models import Entity, EntityType

NOW = datetime(2024, 1, 1, 0, 0, 0)


class TestEntityDiscovery:
    """Tests for the EntityDiscovery class."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock HAClient."""
        client = AsyncMock()
        return client

    @pytest.fixture
    def discovery(self, mock_client):
        """Create an EntityDiscovery instance with mocked client."""
        return EntityDiscovery(mock_client)

    @pytest.fixture
    def sample_states(self):
        """Sample HA state data."""
        return [
            {
                "entity_id": "light.living_room",
                "state": "on",
                "attributes": {"brightness": 200},
                "last_changed": "2024-01-01T00:00:00",
                "last_updated": "2024-01-01T00:00:00",
            },
            {
                "entity_id": "sensor.temperature",
                "state": "22.5",
                "attributes": {"unit_of_measurement": "°C"},
                "last_changed": "2024-01-01T00:00:00",
                "last_updated": "2024-01-01T00:00:00",
            },
        ]

    @pytest.mark.asyncio
    async def test_discover_all_success(self, discovery, mock_client, sample_states):
        """Test successful entity discovery."""
        mock_client.get_states = AsyncMock(return_value=sample_states)
        mock_client._request = AsyncMock(return_value=[])

        result = await discovery.discover_all()
        assert result["total_entities"] == 2
        assert len(result["entities"]) == 2
        assert result["errors"] == []
        assert result["warnings"] == []

    @pytest.mark.asyncio
    async def test_discover_all_states_failure(self, discovery, mock_client):
        """Test discovery when states fetch fails."""
        from app.ha_client import HAConnectionError
        mock_client.get_states = AsyncMock(side_effect=HAConnectionError("http://test", "Failed", 1))

        result = await discovery.discover_all()
        assert result["total_entities"] == 0
        assert len(result["entities"]) == 0
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_discover_all_partial_registry_failure(self, discovery, mock_client, sample_states):
        """Test discovery when registry fetch fails but states succeed."""
        from app.ha_client import HAConnectionError
        mock_client.get_states = AsyncMock(return_value=sample_states)
        mock_client._request = AsyncMock(side_effect=HAConnectionError("http://test", "Failed", 1))

        result = await discovery.discover_all()
        assert result["total_entities"] == 2
        assert len(result["entities"]) == 2
        assert any("Could not fetch" in w for w in result["warnings"])

    def test_filter_by_domains(self, discovery):
        """Test filtering entities by domain."""
        entities = [
            Entity(entity_id="light.test", state="on", attributes={}, last_changed=NOW, last_updated=NOW, domain="light", entity_type=EntityType.LIGHT),
            Entity(entity_id="sensor.temp", state="22", attributes={}, last_changed=NOW, last_updated=NOW, domain="sensor", entity_type=EntityType.SENSOR),
        ]

        result = discovery.filter_entities(entities, domains=["light"])
        assert len(result) == 1
        assert result[0].entity_id == "light.test"

    def test_filter_by_types(self, discovery):
        """Test filtering entities by type."""
        entities = [
            Entity(entity_id="light.test", state="on", attributes={}, last_changed=NOW, last_updated=NOW, domain="light", entity_type=EntityType.LIGHT),
            Entity(entity_id="switch.test", state="off", attributes={}, last_changed=NOW, last_updated=NOW, domain="switch", entity_type=EntityType.SWITCH),
        ]

        result = discovery.filter_entities(entities, types=[EntityType.LIGHT])
        assert len(result) == 1
        assert result[0].entity_type == EntityType.LIGHT

    def test_filter_by_areas(self, discovery):
        """Test filtering entities by area."""
        entities = [
            Entity(entity_id="light.kitchen", state="on", attributes={}, last_changed=NOW, last_updated=NOW, domain="light", entity_type=EntityType.LIGHT, area_name="Kitchen"),
            Entity(entity_id="light.bedroom", state="off", attributes={}, last_changed=NOW, last_updated=NOW, domain="light", entity_type=EntityType.LIGHT, area_name="Bedroom"),
        ]

        result = discovery.filter_entities(entities, areas=["Kitchen"])
        assert len(result) == 1
        assert result[0].entity_id == "light.kitchen"

    def test_filter_by_search(self, discovery):
        """Test filtering entities by search string."""
        entities = [
            Entity(entity_id="light.living_room", state="on", attributes={}, last_changed=NOW, last_updated=NOW, domain="light", entity_type=EntityType.LIGHT),
            Entity(entity_id="sensor.temperature", state="22", attributes={}, last_changed=NOW, last_updated=NOW, domain="sensor", entity_type=EntityType.SENSOR),
        ]

        result = discovery.filter_entities(entities, search="living")
        assert len(result) == 1
        assert result[0].entity_id == "light.living_room"

    def test_filter_combined(self, discovery):
        """Test combining multiple filters."""
        entities = [
            Entity(entity_id="light.kitchen", state="on", attributes={}, last_changed=NOW, last_updated=NOW, domain="light", entity_type=EntityType.LIGHT, area_name="Kitchen"),
            Entity(entity_id="switch.kitchen", state="off", attributes={}, last_changed=NOW, last_updated=NOW, domain="switch", entity_type=EntityType.SWITCH, area_name="Kitchen"),
        ]

        result = discovery.filter_entities(entities, domains=["light"], areas=["Kitchen"])
        assert len(result) == 1
        assert result[0].entity_id == "light.kitchen"

    def test_group_by_area(self, discovery):
        """Test grouping entities by area."""
        entities = [
            Entity(entity_id="light.kitchen", state="on", attributes={}, last_changed=NOW, last_updated=NOW, domain="light", entity_type=EntityType.LIGHT, area_name="Kitchen"),
            Entity(entity_id="light.bedroom", state="off", attributes={}, last_changed=NOW, last_updated=NOW, domain="light", entity_type=EntityType.LIGHT, area_name="Bedroom"),
        ]

        result = discovery.group_by_area(entities)
        assert "Kitchen" in result
        assert "Bedroom" in result
        assert len(result["Kitchen"]) == 1
        assert len(result["Bedroom"]) == 1

    def test_group_by_device(self, discovery):
        """Test grouping entities by device."""
        entities = [
            Entity(entity_id="light.test", state="on", attributes={}, last_changed=NOW, last_updated=NOW, domain="light", entity_type=EntityType.LIGHT, device_info={"device_id": "dev1"}),
            Entity(entity_id="sensor.test", state="22", attributes={}, last_changed=NOW, last_updated=NOW, domain="sensor", entity_type=EntityType.SENSOR, device_info={"device_id": "dev1"}),
        ]

        result = discovery.group_by_device(entities)
        assert len(result) == 1
        assert len(list(result.values())[0]) == 2

    def test_get_summary(self, discovery):
        """Test entity summary generation."""
        entities = [
            Entity(entity_id="light.kitchen", state="on", attributes={}, last_changed=NOW, last_updated=NOW, domain="light", entity_type=EntityType.LIGHT, area_name="Kitchen"),
            Entity(entity_id="sensor.temp", state="22", attributes={}, last_changed=NOW, last_updated=NOW, domain="sensor", entity_type=EntityType.SENSOR, area_name="Kitchen"),
        ]

        result = discovery.get_summary(entities)
        assert result["total"] == 2
        assert result["by_domain"]["light"] == 1
        assert result["by_domain"]["sensor"] == 1
        assert result["by_area"]["Kitchen"] == 2
