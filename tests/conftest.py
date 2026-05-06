"""Shared pytest fixtures for HA Integration API tests."""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest


# Patch ClientTimeout to a valid exception class — in aiohttp 3.x it's a config
# object (not an exception), but the production code catches it in an except
# clause. Without this fix, any exception propagating through that clause would
# raise TypeError: "catching classes that do not inherit from BaseException".
@pytest.fixture(autouse=True)
def patch_aiohttp_client_timeout():
    """Replace ClientTimeout with ConnectionTimeoutError (a real exception)."""
    with patch.object(aiohttp, 'ClientTimeout', aiohttp.ConnectionTimeoutError):
        yield


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_ha_client():
    """Provide a mocked HAClient with predictable responses.
    
    Usage:
        async def test_something(mock_ha_client):
            mock_ha_client.get_states.return_value = [...]
            result = await some_function(mock_ha_client)
    """
    client = AsyncMock()
    
    # Default return values for common methods
    client.get_states.return_value = [
        {
            "entity_id": "light.test",
            "state": "on",
            "attributes": {"brightness": 200},
            "last_changed": "2024-01-01T00:00:00",
            "last_updated": "2024-01-01T00:00:00",
        }
    ]
    
    client.get_state.return_value = {
        "entity_id": "light.test",
        "state": "on",
        "attributes": {"brightness": 200},
        "last_changed": "2024-01-01T00:00:00",
        "last_updated": "2024-01-01T00:00:00",
    }
    
    client.set_state.return_value = {"entity_id": "light.test"}
    
    client.call_service.return_value = {"result": "success"}
    
    client.check_health.return_value = {"status": "ok", "url": "http://test.local"}
    
    # Mock context manager
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock()
    
    return client


@pytest.fixture
async def mock_cache():
    """Provide an in-memory SQLite cache for testing.
    
    Uses :memory: SQLite database so no disk I/O is needed.
    
    Usage:
        async def test_something(mock_cache):
            await mock_cache.set("light.test", {"state": "on"})
            state = await mock_cache.get("light.test")
    """
    from app.cache import EntityCache
    
    # Create cache with in-memory SQLite - this auto-creates tables
    cache = EntityCache(db_path=":memory:", ttl_seconds=60)
    
    yield cache


@pytest.fixture
def sample_entity():
    """Provide a sample Entity object for testing."""
    from app.models import Entity, EntityType
    
    return Entity(
        entity_id="light.test",
        state="on",
        attributes={"brightness": 200},
        last_changed=datetime.now(),
        last_updated=datetime.now(),
        domain="light",
        entity_type=EntityType.LIGHT,
        area_name="Living Room",
        device_info={"device_id": "dev1"},
    )


@pytest.fixture
def sample_entities():
    """Provide a list of sample entities for testing."""
    from app.models import Entity, EntityType
    
    now = datetime.now()
    return [
        Entity(
            entity_id="light.kitchen",
            state="on",
            attributes={},
            last_changed=now,
            last_updated=now,
            domain="light",
            entity_type=EntityType.LIGHT,
            area_name="Kitchen",
        ),
        Entity(
            entity_id="sensor.temperature",
            state="22.5",
            attributes={"unit_of_measurement": "°C"},
            last_changed=now,
            last_updated=now,
            domain="sensor",
            entity_type=EntityType.SENSOR,
            area_name="Kitchen",
        ),
        Entity(
            entity_id="switch.bedroom",
            state="off",
            attributes={},
            last_changed=now,
            last_updated=now,
            domain="switch",
            entity_type=EntityType.SWITCH,
            area_name="Bedroom",
        ),
    ]


@pytest.fixture
def sample_states():
    """Provide sample HA state data for testing."""
    return [
        {
            "entity_id": "light.kitchen",
            "state": "on",
            "attributes": {"brightness": 150},
            "last_changed": "2024-01-01T10:00:00",
            "last_updated": "2024-01-01T10:00:00",
        },
        {
            "entity_id": "sensor.temperature",
            "state": "22.5",
            "attributes": {"unit_of_measurement": "°C"},
            "last_changed": "2024-01-01T10:00:00",
            "last_updated": "2024-01-01T10:00:00",
        },
    ]


@pytest.fixture
def settings():
    """Provide a mock settings object for testing."""
    from app.config import Settings
    
    class MockSettings(Settings):
        ha_url: str = "http://test.local"
        ha_token: str = "test-token"
        ha_timeout: float = 5.0
        ha_max_retries: int = 2
        ha_retry_delay: float = 0.1
        cache_ttl_seconds: int = 60
        cache_refresh_interval: int = 300
        ws_ping_interval: float = 30.0
        ws_ping_timeout: float = 10.0
        host: str = "0.0.0.0"
        port: int = 8000
    
    return MockSettings()


# Monkey-patch the settings instance in app.config
@pytest.fixture(autouse=True)
def patch_settings(settings):
    """Automatically patch settings for all tests."""
    import sys
    from unittest.mock import patch
    
    with patch('app.config.settings', settings):
        yield
