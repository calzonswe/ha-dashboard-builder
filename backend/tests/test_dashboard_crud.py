"""Dashboard and widget CRUD API tests (Phase 4).

Tests for creating, listing, updating, and deleting dashboards and widgets.
These endpoints don't require an HA connection — they operate on the local SQLite DB.
"""

from fastapi.testclient import TestClient
from app.main import app


class TestDashboardCRUD:
    """Test dashboard (page) creation, retrieval, listing, and deletion."""

    def test_create_dashboard(self):
        """POST /api/v1/dashboards -> 201 with created dashboard data."""
        resp = TestClient(app).post(
            "/api/v1/dashboards", json={"name": "Living Room"}
        )
        assert resp.status_code == 201, f"Response: {resp.json()}"
        data = resp.json()
        assert data["id"] is not None
        assert data["name"] == "Living Room"

    def test_create_multiple_dashboards(self):
        """Create multiple dashboards and verify they all exist."""
        names = ["Kitchen", "Bedroom", "Office"]
        for name in names:
            resp = TestClient(app).post(
                "/api/v1/dashboards", json={"name": name}
            )
            assert resp.status_code == 201

        # Verify all exist via list endpoint
        resp = TestClient(app).get("/api/v1/dashboards")
        assert resp.status_code == 200
        data = resp.json()
        assert "dashboards" in data
        assert "count" in data
        dashboard_names = {d["name"] for d in data["dashboards"]}
        for name in names:
            assert name in dashboard_names

    def test_list_dashboards(self):
        """GET /api/v1/dashboards -> 200 with list of dashboards."""
        resp = TestClient(app).get("/api/v1/dashboards")
        assert resp.status_code == 200
        data = resp.json()
        assert "dashboards" in data
        assert "count" in data
        assert isinstance(data["count"], int)

    def test_get_single_dashboard(self):
        """GET /api/v1/dashboards/{id} -> 200 with dashboard + empty cards."""
        resp = TestClient(app).post(
            "/api/v1/dashboards", json={"name": "Get Test"}
        )
        assert resp.status_code == 201
        dashboard_id = resp.json()["id"]

        resp = TestClient(app).get(f"/api/v1/dashboards/{dashboard_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == dashboard_id
        assert data["name"] == "Get Test"
        assert isinstance(data["cards"], list)

    def test_get_nonexistent_dashboard(self):
        """GET /api/v1/dashboards/9999 -> 404."""
        resp = TestClient(app).get("/api/v1/dashboards/9999")
        assert resp.status_code == 404

    def test_delete_dashboard(self):
        """DELETE /api/v1/dashboards/{id} -> 204 and verify removal."""
        resp = TestClient(app).post(
            "/api/v1/dashboards", json={"name": "Delete Me"}
        )
        assert resp.status_code == 201
        dashboard_id = resp.json()["id"]

        # Delete it
        resp = TestClient(app).delete(f"/api/v1/dashboards/{dashboard_id}")
        assert resp.status_code == 204

        # Verify gone
        resp = TestClient(app).get(f"/api/v1/dashboards/{dashboard_id}")
        assert resp.status_code == 404


class TestWidgetCRUD:
    """Test widget (card) creation, retrieval, updating, and deletion."""

    def _create_dashboard(self):
        """Helper to create a dashboard and return its ID."""
        resp = TestClient(app).post(
            "/api/v1/dashboards", json={"name": "Widget Test"}
        )
        assert resp.status_code == 201
        return resp.json()["id"]

    def test_create_widget(self):
        """POST /api/v1/dashboards/{id}/widgets -> 201 with widget data."""
        dashboard_id = self._create_dashboard()

        resp = TestClient(app).post(
            f"/api/v1/dashboards/{dashboard_id}/widgets",
            json={
                "card_type": "switch",
                "entity_id": "switch.living_room_light",
                "title": "Living Room Light",
                "config": {"color": "blue"},
                "x": 2,
                "y": 3,
                "width": 2,
                "height": 1,
            },
        )
        assert resp.status_code == 201, f"Response: {resp.json()}"
        data = resp.json()
        assert data["id"] is not None
        assert data["card_type"] == "switch"
        assert data["entity_id"] == "switch.living_room_light"
        assert data["title"] == "Living Room Light"
        assert data["config"] == {"color": "blue"}
        assert data["x"] == 2
        assert data["y"] == 3

    def test_create_widget_without_entity(self):
        """Create a widget with no entity (e.g., an empty spacer)."""
        dashboard_id = self._create_dashboard()

        resp = TestClient(app).post(
            f"/api/v1/dashboards/{dashboard_id}/widgets",
            json={
                "card_type": "spacer",
                "title": "",
                "config": {},
                "x": 0,
                "y": 0,
                "width": 2,
                "height": 1,
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["entity_id"] is None

    def test_list_widgets(self):
        """GET /api/v1/dashboards/{id}/widgets -> 200 with widget list."""
        dashboard_id = self._create_dashboard()

        # Create 3 widgets
        for i in range(3):
            TestClient(app).post(
                f"/api/v1/dashboards/{dashboard_id}/widgets",
                json={
                    "card_type": "sensor",
                    "entity_id": f"sensor.temp_{i}",
                    "title": f"Sensor {i}",
                    "config": {},
                    "x": i,
                    "y": 0,
                    "width": 2,
                    "height": 1,
                },
            )

        resp = TestClient(app).get(f"/api/v1/dashboards/{dashboard_id}/widgets")
        assert resp.status_code == 200
        data = resp.json()
        assert "widgets" in data
        assert "count" in data
        assert data["count"] >= 3

    def test_get_dashboard_with_widgets(self):
        """GET /api/v1/dashboards/{id} returns widgets in cards."""
        dashboard_id = self._create_dashboard()

        TestClient(app).post(
            f"/api/v1/dashboards/{dashboard_id}/widgets",
            json={
                "card_type": "light",
                "entity_id": "light.living_room",
                "title": "Living Room Light",
                "config": {"color_mode": "rgb"},
                "x": 2,
                "y": 1,
                "width": 3,
                "height": 2,
            },
        )

        resp = TestClient(app).get(f"/api/v1/dashboards/{dashboard_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["cards"]) >= 1
        card = data["cards"][0]
        assert card["card_type"] == "light"
        assert card["entity_id"] == "light.living_room"

    def test_update_widget(self):
        """PUT /api/v1/dashboards/{pid}/widgets/{wid} -> 200 with updated data."""
        dashboard_id = self._create_dashboard()

        # Create a widget
        resp = TestClient(app).post(
            f"/api/v1/dashboards/{dashboard_id}/widgets",
            json={
                "card_type": "switch",
                "entity_id": "switch.old_name",
                "title": "Old Title",
                "config": {"color": "red"},
                "x": 1,
                "y": 1,
                "width": 2,
                "height": 1,
            },
        )
        assert resp.status_code == 201
        widget_id = resp.json()["id"]

        # Update it
        resp = TestClient(app).put(
            f"/api/v1/dashboards/{dashboard_id}/widgets/{widget_id}",
            json={
                "card_type": "light",
                "entity_id": "switch.new_name",
                "title": "New Title",
                "config": {"color": "green"},
                "x": 5,
                "y": 10,
                "width": 4,
                "height": 2,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["card_type"] == "light"
        assert data["entity_id"] == "switch.new_name"
        assert data["title"] == "New Title"
        assert data["config"]["color"] == "green"
        assert data["x"] == 5
        assert data["y"] == 10

    def test_delete_widget(self):
        """DELETE /api/v1/dashboards/{pid}/widgets/{wid} -> 204."""
        dashboard_id = self._create_dashboard()

        # Create a widget
        resp = TestClient(app).post(
            f"/api/v1/dashboards/{dashboard_id}/widgets",
            json={
                "card_type": "sensor",
                "entity_id": "sensor.temp_1",
                "title": "Temp 1",
                "config": {},
                "x": 0,
                "y": 0,
                "width": 2,
                "height": 1,
            },
        )
        assert resp.status_code == 201
        widget_id = resp.json()["id"]

        # Delete it
        resp = TestClient(app).delete(
            f"/api/v1/dashboards/{dashboard_id}/widgets/{widget_id}"
        )
        assert resp.status_code == 204

        # Verify gone
        resp = TestClient(app).get(f"/api/v1/dashboards/{dashboard_id}/widgets")
        data = resp.json()
        assert data["count"] == 0

    def test_delete_dashboard_cascades(self):
        """DELETE dashboard also removes all its widgets."""
        dashboard_id = self._create_dashboard()

        # Create 2 widgets on this dashboard
        for i in range(2):
            TestClient(app).post(
                f"/api/v1/dashboards/{dashboard_id}/widgets",
                json={
                    "card_type": "switch",
                    "entity_id": f"switch.test_{i}",
                    "title": f"Switch {i}",
                    "config": {},
                    "x": i,
                    "y": 0,
                    "width": 2,
                    "height": 1,
                },
            )

        # Delete dashboard
        resp = TestClient(app).delete(f"/api/v1/dashboards/{dashboard_id}")
        assert resp.status_code == 204

        # Verify dashboard and its widgets are gone (cascade delete)
        resp = TestClient(app).get(f"/api/v1/dashboards/{dashboard_id}/widgets")
        assert resp.status_code == 404


class TestWidgetGridConstraints:
    """Test that widget grid constraints are enforced."""

    def _create_dashboard(self):
        resp = TestClient(app).post(
            "/api/v1/dashboards", json={"name": "Grid Test"}
        )
        assert resp.status_code == 201
        return resp.json()["id"]

    def test_widget_width_constraint(self):
        """Width must be between 1 and 12."""
        dashboard_id = self._create_dashboard()

        # Width=0 should fail (constraint violation)
        resp = TestClient(app).post(
            f"/api/v1/dashboards/{dashboard_id}/widgets",
            json={
                "card_type": "switch",
                "entity_id": "switch.test",
                "config": {},
                "x": 0,
                "y": 0,
                "width": 0,
                "height": 1,
            },
        )
        assert resp.status_code == 422  # Validation error

    def test_widget_height_constraint(self):
        """Height must be between 1 and 10."""
        dashboard_id = self._create_dashboard()

        # Height=0 should fail
        resp = TestClient(app).post(
            f"/api/v1/dashboards/{dashboard_id}/widgets",
            json={
                "card_type": "switch",
                "entity_id": "switch.test",
                "config": {},
                "x": 0,
                "y": 0,
                "width": 2,
                "height": 0,
            },
        )
        assert resp.status_code == 422

    def test_widget_x_constraint(self):
        """X must be between 0 and 12."""
        dashboard_id = self._create_dashboard()

        # X=13 should fail
        resp = TestClient(app).post(
            f"/api/v1/dashboards/{dashboard_id}/widgets",
            json={
                "card_type": "switch",
                "entity_id": "switch.test",
                "config": {},
                "x": 13,
                "y": 0,
                "width": 2,
                "height": 1,
            },
        )
        assert resp.status_code == 422

    def test_widget_y_constraint(self):
        """Y must be >= 0."""
        dashboard_id = self._create_dashboard()

        # Y=-1 should fail
        resp = TestClient(app).post(
            f"/api/v1/dashboards/{dashboard_id}/widgets",
            json={
                "card_type": "switch",
                "entity_id": "switch.test",
                "config": {},
                "x": 0,
                "y": -1,
                "width": 2,
                "height": 1,
            },
        )
        assert resp.status_code == 422


class TestDashboardWidgetIntegration:
    """End-to-end integration tests for dashboard + widget workflows."""

    def test_full_dashboard_workflow(self):
        """Create dashboard -> add widgets -> retrieve full dashboard."""
        # Create dashboard
        dash_resp = TestClient(app).post(
            "/api/v1/dashboards", json={"name": "Full Kitchen"}
        )
        assert dash_resp.status_code == 201
        dashboard_id = dash_resp.json()["id"]

        # Add a light widget
        light_resp = TestClient(app).post(
            f"/api/v1/dashboards/{dashboard_id}/widgets",
            json={
                "card_type": "light",
                "entity_id": "light.kitchen_overhead",
                "title": "Kitchen Overhead",
                "config": {"color_mode": "brightness"},
                "x": 2,
                "y": 1,
                "width": 3,
                "height": 2,
            },
        )
        assert light_resp.status_code == 201

        # Add a sensor widget
        sensor_resp = TestClient(app).post(
            f"/api/v1/dashboards/{dashboard_id}/widgets",
            json={
                "card_type": "sensor",
                "entity_id": "sensor.kitchen_temperature",
                "title": "Kitchen Temp",
                "config": {"unit": "°C"},
                "x": 6,
                "y": 1,
                "width": 3,
                "height": 2,
            },
        )
        assert sensor_resp.status_code == 201

        # Add a switch widget
        switch_resp = TestClient(app).post(
            f"/api/v1/dashboards/{dashboard_id}/widgets",
            json={
                "card_type": "switch",
                "entity_id": "switch.kitchen_fan",
                "title": "Kitchen Fan",
                "config": {},
                "x": 2,
                "y": 4,
                "width": 2,
                "height": 1,
            },
        )
        assert switch_resp.status_code == 201

        # Retrieve full dashboard and verify all widgets present
        resp = TestClient(app).get(f"/api/v1/dashboards/{dashboard_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Full Kitchen"
        assert len(data["cards"]) >= 3

        # Verify card types
        card_types = {c["card_type"] for c in data["cards"]}
        assert "light" in card_types
        assert "sensor" in card_types
        assert "switch" in card_types

    def test_widget_ordering(self):
        """Widgets should be ordered by y, then x."""
        resp = TestClient(app).post(
            "/api/v1/dashboards", json={"name": "Ordering Test"}
        )
        dashboard_id = resp.json()["id"]

        # Add widgets in reverse order
        TestClient(app).post(
            f"/api/v1/dashboards/{dashboard_id}/widgets",
            json={
                "card_type": "sensor",
                "entity_id": "sensor.z",
                "config": {},
                "x": 0,
                "y": 5,
                "width": 2,
                "height": 1,
            },
        )
        TestClient(app).post(
            f"/api/v1/dashboards/{dashboard_id}/widgets",
            json={
                "card_type": "sensor",
                "entity_id": "sensor.a",
                "config": {},
                "x": 0,
                "y": 1,
                "width": 2,
                "height": 1,
            },
        )

        resp = TestClient(app).get(f"/api/v1/dashboards/{dashboard_id}")
        assert resp.status_code == 200
        cards = resp.json()["cards"]
        # Widget at y=1 should come before widget at y=5
        first_y = cards[0]["y"] if cards else -1
        last_y = cards[-1]["y"] if len(cards) > 1 else -1
        assert first_y <= last_y
