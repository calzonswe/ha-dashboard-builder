"""Entity state change tracking."""

import asyncio
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from app.cache import EntityCache
from app.ha_client import HAClient, HAConnectionError

logger = logging.getLogger(__name__)


class StateChangeTracker:
    """Track and record state changes for entities."""

    def __init__(self, client: HAClient, cache: EntityCache) -> None:
        self.client = client
        self.cache = cache
        self._current_states: Dict[str, str] = {}
        self._listeners: List[Callable[[str, str, str], Any]] = []
        self._running = False

    async def poll_for_changes(self) -> List[Dict[str, Any]]:
        """Poll HA for current states and detect changes."""
        try:
            states_data = await self.client.get_states()
        except Exception as e:
            logger.error(f"Failed to poll states: {e}")
            return []

        changes: List[Dict[str, Any]] = []
        now = datetime.now()

        for state_item in states_data:
            entity_id = state_item["entity_id"]
            new_state = str(state_item.get("state", ""))
            old_state = self._current_states.get(entity_id)

            if old_state is not None and old_state != new_state:
                # State changed
                area_name = state_item.get("attributes", {}).get("area_name")
                changes.append({
                    "entity_id": entity_id,
                    "old_state": old_state,
                    "new_state": new_state,
                    "changed_at": now,
                    "area_name": area_name,
                })

                # Record in cache
                self.cache.record_state_change(entity_id, old_state, new_state, area_name)

                # Notify listeners
                for listener in self._listeners:
                    try:
                        listener(entity_id, old_state, new_state)
                    except Exception as e:
                        logger.error(f"Listener error for {entity_id}: {e}")

            self._current_states[entity_id] = new_state

        return changes

    async def start_polling(self, interval_seconds: float = 10.0) -> None:
        """Start continuous state polling."""
        self._running = True
        logger.info(f"Starting state polling every {interval_seconds}s")

        while self._running:
            try:
                changes = await self.poll_for_changes()
                if changes:
                    logger.info(f"Detected {len(changes)} state change(s)")
            except Exception as e:
                logger.error(f"Polling error: {e}")

            await asyncio.sleep(interval_seconds)

    def stop_polling(self) -> None:
        """Stop the polling loop."""
        self._running = False

    def add_listener(self, callback: Callable[[str, str, str], Any]) -> None:
        """Add a listener for state changes. Callback signature: (entity_id, old_state, new_state)."""
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[str, str, str], Any]) -> None:
        """Remove a state change listener."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    async def get_entity_history(
        self, entity_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get historical state changes for an entity from cache."""
        return self.cache.get_state_changes(entity_id, limit=limit)

    def get_current_state(self, entity_id: str) -> Optional[str]:
        """Get the last known state of an entity."""
        return self._current_states.get(entity_id)

    async def refresh_states(self) -> int:
        """Refresh all cached states from HA. Returns count refreshed."""
        try:
            states_data = await self.client.get_states()
        except Exception as e:
            logger.error(f"Failed to refresh states: {e}")
            return 0

        for state_item in states_data:
            entity_id = state_item["entity_id"]
            new_state = str(state_item.get("state", ""))
            old_state = self._current_states.get(entity_id)

            if old_state != new_state and old_state is not None:
                area_name = state_item.get("attributes", {}).get("area_name")
                self.cache.record_state_change(entity_id, old_state, new_state, area_name)

            self._current_states[entity_id] = new_state

        return len(states_data)

    def get_stats(self) -> Dict[str, Any]:
        """Get tracker statistics."""
        cache_stats = self.cache.get_stats()
        return {
            "tracked_entities": len(self._current_states),
            **cache_stats,
        }


# Convenience instance
tracker = StateChangeTracker(HAClient(), EntityCache())
