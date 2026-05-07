"""Home Assistant API Client Module with retry logic."""

import logging
from typing import Optional, Dict, Any, List
import time
import httpx

logger = logging.getLogger(__name__)


class HAConnectionError(Exception):
    """Raised when connection to Home Assistant fails."""

    pass


class HAAPIError(Exception):
    """Raised when the Home Assistant API returns an error."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"HA API Error {status_code}: {message}")


class HAStateError(Exception):
    """Raised when the Home Assistant instance is not in a usable state."""

    pass


class HAAPI:
    """Async-compatible Home Assistant REST API client with retry logic.

    Uses httpx for HTTP requests to the HA REST API.
    Supports both sync and async patterns via standard httpx Client/AsyncClient.

    Features:
    - Automatic retries on connection failures (configurable)
    - Timeout handling for slow responses
    - Graceful error handling with detailed messages
    """

    def __init__(self, host: str, token: str, port: int = 8123, ssl: bool = True):
        self.host = host.rstrip("/")
        self.port = port
        self.token = token
        self.ssl = ssl
        self.base_url = f"{'https' if ssl else 'http'}://{self.host}:{port}/api/"

        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
        self.timeout = 10.0  # seconds

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def _request_with_retry(self, method: str, endpoint: str, **kwargs) -> Any:
        """Make an HTTP request with automatic retry on failure."""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()

        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"Request {method} {url} (attempt {attempt}/{self.max_retries})")

                with httpx.Client(timeout=self.timeout) as client:
                    response = client.request(method, url, headers=headers, **kwargs)

                    # Check for HTTP errors
                    if response.status_code >= 400:
                        error_msg = f"HTTP {response.status_code}: {response.reason_phrase}"
                        logger.warning(f"{error_msg} on attempt {attempt}")

                        # Don't retry client errors (4xx) except 429 (rate limit)
                        if response.status_code < 500 and response.status_code != 429:
                            raise HAAPIError(response.status_code, error_msg)

                    response.raise_for_status()

                    # Return parsed JSON for non-204 responses, None for empty responses
                    if response.status_code == 204:
                        return None
                    return response.json()

            except httpx.HTTPStatusError as exc:
                last_error = exc
                logger.warning(f"HTTP status error on attempt {attempt}: {exc}")

                # Don't retry client errors (4xx) except 429
                if exc.response.status_code < 500 and exc.response.status_code != 429:
                    raise HAAPIError(exc.response.status_code, str(exc)) from exc

            except httpx.ConnectError as exc:
                last_error = exc
                logger.warning(f"Connection error on attempt {attempt}: {exc}")

            except httpx.ReadTimeout as exc:
                last_error = exc
                logger.warning(f"Read timeout on attempt {attempt}: {exc}")

            except Exception as exc:
                last_error = exc
                logger.error(f"Unexpected error on attempt {attempt}: {exc}")

            # Wait before retrying (exponential backoff)
            if attempt < self.max_retries:
                delay = self.retry_delay * (2 ** (attempt - 1))
                logger.info(f"Retrying in {delay:.1f} seconds...")
                time.sleep(delay)

        # All retries exhausted
        error_msg = f"All {self.max_retries} attempts failed. Last error: {last_error}"
        raise HAConnectionError(error_msg) from last_error if last_error else None

    def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Make an HTTP request to the HA REST API (uses retry logic)."""
        return self._request_with_retry(method, endpoint, **kwargs)

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def test_connection(self) -> Dict[str, Any]:
        """Test the connection and return basic info about the HA instance."""
        data = self._request("GET", "states")
        if data is None:
            raise HAConnectionError("Empty response from /api/states")
        # Count entities to verify we got real data
        entity_count = len(data) if isinstance(data, list) else 0
        logger.info(f"Connected to Home Assistant at {self.host}:{self.port} " f"({entity_count} entities found)")
        return {"host": self.host, "port": self.port, "entities": entity_count}

    def get_states(self) -> List[Dict[str, Any]]:
        """Fetch all entity states from Home Assistant."""
        return self._request("GET", "states") or []

    def get_state(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get the current state of a single entity."""
        data = self._request("GET", f"states/{entity_id}")
        if isinstance(data, dict):
            return data
        return None

    def get_services(self) -> List[Dict[str, Any]]:
        """Fetch all registered services (domains + services)."""
        data = self._request("GET", "services")
        if isinstance(data, list):
            return data
        return []

    def call_service(
        self,
        domain: str,
        service: str,
        service_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Call a Home Assistant service."""
        payload = {"domain": domain, "service": service}
        if service_data:
            payload["service_data"] = {**service_data}
        return self._request("POST", f"services/{domain}/{service}", json=payload)

    def get_config(self) -> Dict[str, Any]:
        """Fetch the Home Assistant configuration."""
        data = self._request("GET", "config")
        if isinstance(data, dict):
            return data
        raise HAAPIError(500, "Could not retrieve HA config")

    def get_areas(self) -> List[Dict[str, Any]]:
        """Fetch all areas (rooms/zones)."""
        data = self._request("GET", "config/areas")
        if isinstance(data, list):
            return data
        return []

    def get_devices(self) -> List[Dict[str, Any]]:
        """Fetch all registered devices."""
        data = self._request("GET", "config/devices")
        if isinstance(data, list):
            return data
        return []

    def get_entities_for_device(self, device_id: str) -> List[Dict[str, Any]]:
        """Fetch entities belonging to a specific device."""
        states = self.get_states()
        return [s for s in states if s.get("device_id") == device_id]
