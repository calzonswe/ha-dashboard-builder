"""Shared test fixtures for integration testing."""

import pytest
from unittest.mock import MagicMock


def pytest_configure(config):
    """Delete stale DB file before any tests run so init_db() creates fresh schema."""
    import pathlib

    db_path = pathlib.Path(__file__).parent.parent / "ha_dashboard.db"
    if db_path.exists():
        db_path.unlink()


def pytest_sessionstart(session):
    """Initialize the database after deleting stale DB file."""
    from app.database import init_db

    init_db()


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
            "attributes": {
                "friendly_name": "Living Room Temperature",
                "unit_of_measurement": "°C",
            },
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
        {
            "entity_id": "sensor.bedroom_temperature",
            "state": "21.0",
            "attributes": {"friendly_name": "Bedroom Temperature", "unit_of_measurement": "°C"},
            "last_changed": "2026-05-06T10:01:00Z",
        },
        {
            "entity_id": "sensor.outdoor_temperature",
            "state": "18.3",
            "attributes": {"friendly_name": "Outdoor Temperature", "unit_of_measurement": "°C"},
            "last_changed": "2026-05-06T10:02:00Z",
        },
        {
            "entity_id": "sensor.living_room_humidity",
            "state": "45.2",
            "attributes": {"friendly_name": "Living Room Humidity", "unit_of_measurement": "%"},
            "last_changed": "2026-05-06T10:03:00Z",
        },
        {
            "entity_id": "sensor.bedroom_humidity",
            "state": "48.7",
            "attributes": {"friendly_name": "Bedroom Humidity", "unit_of_measurement": "%"},
            "last_changed": "2026-05-06T10:04:00Z",
        },
        {
            "entity_id": "sensor.kitchen_temperature",
            "state": "23.1",
            "attributes": {"friendly_name": "Kitchen Temperature", "unit_of_measurement": "°C"},
            "last_changed": "2026-05-06T10:05:00Z",
        },
        {
            "entity_id": "light.living_room_ceiling",
            "state": "on",
            "attributes": {"friendly_name": "Living Room Ceiling Light", "brightness": 150},
            "last_changed": "2026-05-06T09:30:00Z",
        },
        {
            "entity_id": "light.living_room_table_lamp",
            "state": "off",
            "attributes": {"friendly_name": "Living Room Table Lamp"},
            "last_changed": "2026-05-06T08:15:00Z",
        },
        {
            "entity_id": "light.bedroom_ceiling",
            "state": "on",
            "attributes": {"friendly_name": "Bedroom Ceiling Light"},
            "last_changed": "2026-05-06T19:00:00Z",
        },
        {
            "entity_id": "light.bedroom_nightstand",
            "state": "off",
            "attributes": {"friendly_name": "Bedroom Nightstand Lamp"},
            "last_changed": "2026-05-06T07:30:00Z",
        },
        {
            "entity_id": "light.kitchen_overhead",
            "state": "on",
            "attributes": {"friendly_name": "Kitchen Overhead Light"},
            "last_changed": "2026-05-06T08:00:00Z",
        },
        {
            "entity_id": "light.kitchen_under_cabinet",
            "state": "off",
            "attributes": {"friendly_name": "Kitchen Under Cabinet Light"},
            "last_changed": "2026-05-06T12:00:00Z",
        },
        {
            "entity_id": "light.bathroom_mirror",
            "state": "off",
            "attributes": {"friendly_name": "Bathroom Mirror Light"},
            "last_changed": "2026-05-06T07:45:00Z",
        },
        {
            "entity_id": "light.bathroom_ceiling",
            "state": "off",
            "attributes": {"friendly_name": "Bathroom Ceiling Light"},
            "last_changed": "2026-05-06T07:45:00Z",
        },
        {
            "entity_id": "switch.hallway_light",
            "state": "off",
            "attributes": {"friendly_name": "Hallway Light"},
            "last_changed": "2026-05-06T07:00:00Z",
        },
        {
            "entity_id": "switch.laundry_machine",
            "state": "off",
            "attributes": {"friendly_name": "Laundry Machine"},
            "last_changed": "2026-05-06T14:30:00Z",
        },
        {
            "entity_id": "switch.laundry_dryer",
            "state": "off",
            "attributes": {"friendly_name": "Laundry Dryer"},
            "last_changed": "2026-05-06T14:30:00Z",
        },
        {
            "entity_id": "switch.garage_door",
            "state": "closed",
            "attributes": {"friendly_name": "Garage Door"},
            "last_changed": "2026-05-06T08:30:00Z",
        },
        {
            "entity_id": "switch.garage_light",
            "state": "off",
            "attributes": {"friendly_name": "Garage Light"},
            "last_changed": "2026-05-06T08:30:00Z",
        },
        {
            "entity_id": "switch.porch_light",
            "state": "on",
            "attributes": {"friendly_name": "Porch Light"},
            "last_changed": "2026-05-06T18:00:00Z",
        },
        {
            "entity_id": "switch.garden_sprinkler",
            "state": "off",
            "attributes": {"friendly_name": "Garden Sprinkler"},
            "last_changed": "2026-05-06T14:00:00Z",
        },
        {
            "entity_id": "climate.living_room",
            "state": "heat",
            "attributes": {"friendly_name": "Living Room Thermostat", "temperature": 21.0},
            "last_changed": "2026-05-06T10:00:00Z",
        },
        {
            "entity_id": "climate.bedroom",
            "state": "off",
            "attributes": {"friendly_name": "Bedroom Thermostat"},
            "last_changed": "2026-05-06T07:00:00Z",
        },
        {
            "entity_id": "binary_sensor.living_room_motion",
            "state": "off",
            "attributes": {"friendly_name": "Living Room Motion Sensor"},
            "last_changed": "2026-05-06T10:00:00Z",
        },
        {
            "entity_id": "binary_sensor.front_door_motion",
            "state": "off",
            "attributes": {"friendly_name": "Front Door Motion Sensor"},
            "last_changed": "2026-05-06T10:00:00Z",
        },
        {
            "entity_id": "binary_sensor.back_door_motion",
            "state": "off",
            "attributes": {"friendly_name": "Back Door Motion Sensor"},
            "last_changed": "2026-05-06T10:00:00Z",
        },
        {
            "entity_id": "binary_sensor.garage_motion",
            "state": "off",
            "attributes": {"friendly_name": "Garage Motion Sensor"},
            "last_changed": "2026-05-06T10:00:00Z",
        },
        {
            "entity_id": "binary_sensor.front_door_lock",
            "state": "on",
            "attributes": {"friendly_name": "Front Door Lock"},
            "last_changed": "2026-05-06T18:30:00Z",
        },
        {
            "entity_id": "binary_sensor.back_door_lock",
            "state": "on",
            "attributes": {"friendly_name": "Back Door Lock"},
            "last_changed": "2026-05-06T18:30:00Z",
        },
        {
            "entity_id": "binary_sensor.garage_door_lock",
            "state": "on",
            "attributes": {"friendly_name": "Garage Door Lock"},
            "last_changed": "2026-05-06T18:30:00Z",
        },
        {
            "entity_id": "binary_sensor.window_living_room",
            "state": "off",
            "attributes": {"friendly_name": "Living Room Window"},
            "last_changed": "2026-05-06T18:30:00Z",
        },
        {
            "entity_id": "binary_sensor.window_bedroom",
            "state": "off",
            "attributes": {"friendly_name": "Bedroom Window"},
            "last_changed": "2026-05-06T18:30:00Z",
        },
        {
            "entity_id": "binary_sensor.window_kitchen",
            "state": "off",
            "attributes": {"friendly_name": "Kitchen Window"},
            "last_changed": "2026-05-06T18:30:00Z",
        },
        {
            "entity_id": "sensor.living_room_co2",
            "state": "420.5",
            "attributes": {"friendly_name": "Living Room CO2", "unit_of_measurement": "ppm"},
            "last_changed": "2026-05-06T10:00:00Z",
        },
        {
            "entity_id": "sensor.bedroom_co2",
            "state": "380.2",
            "attributes": {"friendly_name": "Bedroom CO2", "unit_of_measurement": "ppm"},
            "last_changed": "2026-05-06T10:00:00Z",
        },
        {
            "entity_id": "sensor.living_room_pm25",
            "state": "12.3",
            "attributes": {"friendly_name": "Living Room PM2.5", "unit_of_measurement": "µg/m³"},
            "last_changed": "2026-05-06T10:00:00Z",
        },
        {
            "entity_id": "sensor.kitchen_pm25",
            "state": "8.7",
            "attributes": {"friendly_name": "Kitchen PM2.5", "unit_of_measurement": "µg/m³"},
            "last_changed": "2026-05-06T10:00:00Z",
        },
        {
            "entity_id": "sensor.living_room_battery",
            "state": "87.5",
            "attributes": {"friendly_name": "Living Room Sensor Battery", "unit_of_measurement": "%"},
            "last_changed": "2026-05-06T10:00:00Z",
        },
        {
            "entity_id": "sensor.bedroom_battery",
            "state": "92.3",
            "attributes": {"friendly_name": "Bedroom Sensor Battery", "unit_of_measurement": "%"},
            "last_changed": "2026-05-06T10:00:00Z",
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
    monkeypatch.setattr(
        "app.services.ha_client.HAAPI", lambda *args, **kwargs: mock_ha_api
    )
