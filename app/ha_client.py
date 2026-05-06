"""Home Assistant API client with retry logic and timeout handling."""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import aiohttp

from app.config import settings

logger = logging.getLogger(__name__)


class HAConnectionError(Exception):
    """Raised when connection to Home Assistant fails after retries."""

    def __init__(self, url: str, last_error: str, retries: int) -> None:
        self.url = url
        self.last_error = last_error
        self.retries = retries
        super().__init__(f"Failed to connect to {url} after {retries} retries: {last_error}")


class HATimeoutError(Exception):
    """Raised when a request times out."""

    def __init__(self, url: str, timeout: float) -> None:
        self.url = url
        self.timeout = timeout
        super().__init__(f"Request to {url} timed out after {timeout}s")


class HAClient:
    """Async client for Home Assistant REST API with retry and timeout support."""

    def __init__(
        self,
        base_url: str = "http://localhost:8123",
        token: str = "",
        timeout: float = 10.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
                headers["X-HA-access"] = self.token

            connector = aiohttp.TCPConnector(verify_ssl=False)
            self._session = aiohttp.ClientSession(
                base_url=f"{self.base_url}/api/",
                headers=headers,
                connector=connector,
            )
        return self._session

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _request(
        self,
        method: str,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an HTTP request with retry and timeout logic."""
        url = f"{self.base_url}/api/{path}"

        for attempt in range(1, self.max_retries + 1):
            try:
                session = await self._get_session()
                async with session.request(method, path, json=json_data) as resp:
                    if resp.status == 401:
                        raise HAConnectionError(url, "Unauthorized", attempt)
                    elif resp.status == 403:
                        raise HAConnectionError(url, "Forbidden", attempt)
                    elif resp.status >= 500:
                        error_text = await resp.text()
                        logger.warning(
                            f"Server error {resp.status} on {url} (attempt {attempt})"
                        )
                        if attempt < self.max_retries:
                            await asyncio.sleep(self.retry_delay * attempt)
                            continue
                        raise HAConnectionError(url, error_text, attempt)

                    data = await resp.json()
                    logger.debug(f"GET {path} -> {resp.status}")
                    return data

            except (aiohttp.ClientTimeout, asyncio.TimeoutError):
                logger.warning(
                    f"Timeout on {url} (attempt {attempt}/{self.max_retries})"
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * attempt)
                    continue
                raise HATimeoutError(url, self.timeout)

            except (aiohttp.ClientConnectorError, aiohttp.ClientOSError, OSError) as e:
                logger.warning(
                    f"Connection error on {url} (attempt {attempt}): {e}"
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * attempt)
                    continue
                raise HAConnectionError(url, str(e), attempt)

            except Exception as e:
                logger.error(f"Unexpected error on {url}: {e}")
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * attempt)
                    continue
                raise HAConnectionError(url, str(e), attempt)

        # Should not reach here, but just in case
        raise HAConnectionError(url, "Max retries exceeded", self.max_retries)

    async def get_states(self) -> List[Dict[str, Any]]:
        """Fetch all entity states from Home Assistant."""
        return await self._request("GET", "states")

    async def get_state(self, entity_id: str) -> Dict[str, Any]:
        """Get the state of a single entity."""
        return await self._request("GET", f"states/{entity_id}")

    async def set_state(
        self, entity_id: str, new_state: str, attributes: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Set the state of an entity."""
        payload: Dict[str, Any] = {"state": new_state}
        if attributes:
            payload["attributes"] = attributes
        return await self._request("POST", f"states/{entity_id}", json_data=payload)

    async def call_service(
        self, domain: str, service: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Call a Home Assistant service."""
        payload: Dict[str, Any] = {"domain": domain, "service": service}
        if data:
            payload["data"] = data
        return await self._request("POST", f"services/{domain}/{service}", json_data=payload)

    async def get_entities(self) -> List[Dict[str, Any]]:
        """Get all entities with their states and areas."""
        states = await self.get_states()
        # Also fetch the entity registry for area/device info
        try:
            registry = await self._request("GET", "config/entity_registry")
        except Exception:
            registry = []

        return {"states": states, "registry": registry}

    async def check_health(self) -> Dict[str, Any]:
        """Check if Home Assistant is reachable."""
        try:
            await self._request("GET", "health")
            return {"status": "ok", "url": self.base_url}
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "error", "url": self.base_url, "error": str(e)}

    async def __aenter__(self) -> "HAClient":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()


# Convenience instance using settings
client = HAClient(
    base_url=settings.ha_url,
    token=settings.ha_token,
    timeout=settings.ha_timeout,
    max_retries=settings.ha_max_retries,
    retry_delay=settings.ha_retry_delay,
)
