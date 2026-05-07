"""Integration tests for HA Dashboard Builder API.

Tests use FastAPI's TestClient with a mocked HAAPI instance to verify
the full request/response flow without needing a real Home Assistant instance.
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app


class MockHAAPI:
    """Mock HAAPI that returns realistic data for integration tests."""

    def __init__(self, *args, **kwargs):
        self.host = kwargs.get("host", "192.168.1.50")
        self.port = kwargs.get("port", 8123)

    def test_connection(self):
        return {"host": self.host, "port": self.port, "entities": 42}

    def get_states(self):
        return [
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

    def get_state(self, entity_id):
        states = self.get_states()
        for s in states:
            if s["entity_id"] == entity_id:
                return {**s, "domain": s["entity_id"].split(".")[0], "entity_type": ""}
        return None

    def get_services(self):
        return [
            {"domain": "light", "service": "turn_on"},
            {"domain": "light", "service": "turn_off"},
            {"domain": "switch", "service": "toggle"},
        ]

    def call_service(self, domain, service, service_data=None):
        return {"message": f"Service {domain}/{service} called"}

    def get_config(self):
        return {"name": "My Home Assistant", "time_zone": "Europe/Stockholm"}

    def get_areas(self):
        return [
            {"id": "area_living_room", "name": "Living Room"},
            {"id": "area_kitchen", "name": "Kitchen"},
        ]

    def get_devices(self):
        return [
            {
                "id": "device_001",
                "name": "Temp Sensor 1",
                "area_id": "area_living_room",
                "manufacturer": "Aqara",
                "model": "Temperature Sensor",
            },
        ]

    def get_entities_for_device(self, device_id):
        return [
            {
                "entity_id": "sensor.living_room_temperature",
                "state": "22.5",
                "device_id": device_id,
            }
        ]


class TestHAConnection:
    """Integration tests for HA connection endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Patch HAAPI globally and create test client."""
        # Patch at module levels where HAAPI is imported/used
        with patch("app.main.HAAPI", MockHAAPI), patch("app.api.routes.HAAPI", MockHAAPI):

            # Reset global state before each test
            import app.api.routes as routes_module

            routes_module._ha_client = None
            routes_module._entity_service = None

            self.client = TestClient(app)
            yield

    def test_root_endpoint(self):
        """Test the root health check endpoint."""
        response = self.client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "HA Dashboard Builder API is running" in data["message"]

    def test_health_check(self):
        """Test the health check endpoint."""
        response = self.client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_connect_to_ha_success(self):
        """Test successful HA connection."""
        response = self.client.post(
            "/api/api/ha/connect",
            json={
                "host": "192.168.1.50",
                "port": 8123,
                "token": "test_token_abc123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["host"] == "192.168.1.50"
        assert data["port"] == 8123
        assert data["entities"] == 42

    def test_connect_to_ha_invalid_host(self):
        """Test connection with invalid host returns error."""
        import app.api.routes as routes_module
        from app.services.ha_client import HAConnectionError

        class FailingHAAPI:
            def __init__(self, *args, **kwargs):
                pass

            def test_connection(self):
                raise HAConnectionError("Cannot resolve host")

        with patch("app.api.routes.HAAPI", FailingHAAPI), patch("app.main.HAAPI", FailingHAAPI):

            routes_module._ha_client = None
            routes_module._entity_service = None

            response = self.client.post(
                "/api/api/ha/connect",
                json={"host": "invalid.host", "port": 8123, "token": "bad_token"},
            )
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data

    def test_ha_status_disconnected(self):
        """Test status endpoint when no connection exists."""
        import app.api.routes as routes_module

        routes_module._ha_client = None
        routes_module._entity_service = None

        response = self.client.get(
            "/api/api/ha/status",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is False


class TestEntityDiscovery:
    """Integration tests for entity discovery endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Patch HAAPI and establish a connection before each test."""
        with patch("app.main.HAAPI", MockHAAPI), patch("app.api.routes.HAAPI", MockHAAPI):

            import app.api.routes as routes_module

            # Establish connection first
            routes_module.set_ha_connection(host="192.168.1.50", port=8123, token="test_token")

            self.client = TestClient(app)
            yield

    def test_discover_entities(self):
        """Test full entity discovery flow."""
        response = self.client.post("/api/api/ha/discover")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["summary"]["total_entities"] > 0
        assert len(data["summary"]["domains"]) > 0

    def test_get_cached_entities(self):
        """Test retrieving cached entities after discovery."""
        # First discover
        self.client.post("/api/api/ha/discover")

        # Then get cached entities
        response = self.client.get("/api/api/ha/entities")
        assert response.status_code == 200
        data = response.json()
        assert "entities" in data
        assert "count" in data
        assert data["count"] > 0

    def test_get_entity_by_id(self):
        """Test fetching a specific entity by ID."""
        # Discover first to populate cache
        self.client.post("/api/api/ha/discover")

        response = self.client.get("/api/api/ha/entities/sensor.living_room_temperature")
        assert response.status_code == 200
        data = response.json()
        assert data["entity_id"] == "sensor.living_room_temperature"
        assert data["state"] == "22.5"

    def test_get_nonexistent_entity(self):
        """Test fetching an entity that doesn't exist."""
        # Discover first to populate cache
        self.client.post("/api/api/ha/discover")

        response = self.client.get("/api/api/ha/entities/sensor.nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


class TestEntitySearch:
    """Integration tests for entity search endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Patch HAAPI and establish connection + discovery before each test."""
        with patch("app.main.HAAPI", MockHAAPI), patch("app.api.routes.HAAPI", MockHAAPI):

            import app.api.routes as routes_module

            routes_module.set_ha_connection(host="192.168.1.50", port=8123, token="test_token")

            self.client = TestClient(app)
            yield

    def test_search_by_name(self):
        """Test searching entities by name."""
        # Discover to populate cache
        self.client.post("/api/api/ha/discover")

        response = self.client.post(
            "/api/api/ha/search",
            json={"query": "Living Room"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] > 0
        # Should find the temperature sensor
        entity_ids = [e["entity_id"] for e in data["entities"]]
        assert "sensor.living_room_temperature" in entity_ids

    def test_search_by_entity_id(self):
        """Test searching entities by entity ID."""
        self.client.post("/api/api/ha/discover")

        response = self.client.post(
            "/api/api/ha/search",
            json={"query": "kitchen_lights"},
        )
        assert response.status_code == 200
        data = response.json()
        entity_ids = [e["entity_id"] for e in data["entities"]]
        assert "light.kitchen_lights" in entity_ids

    def test_search_no_results(self):
        """Test search with no matching entities."""
        self.client.post("/api/api/ha/discover")

        response = self.client.post(
            "/api/api/ha/search",
            json={"query": "zzznonexistent"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0


class TestServiceCalls:
    """Integration tests for Home Assistant service call endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Patch HAAPI and establish connection before each test."""
        with patch("app.main.HAAPI", MockHAAPI), patch("app.api.routes.HAAPI", MockHAAPI):

            import app.api.routes as routes_module

            routes_module.set_ha_connection(host="192.168.1.50", port=8123, token="test_token")

            self.client = TestClient(app)
            yield

    def test_call_service_success(self):
        """Test successful service call."""
        response = self.client.post(
            "/api/api/ha/services/call",
            json={
                "domain": "light",
                "service": "turn_on",
                "service_data": {"entity_id": "light.kitchen_lights"},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "called successfully" in data["message"]

    def test_call_service_without_data(self):
        """Test service call without optional service_data."""
        response = self.client.post(
            "/api/api/ha/services/call",
            json={
                "domain": "switch",
                "service": "toggle",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestErrorHandling:
    """Integration tests for error handling scenarios."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Patch HAAPI and create test client."""
        with patch("app.main.HAAPI", MockHAAPI), patch("app.api.routes.HAAPI", MockHAAPI):

            import app.api.routes as routes_module

            routes_module._ha_client = None
            routes_module._entity_service = None

            self.client = TestClient(app)
            yield

    def test_search_without_connection(self):
        """Test search endpoint when no HA connection exists."""
        response = self.client.post(
            "/api/api/ha/search",
            json={"query": "test"},
        )
        assert response.status_code == 400
        data = response.json()
        assert "Entity discovery not initialized" in data["detail"]

    def test_service_call_without_connection(self):
        """Test service call when no HA connection exists."""
        response = self.client.post(
            "/api/api/ha/services/call",
            json={"domain": "light", "service": "turn_on"},
        )
        assert response.status_code == 400

    def test_invalid_search_query(self):
        """Test search with empty query returns validation error."""
        # First establish connection so we get past the dependency check
        import app.api.routes as routes_module

        routes_module.set_ha_connection(host="192.168.1.50", port=8123, token="test_token")

        response = self.client.post(
            "/api/api/ha/search",
            json={"query": ""},  # Empty query should fail validation
        )
        assert response.status_code == 422  # FastAPI validation error


class TestWebSocket:
    """Integration tests for WebSocket endpoint."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Patch HAAPI and establish connection before each test."""
        with patch("app.main.HAAPI", MockHAAPI), patch("app.api.routes.HAAPI", MockHAAPI):

            import app.api.routes as routes_module

            routes_module.set_ha_connection(host="192.168.1.50", port=8123, token="test_token")

            self.client = TestClient(app)
            yield

    def test_websocket_endpoint_exists(self):
        """Test that the WebSocket endpoint is registered."""
        # Check that the websocket route exists by looking at app routes
        from fastapi.routing import APIWebSocketRoute

        ws_routes = [r for r in self.client.app.routes if isinstance(r, APIWebSocketRoute)]
        assert len(ws_routes) > 0
