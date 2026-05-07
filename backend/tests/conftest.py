"""Shared test fixtures for integration testing."""

import os
import pytest
from unittest.mock import MagicMock


def pytest_configure(config):
    """Delete stale DB file before any tests run so init_db() creates fresh schema."""
    import pathlib
    db_path = pathlib.Path(__file__).parent.parent / "ha_dashboard.db"
    if db_path.exists():
        db_path.unlink()


@pytest.fixture(scope="session")
def mock_ha_api():
    """Create a fully mocked HAAPI instance with realistic responses."""
    from app.services.ha_client import HAAPI

    api = MagicMock(spec=HAAPI)

    api.test_connection.return_value = {
        "host": "192.168.1.50",
        "port": 8123,
        "entities": 42,
    }

    api.get_states.return_value = [
        {
            "entity_id": "sensor.living_room_temperature",
            "state": "22.5",
            "attributes": {"friendly_name": "Living Room Temperature", "unit_of_measurement": "°C"},
            "last_changed": "2026-05-06T10:00:00Z",
        },
        {
            "entity_id": "light.kitchen_lights",
            "state": "on",
            "attributes": {"friendly_name": "Kitchen Lights", "brightness": 200},
            "last_changed": "2026-05-06T09:30:00Z",
        },
        {
            "entity_id": "switch.front_door",
            "state": "off",
            "attributes": {"friendly_name": "Front Door Lock"},
            "last_changed": "2026-05-06T08:00:00Z",
        },
    ]

    api.get_state.return_value = {
        "entity_id": "sensor.living_room_temperature",
        "state": "22.5",
        "attributes": {"friendly_name": "Living Room Temperature"},
        "domain": "sensor",
        "entity_type": "temperature_sensor",
    }

    api.get_services.return_value = [
        {"domain": "light", "service": "turn_on"},
        {"domain": "light", "service": "turn_off"},
        {"domain": "switch", "service": "toggle"},
    ]

    api.call_service.return_value = {"message": "Service called successfully"}

    api.get_config.return_value = {
        "latitude": 59.3293,
        "longitude": 18.0686,
        "time_zone": "Europe/Stockholm",
        "name": "My Home Assistant",
    }

    api.get_areas.return_value = [
        {"id": "area_living_room", "name": "Living Room"},
        {"id": "area_kitchen", "name": "Kitchen"},
    ]

    api.get_devices.return_value = [
        {
            "id": "device_001",
            "name": "Temp Sensor 1",
            "area_id": "area_living_room",
            "manufacturer": "Aqara",
            "model": "Temperature Sensor",
        },
    ]

    api.get_entities_for_device.return_value = [
        {
            "entity_id": "sensor.living_room_temperature",
            "state": "22.5",
            "device_id": "device_001",
        }
    ]

    return api


@pytest.fixture(autouse=True)
def patch_ha_client(monkeypatch, mock_ha_api):
    """Automatically patch HAAPI in the app module for all tests."""
    monkeypatch.setattr("app.services.ha_client.HAAPI", lambda *args, **kwargs: mock_ha_api)
