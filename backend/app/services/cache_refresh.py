"""Periodic cache refresh service with configurable interval."""

import asyncio
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class CacheRefreshService:
    """Manages periodic cache refresh operations.

    Automatically refreshes entity cache at configured intervals
    to keep dashboard data up-to-date with Home Assistant state changes.
    """

    def __init__(self, discovery_service, interval_seconds: int = 60):
        self.discovery_service = discovery_service
        self.interval_seconds = interval_seconds
        self._is_running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the periodic cache refresh loop."""
        if self._is_running:
            logger.warning("Cache refresh service is already running")
            return

        self._is_running = True
        logger.info(f"Starting cache refresh service (interval: {self.interval_seconds}s)")

        # Run in background task
        self._task = asyncio.create_task(self._refresh_loop())

    async def stop(self):
        """Stop the periodic cache refresh loop."""
        if not self._is_running:
            logger.warning("Cache refresh service is not running")
            return

        self._is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        logger.info("Cache refresh service stopped")

    async def _refresh_loop(self):
        """Main loop for periodic cache refresh."""
        while self._is_running:
            try:
                logger.debug("Starting cache refresh cycle...")

                # Perform discovery and cache refresh
                summary = await asyncio.to_thread(self.discovery_service.discover)

                if summary["status"] == "success":
                    logger.info(f"Cache refreshed successfully: {summary['total_entities']} entities")
                else:
                    logger.warning(f"Cache refresh had issues: {summary.get('errors', [])}")

                # Wait for next interval
                await asyncio.sleep(self.interval_seconds)

            except asyncio.CancelledError:
                logger.info("Cache refresh loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in cache refresh loop: {e}")
                await asyncio.sleep(10)  # Shorter wait on error

    async def trigger_manual_refresh(self) -> Dict[str, Any]:
        """Trigger an immediate cache refresh.

        Returns:
            Discovery summary with status and counts
        """
        logger.info("Manual cache refresh triggered")
        return await asyncio.to_thread(self.discovery_service.discover)

    @property
    def is_running(self) -> bool:
        """Check if the service is currently running."""
        return self._is_running

    @property
    def interval_seconds(self) -> int:
        """Get the current refresh interval in seconds."""
        return self._interval_seconds

    @interval_seconds.setter
    def interval_seconds(self, value: int):
        """Set the refresh interval in seconds (minimum 10)."""
        self._interval_seconds = max(10, value)
