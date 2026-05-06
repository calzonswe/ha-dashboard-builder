"""Unit tests for HA client module."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from app.ha_client import HAClient, HAConnectionError, HATimeoutError


class TestHAClient:
    """Tests for the HAClient class."""

    @pytest.fixture
    def client(self):
        """Create a test client instance."""
        return HAClient(
            base_url="http://test.local",
            token="test-token",
            timeout=5.0,
            max_retries=2,
            retry_delay=0.1,
        )

    @pytest.mark.asyncio
    async def test_get_session_creates_new_session(self, client):
        """Test that _get_session creates a new aiohttp session."""
        session = await client._get_session()
        assert isinstance(session, aiohttp.ClientSession)
        assert session.headers.get("Authorization") == "Bearer test-token"

    @pytest.mark.asyncio
    async def test_get_session_reuses_same_session(self, client):
        """Test that _get_session reuses the same session."""
        session1 = await client._get_session()
        session2 = await client._get_session()
        assert session1 is session2

    @pytest.mark.asyncio
    async def test_close_closes_session(self, client):
        """Test that close() closes the HTTP session."""
        # Create a real session so we can mock its close method
        session = aiohttp.ClientSession()
        client._session = session
        
        with patch.object(session, 'close') as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_success(self, client):
        """Test successful request returns parsed JSON."""
        # Create a proper response object
        resp = AsyncMock()
        resp.status = 200
        resp.json = AsyncMock(return_value={"result": "ok"})

        # Create an async context manager that yields the response
        ctx_cm = MagicMock()
        ctx_cm.__aenter__ = AsyncMock(return_value=resp)
        ctx_cm.__aexit__ = AsyncMock(return_value=False)

        # Use MagicMock (not AsyncMock) so request() returns ctx_cm directly,
        # not wrapped in a coroutine.
        mock_session = MagicMock()
        mock_session.request.return_value = ctx_cm
        
        with patch.object(client, '_get_session', return_value=mock_session):
            result = await client._request("GET", "test")
            assert result == {"result": "ok"}

    @pytest.mark.asyncio
    async def test_request_401_raises_connection_error(self, client):
        """Test that 401 response raises HAConnectionError."""
        resp = AsyncMock()
        resp.status = 401

        ctx_cm = MagicMock()
        ctx_cm.__aenter__ = AsyncMock(return_value=resp)
        ctx_cm.__aexit__ = AsyncMock(return_value=False)

        # Use MagicMock (not AsyncMock) so request() returns ctx_cm directly
        mock_session = MagicMock()
        mock_session.request.return_value = ctx_cm
        
        with patch.object(client, '_get_session', return_value=mock_session):
            with pytest.raises(HAConnectionError) as exc_info:
                await client._request("GET", "test")
            assert "Unauthorized" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_request_403_raises_connection_error(self, client):
        """Test that 403 response raises HAConnectionError."""
        resp = AsyncMock()
        resp.status = 403

        ctx_cm = MagicMock()
        ctx_cm.__aenter__ = AsyncMock(return_value=resp)
        ctx_cm.__aexit__ = AsyncMock(return_value=False)

        # Use MagicMock (not AsyncMock) so request() returns ctx_cm directly
        mock_session = MagicMock()
        mock_session.request.return_value = ctx_cm
        
        with patch.object(client, '_get_session', return_value=mock_session):
            with pytest.raises(HAConnectionError) as exc_info:
                await client._request("GET", "test")
            assert "Forbidden" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_request_500_retries(self, client):
        """Test that 500 errors trigger retry."""
        resp = AsyncMock()
        resp.status = 500
        resp.text = AsyncMock(return_value="Server Error")

        ctx_cm = MagicMock()
        ctx_cm.__aenter__ = AsyncMock(return_value=resp)
        ctx_cm.__aexit__ = AsyncMock(return_value=False)

        # Use MagicMock (not AsyncMock) so request() returns ctx_cm directly
        mock_session = MagicMock()
        mock_session.request.return_value = ctx_cm
        
        with patch.object(client, '_get_session', return_value=mock_session):
            with pytest.raises(HAConnectionError):
                await client._request("GET", "test")
            assert mock_session.request.call_count == 2  # max_retries = 2

    @pytest.mark.asyncio
    async def test_get_states(self, client):
        """Test get_states() method."""
        expected = [{"entity_id": "light.test", "state": "on"}]
        with patch.object(client, '_request', return_value=expected) as mock_req:
            result = await client.get_states()
            assert result == expected
            mock_req.assert_called_once_with("GET", "states")

    @pytest.mark.asyncio
    async def test_get_state(self, client):
        """Test get_state() method."""
        with patch.object(client, '_request', return_value={"entity_id": "light.test"}) as mock_req:
            result = await client.get_state("light.test")
            assert result == {"entity_id": "light.test"}
            mock_req.assert_called_once_with("GET", "states/light.test")

    @pytest.mark.asyncio
    async def test_set_state(self, client):
        """Test set_state() method."""
        with patch.object(client, '_request', return_value={"entity_id": "light.test"}) as mock_req:
            result = await client.set_state("light.test", "on", {"brightness": 100})
            assert result == {"entity_id": "light.test"}
            mock_req.assert_called_once_with(
                "POST", "states/light.test", json_data={"state": "on", "attributes": {"brightness": 100}}
            )

    @pytest.mark.asyncio
    async def test_call_service(self, client):
        """Test call_service() method."""
        with patch.object(client, '_request', return_value={"result": "success"}) as mock_req:
            result = await client.call_service("light", "turn_on", {"entity_id": "light.test"})
            assert result == {"result": "success"}
            mock_req.assert_called_once_with(
                "POST", "services/light/turn_on", json_data={"domain": "light", "service": "turn_on", "data": {"entity_id": "light.test"}}
            )

    @pytest.mark.asyncio
    async def test_check_health_ok(self, client):
        """Test check_health() returns ok status."""
        with patch.object(client, '_request', return_value={"status": "ok"}):
            result = await client.check_health()
            assert result == {"status": "ok", "url": "http://test.local"}

    @pytest.mark.asyncio
    async def test_check_health_error(self, client):
        """Test check_health() returns error status."""
        with patch.object(client, '_request', side_effect=HAConnectionError("http://test.local/api/health", "Failed", 1)):
            result = await client.check_health()
            assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test HAClient as context manager."""
        async with HAClient(base_url="http://test.local") as c:
            assert isinstance(c, HAClient)


class TestHAClientExceptions:
    """Tests for exception classes."""

    def test_ha_connection_error(self):
        """Test HAConnectionError message format."""
        err = HAConnectionError("http://test/api", "Failed", 3)
        assert str(err) == "Failed to connect to http://test/api after 3 retries: Failed"
        assert err.url == "http://test/api"
        assert err.last_error == "Failed"
        assert err.retries == 3

    def test_ha_timeout_error(self):
        """Test HATimeoutError message format."""
        err = HATimeoutError("http://test/api", 10.0)
        assert str(err) == "Request to http://test/api timed out after 10.0s"
        assert err.url == "http://test/api"
        assert err.timeout == 10.0
