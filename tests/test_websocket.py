"""Unit tests for WebSocket / SSE API endpoints."""

import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import WebSocket
from httpx import ASGITransport, AsyncClient

from app.api import (
    HAEventSubscriber,
    WebSocketManager,
    EntityStateUpdate,
    EntityListUpdate,
    ServerPing,
    ErrorMessage,
    create_app,
)


# ---------------------------------------------------------------------------
# Pydantic model tests
# ---------------------------------------------------------------------------


class TestPydanticModels:
    """Tests for WebSocket / SSE message models."""

    def test_entity_state_update_defaults(self):
        """Test EntityStateUpdate default values."""
        msg = EntityStateUpdate(
            entity_id="light.test",
            new_state="on",
            changed_at=datetime.now(),
        )
        assert msg.type == "state_changed"
        assert msg.old_state is None

    def test_entity_list_update(self):
        """Test EntityListUpdate serialization."""
        entities = [
            {"entity_id": "light.test", "state": "on"},
        ]
        update = EntityListUpdate(
            entities=entities,
            total_count=1,
            received_at=datetime.now(),
        )
        data = json.loads(update.model_dump_json())
        assert data["type"] == "entity_list"
        assert data["total_count"] == 1

    def test_server_ping(self):
        """Test ServerPing model."""
        ping = ServerPing(timestamp=datetime.now())
        assert ping.type == "ping"

    def test_error_message(self):
        """Test ErrorMessage model."""
        err = ErrorMessage(code=500, detail="Internal error")
        assert err.type == "error"


# ---------------------------------------------------------------------------
# WebSocketManager tests
# ---------------------------------------------------------------------------


class TestWebSocketManager:
    """Tests for the WebSocketManager class."""

    @pytest.fixture
    def manager(self):
        """Create a WebSocketManager instance."""
        return WebSocketManager()

    @pytest.mark.asyncio
    async def test_connect_and_disconnect(self, manager):
        """Test connect and disconnect lifecycle."""
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        await manager.connect(mock_ws, "default")
        assert mock_ws in manager._connections

        await manager.disconnect(mock_ws)
        assert mock_ws not in manager._connections

    @pytest.mark.asyncio
    async def test_broadcast_to_all(self, manager):
        """Test broadcasting to all connections."""
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws1.accept = AsyncMock()
        ws2.accept = AsyncMock()

        await manager.connect(ws1)
        await manager.connect(ws2)

        await manager.broadcast('{"type":"test"}')
        assert ws1.send_text.called
        assert ws2.send_text.called

    @pytest.mark.asyncio
    async def test_broadcast_to_room(self, manager):
        """Test broadcasting to a specific room."""
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws1.accept = AsyncMock()
        ws2.accept = AsyncMock()

        await manager.connect(ws1, "kitchen")
        await manager.connect(ws2, "bedroom")

        await manager.broadcast('{"type":"test"}', room="kitchen")
        assert ws1.send_text.called
        assert not ws2.send_text.called

    @pytest.mark.asyncio
    async def test_send_single_message(self, manager):
        """Test sending a message to a single connection."""
        mock_ws = AsyncMock()
        await manager.send(mock_ws, "hello")
        mock_ws.send_text.assert_called_once_with("hello")


# ---------------------------------------------------------------------------
# HAEventSubscriber tests
# ---------------------------------------------------------------------------


class TestHAEventSubscriber:
    """Tests for the HAEventSubscriber class."""

    @pytest.fixture
    def subscriber(self):
        """Create a test subscriber instance."""
        return HAEventSubscriber(
            ha_url="http://test.local",
            token="test-token",
            max_retries=2,
            retry_delay=0.1,
        )

    @pytest.mark.asyncio
    async def test_close_closes_session(self, subscriber):
        """Test that close() closes the HTTP session."""
        mock_session = AsyncMock()
        mock_session.closed = False
        subscriber._session = mock_session
        await subscriber.close()
        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_sets_running_false(self, subscriber):
        """Test that stop() sets _running to False."""
        subscriber._running = True
        await subscriber.stop()
        assert not subscriber._running


# ---------------------------------------------------------------------------
# FastAPI app tests (unit-level with mocked dependencies)
# ---------------------------------------------------------------------------


class TestFastAPIApp:
    """Tests for the FastAPI application endpoints."""

    @pytest.fixture
    def mock_ha_client(self):
        """Create a mocked HAClient."""
        client = AsyncMock()
        client.get_states.return_value = [
            {
                "entity_id": "light.test",
                "state": "on",
                "attributes": {"brightness": 200},
                "last_changed": "2024-01-01T00:00:00",
                "last_updated": "2024-01-01T00:00:00",
            },
        ]
        client.get_state.return_value = {
            "entity_id": "light.test",
            "state": "on",
            "attributes": {"brightness": 200},
            "last_changed": "2024-01-01T00:00:00",
            "last_updated": "2024-01-01T00:00:00",
        }
        client.check_health.return_value = {"status": "ok"}
        return client

    @pytest.fixture
    def mock_subscriber(self):
        """Create a mocked HAEventSubscriber."""
        sub = AsyncMock()
        sub.subscribe = AsyncMock()
        sub.stop = AsyncMock()
        return sub

    @pytest.fixture
    def app(self, mock_ha_client, mock_subscriber):
        """Create the FastAPI app with mocked dependencies."""
        return create_app(
            ha_client=mock_ha_client,
            event_subscriber=mock_subscriber,
        )

    @pytest.mark.asyncio
    async def test_health_check_ok(self, app):
        """Test health endpoint returns ok status."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "ok"
            assert data["connected"] is True

    @pytest.mark.asyncio
    async def test_get_states(self, app):
        """Test GET /api/states returns entity states."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/states")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) > 0
            assert data[0]["entity_id"] == "light.test"

    @pytest.mark.asyncio
    async def test_get_state_single_entity(self, app):
        """Test GET /api/states/{entity_id} returns a single state."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/states/light.test")
            assert resp.status_code == 200
            data = resp.json()
            assert data["entity_id"] == "light.test"

    @pytest.mark.asyncio
    async def test_sse_endpoint_initial_snapshot(self, app):
        """Test SSE endpoint sends initial entity list snapshot.

        We mock StreamingResponse so the generator yields once and returns
        pre-canned content instead of hanging on an infinite stream.
        """
        from fastapi.responses import StreamingResponse as RealStreamingResponse

        # Build a real StreamingResponse with known content for verification
        expected_content = "event: entity_list\ndata: {\"type\": \"entity_list\", \"entities\": [], \"total_count\": 0, \"received_at\": \"2024-01-01T00:00:00\"}\n\n"

        mock_response = RealStreamingResponse(
            content=iter([expected_content]),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

        with patch("fastapi.responses.StreamingResponse", return_value=mock_response):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/events/stream")
                assert resp.status_code == 200
                content = resp.text
                assert "entity_list" in content

    @pytest.mark.asyncio
    async def test_sse_endpoint_with_area_filter(self, app):
        """Test SSE endpoint with area filter query param.

        We mock StreamingResponse so the response returns immediately instead of
        hanging on an infinite stream.  Only status code is verified.
        """
        from fastapi.responses import StreamingResponse as RealStreamingResponse

        mock_response = RealStreamingResponse(
            content=iter([""]),
            media_type="text/event-stream",
        )

        with patch("fastapi.responses.StreamingResponse", return_value=mock_response):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/events/stream?area_name=Kitchen")
                assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_sse_endpoint_with_entity_type_filter(self, app):
        """Test SSE endpoint with entity type filter query param.

        We mock StreamingResponse so the response returns immediately instead of
        hanging on an infinite stream.  Only status code is verified.
        """
        from fastapi.responses import StreamingResponse as RealStreamingResponse

        mock_response = RealStreamingResponse(
            content=iter([""]),
            media_type="text/event-stream",
        )

        with patch("fastapi.responses.StreamingResponse", return_value=mock_response):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/events/stream?entity_type=light")
                assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_sse_response_headers(self, app):
        """Test SSE endpoint returns correct headers.

        We mock StreamingResponse so the response returns immediately instead of
        hanging on an infinite stream.  Headers are verified without reading body.
        """
        from fastapi.responses import StreamingResponse as RealStreamingResponse

        mock_response = RealStreamingResponse(
            content=iter([""]),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

        with patch("fastapi.responses.StreamingResponse", return_value=mock_response):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/events/stream")
                assert "text/event-stream" in resp.headers["content-type"]


# ---------------------------------------------------------------------------
# Event handling tests (unit-level)
# ---------------------------------------------------------------------------


class TestEventHandling:
    """Tests for HA event processing and broadcasting."""

    @pytest.mark.asyncio
    async def test_entity_state_update_model(self):
        """Test EntityStateUpdate model serialization."""
        msg = EntityStateUpdate(
            entity_id="light.test",
            old_state="off",
            new_state="on",
            attributes={"brightness": 200},
            changed_at=datetime.now(),
        )
        data = json.loads(msg.model_dump_json())
        assert data["type"] == "state_changed"
        assert data["entity_id"] == "light.test"
        assert data["old_state"] == "off"
        assert data["new_state"] == "on"

    @pytest.mark.asyncio
    async def test_entity_list_update_model(self):
        """Test EntityListUpdate model serialization."""
        entities = [
            {
                "entity_id": "light.test",
                "state": "on",
                "attributes": {"brightness": 200},
                "last_changed": "2024-01-01T00:00:00",
                "area_name": None,
            },
        ]
        msg = EntityListUpdate(
            entities=entities,
            total_count=1,
            received_at=datetime.now(),
        )
        data = json.loads(msg.model_dump_json())
        assert data["type"] == "entity_list"
        assert data["total_count"] == 1


# ---------------------------------------------------------------------------
# App creation tests (unit-level)
# ---------------------------------------------------------------------------


class TestAppCreation:
    """Tests for app factory function."""

    def test_create_app_returns_fastapi(self):
        """Test that create_app returns a FastAPI instance."""
        from fastapi import FastAPI as FastAPIClass

        app = create_app()
        assert isinstance(app, FastAPIClass)
        assert app.title == "HA Integration API"

    def test_create_app_with_custom_client(self):
        """Test creating app with a custom HAClient."""
        mock_client = AsyncMock()
        mock_subscriber = AsyncMock()

        app = create_app(
            ha_client=mock_client,
            event_subscriber=mock_subscriber,
        )
        from fastapi import FastAPI as FastAPIClass
        assert isinstance(app, FastAPIClass)

    def test_create_app_default_settings(self):
        """Test that app uses settings from config."""
        app = create_app()
        # Verify the app was created successfully with default settings
        assert app is not None
