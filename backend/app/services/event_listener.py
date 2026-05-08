"""Async event listener that bridges HA state changes to WebSocket clients."""

import asyncio
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class HAEventListener:
    """Listen for Home Assistant entity state changes and broadcast via WebSocket.

    Polls /api/states periodically and detects differences from the previous snapshot.
    When a change is detected, broadcasts it to all connected WebSocket clients.
    """

    def __init__(self, ha_client, websocket_manager, poll_interval: float = 5.0):
        self.ha_client = ha_client
        self.websocket_manager = websocket_manager
        self.poll_interval = poll_interval
        self._running = False
        self._previous_states: Dict[str, Any] = {}
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the event listener loop."""
        if self._running:
            logger.warning("Event listener already running")
            return
        self._running = True
        # Take initial snapshot
        await self._take_snapshot()
        self._task = asyncio.create_task(self._listen_loop())
        logger.info("HA event listener started")

    async def stop(self):
        """Stop the event listener loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("HA event listener stopped")

    async def _take_snapshot(self):
        """Fetch current states and store as the previous snapshot."""
        try:
            states = await asyncio.to_thread(self.ha_client.get_states)
            for state in states:
                entity_id = state.get("entity_id", "")
                if entity_id:
                    self._previous_states[entity_id] = {
                        "state": str(state.get("state", "")),
                        "attributes": state.get("attributes", {}),
                    }
            logger.debug(f"Snapshot taken: {len(self._previous_states)} entities")
        except Exception as e:
            logger.error(f"Failed to take snapshot: {e}")

    async def _listen_loop(self):
        """Continuously poll HA states and broadcast changes."""
        while self._running:
            try:
                await self._check_for_changes()
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(f"Error in event listener loop: {e}")

            await asyncio.sleep(self.poll_interval)

    async def _check_for_changes(self):
        """Compare current states against previous snapshot and broadcast differences."""
        try:
            states = await asyncio.to_thread(self.ha_client.get_states)
        except Exception as e:
            logger.error(f"Failed to fetch states: {e}")
            return

        current_states: Dict[str, Any] = {}
        changes: list[Dict[str, Any]] = []

        for state in states:
            entity_id = state.get("entity_id", "")
            if not entity_id:
                continue

            current_state_val = str(state.get("state", ""))
            attributes = state.get("attributes", {})

            previous = self._previous_states.get(entity_id, {})
            prev_state = previous.get("state", "")

            # Detect changes: state changed OR new entity appeared
            if (
                current_state_val != prev_state
                or entity_id not in self._previous_states
            ):
                changes.append(
                    {
                        "entity_id": entity_id,
                        "state": current_state_val,
                        "attributes": attributes,
                        "last_changed": state.get("last_changed"),
                    }
                )

            current_states[entity_id] = {
                "state": current_state_val,
                "attributes": attributes,
            }

        # Update snapshot
        self._previous_states = current_states

        if changes:
            logger.info(f"Detected {len(changes)} entity change(s)")
            await self.websocket_manager.broadcast_changes(changes)
