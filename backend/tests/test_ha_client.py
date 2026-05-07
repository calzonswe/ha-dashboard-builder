"""Tests for Home Assistant API Client."""

import pytest
from unittest.mock import patch, MagicMock
from app.services.ha_client import (
    HAAPI,
    HAConnectionError,
    HAAPIError,
)


class TestHAAPI:
    """Test suite for the HAAPI class."""

    @pytest.fixture
    def api(self):
        """Create a test HAAPI instance."""
        return HAAPI(host="192.168.1.50", port=8123, token="test_token_abc123")

    def test_init(self, api):
        """Test initialization with valid parameters."""
        assert api.host == "192.168.1.50"
        assert api.port == 8123
        assert api.token == "test_token_abc123"
        assert api.base_url == "https://192.168.1.50:8123/api/"

    def test_init_http(self):
        """Test initialization with HTTP (no SSL)."""
        api = HAAPI(host="localhost", port=8123, token="token", ssl=False)
        assert api.base_url == "http://localhost:8123/api/"

    @patch("app.services.ha_client.time.sleep")
    def test_test_connection_success(self, mock_sleep, api):
        """Test successful connection test."""
        # Use status 200 with actual state data (not 204 which means empty)
        expected_data = [
            {"entity_id": "sensor.temp", "state": "22.5"},
            {"entity_id": "light.lamp", "state": "on"},
        ]

        with patch("httpx.Client") as MockClient:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = expected_data

            mock_client_instance = MagicMock()
            mock_client_instance.request.return_value = mock_response

            # Setup context manager properly
            MockClient.return_value.__enter__ = MagicMock(
                return_value=mock_client_instance
            )
            MockClient.return_value.__exit__ = MagicMock(return_value=False)

            result = api.test_connection()
            assert result["host"] == "192.168.1.50"
            assert result["port"] == 8123

    @patch("app.services.ha_client.time.sleep")
    def test_test_connection_failure(self, mock_sleep, api):
        """Test connection failure."""
        import httpx

        with patch("httpx.Client") as MockClient:
            mock_client_instance = MagicMock()
            mock_client_instance.request.side_effect = httpx.ConnectError(
                "Connection refused"
            )

            MockClient.return_value.__enter__ = MagicMock(
                return_value=mock_client_instance
            )
            MockClient.return_value.__exit__ = MagicMock(return_value=False)

            with pytest.raises(HAConnectionError):
                api.test_connection()

    @patch("app.services.ha_client.time.sleep")
    def test_get_states(self, mock_sleep, api):
        """Test fetching entity states."""
        expected_data = [
            {"entity_id": "sensor.temp", "state": "22.5"},
            {"entity_id": "light.lamp", "state": "on"},
        ]

        with patch("httpx.Client") as MockClient:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = expected_data

            mock_client_instance = MagicMock()
            mock_client_instance.request.return_value = mock_response

            # Setup context manager properly
            MockClient.return_value.__enter__ = MagicMock(
                return_value=mock_client_instance
            )
            MockClient.return_value.__exit__ = MagicMock(return_value=False)

            result = api.get_states()
            assert len(result) == 2
            assert result[0]["entity_id"] == "sensor.temp"

    @patch("app.services.ha_client.time.sleep")
    def test_get_state(self, mock_sleep, api):
        """Test fetching a single entity state."""
        expected_data = {
            "entity_id": "sensor.temperature",
            "state": "22.5",
            "attributes": {"friendly_name": "Living Room Temp"},
        }

        with patch("httpx.Client") as MockClient:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = expected_data

            mock_client_instance = MagicMock()
            mock_client_instance.request.return_value = mock_response

            # Setup context manager properly
            MockClient.return_value.__enter__ = MagicMock(
                return_value=mock_client_instance
            )
            MockClient.return_value.__exit__ = MagicMock(return_value=False)

            result = api.get_state("sensor.temperature")
            assert result["entity_id"] == "sensor.temperature"
            assert result["state"] == "22.5"

    @patch("app.services.ha_client.time.sleep")
    def test_call_service(self, mock_sleep, api):
        """Test calling a Home Assistant service."""
        expected_data = {"message": "Service called successfully"}

        with patch("httpx.Client") as MockClient:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = expected_data

            mock_client_instance = MagicMock()
            mock_client_instance.request.return_value = mock_response

            # Setup context manager properly
            MockClient.return_value.__enter__ = MagicMock(
                return_value=mock_client_instance
            )
            MockClient.return_value.__exit__ = MagicMock(return_value=False)

            result = api.call_service("light", "turn_on", {"entity_id": "light.lamp"})
            assert result["message"] == "Service called successfully"


class TestHAExceptions:
    """Test suite for HA exception classes."""

    def test_ha_connection_error(self):
        """Test HAConnectionError creation."""
        error = HAConnectionError("Cannot connect to host")
        assert str(error) == "Cannot connect to host"

    def test_ha_api_error(self):
        """Test HAAPIError creation."""
        error = HAAPIError(401, "Unauthorized")
        assert error.status_code == 401
        assert error.message == "Unauthorized"
        assert "401" in str(error)
