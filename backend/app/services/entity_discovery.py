"""Entity Discovery & Caching Module with SQLite persistence."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import sqlite3
import json as json_module

logger = logging.getLogger(__name__)


class EntityCache:
    """SQLite-backed cache for HA entities with state change tracking.

    Persists entity states to SQLite so they survive restarts and can be
    queried without hitting the HA API every time.
    """

    def __init__(self, db_path: str = "./ha_entities.db"):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._ensure_schema()

    def _get_conn(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _ensure_schema(self):
        """Create tables if they don't exist."""
        conn = self._get_conn()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS entities (
                entity_id TEXT PRIMARY KEY,
                name TEXT DEFAULT '',
                domain TEXT DEFAULT '',
                entity_type TEXT DEFAULT '',
                state TEXT DEFAULT '',
                attributes_json TEXT DEFAULT '{}',
                unit_of_measurement TEXT DEFAULT '',
                device_id TEXT DEFAULT '',
                area TEXT DEFAULT '',
                last_changed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS state_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id TEXT NOT NULL,
                old_state TEXT DEFAULT '',
                new_state TEXT NOT NULL,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entity_id) REFERENCES entities(entity_id)
            )
        """
        )
        conn.commit()

    def get_all_entities(self) -> List[Dict[str, Any]]:
        """Return all cached entities from SQLite."""
        conn = self._get_conn()
        cursor = conn.execute("SELECT * FROM entities ORDER BY entity_id")
        return [dict(row) for row in cursor.fetchall()]

    def get_by_domain(self, domain: str) -> List[Dict[str, Any]]:
        """Get entities filtered by domain."""
        conn = self._get_conn()
        cursor = conn.execute("SELECT * FROM entities WHERE domain = ? ORDER BY entity_id", (domain,))
        return [dict(row) for row in cursor.fetchall()]

    def get_by_area(self, area: str) -> List[Dict[str, Any]]:
        """Get entities filtered by area/room name."""
        conn = self._get_conn()
        cursor = conn.execute("SELECT * FROM entities WHERE area = ? ORDER BY entity_id", (area,))
        return [dict(row) for row in cursor.fetchall()]

    def get_by_device(self, device_id: str) -> List[Dict[str, Any]]:
        """Get entities filtered by device ID."""
        conn = self._get_conn()
        cursor = conn.execute("SELECT * FROM entities WHERE device_id = ? ORDER BY entity_id", (device_id,))
        return [dict(row) for row in cursor.fetchall()]

    def get_by_entity_type(self, entity_type: str) -> List[Dict[str, Any]]:
        """Get entities filtered by entity type."""
        conn = self._get_conn()
        cursor = conn.execute("SELECT * FROM entities WHERE entity_type = ? ORDER BY entity_id", (entity_type,))
        return [dict(row) for row in cursor.fetchall()]

    def get_by_state(self, state: str) -> List[Dict[str, Any]]:
        """Get entities matching a specific current state."""
        conn = self._get_conn()
        cursor = conn.execute("SELECT * FROM entities WHERE state = ? ORDER BY entity_id", (state,))
        return [dict(row) for row in cursor.fetchall()]

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search entities by name or ID substring (case-insensitive)."""
        conn = self._get_conn()
        pattern = f"%{query}%"
        cursor = conn.execute("SELECT * FROM entities WHERE name LIKE ? OR entity_id LIKE ?", (pattern, pattern))
        results = [dict(row) for row in cursor.fetchall()]
        logger.info(f"Search '{query}' returned {len(results)} entities")
        return results

    def refresh(self, states: List[Dict[str, Any]]) -> int:
        """Refresh the cache from fresh HA state data.

        Inserts or updates each entity and tracks state changes.
        Returns the number of entities cached/updated.
        """
        conn = self._get_conn()
        count = 0

        for state in states:
            entity_id = state.get("entity_id", "")
            if not entity_id:
                continue

            parts = entity_id.split(".")
            domain = parts[0] if len(parts) >= 1 else ""
            entity_type = parts[1] if len(parts) >= 2 else ""

            # Get current state for change detection
            cursor = conn.execute("SELECT state FROM entities WHERE entity_id = ?", (entity_id,))
            existing = cursor.fetchone()
            old_state = existing["state"] if existing else None

            new_state = str(state.get("state", ""))

            # Insert or update entity
            # Support both raw HA states (attributes.friendly_name) and enriched dicts (top-level name)
            if "name" in state:
                name = state.get("name", entity_id)
            else:
                name = state.get("attributes", {}).get("friendly_name", entity_id)

            conn.execute(
                """
                INSERT OR REPLACE INTO entities
                (entity_id, name, domain, entity_type, state, attributes_json,
                 unit_of_measurement, device_id, area, last_changed, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    entity_id,
                    name,
                    domain,
                    entity_type,
                    new_state,
                    json_module.dumps(state.get("attributes", {})),
                    state.get("unit_of_measurement"),
                    state.get("device_id"),
                    state.get("area"),
                    str(state.get("last_changed", "")),
                    datetime.now().isoformat(),
                ),
            )

            # Track state changes
            if old_state is not None and old_state != new_state:
                conn.execute(
                    """
                    INSERT INTO state_history
                    (entity_id, old_state, new_state, changed_at)
                    VALUES (?, ?, ?, ?)
                """,
                    (entity_id, old_state, new_state, datetime.now().isoformat()),
                )

            count += 1

        conn.commit()
        logger.info(f"Entity cache refreshed: {count} entities")
        return count

    def get_state_history(self, entity_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get state change history for an entity."""
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT * FROM state_history WHERE entity_id = ? ORDER BY id DESC LIMIT ?", (entity_id, limit)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_state_changes_count(self) -> int:
        """Get total number of state changes tracked."""
        conn = self._get_conn()
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM state_history")
        return cursor.fetchone()["cnt"]

    def clear(self):
        """Clear all cached data from SQLite."""
        conn = self._get_conn()
        conn.execute("DELETE FROM entities")
        conn.execute("DELETE FROM state_history")
        conn.commit()
        logger.info("Entity cache cleared")

    def get_entities_by_group(self, group_type: str = "area") -> Dict[str, List[Dict[str, Any]]]:
        """Group entities by area or device.

        Args:
            group_type: 'area' to group by area, 'device' to group by device

        Returns:
            Dictionary mapping group key to list of entities
        """
        all_entities = self.get_all_entities()

        if group_type == "area":
            groups = {}
            for entity in all_entities:
                area = entity.get("area") or "unassigned"
                if area not in groups:
                    groups[area] = []
                groups[area].append(entity)
            return groups

        elif group_type == "device":
            groups = {}
            for entity in all_entities:
                device_id = entity.get("device_id") or "unassigned"
                if device_id not in groups:
                    groups[device_id] = []
                groups[device_id].append(entity)
            return groups

        else:
            raise ValueError(f"Unknown group_type: {group_type}")


class EntityDiscoveryService:
    """Orchestrates entity discovery from HA and caching.

    Connects to Home Assistant, fetches all states, enriches them with
    metadata (areas, devices), and stores the result in SQLite for
    fast dashboard lookups.

    Handles partial failures gracefully - if device/area enrichment fails,
    discovery still completes with available data.
    """

    def __init__(self, ha_client, entity_cache: Optional[EntityCache] = None):
        self.ha_client = ha_client
        self.cache = entity_cache or EntityCache()

    def discover(self) -> Dict[str, Any]:
        """Full discovery cycle: connect → fetch states → enrich → cache.

        Returns a summary dict with counts and status.
        Handles partial failures gracefully.
        """
        logger.info("Starting entity discovery...")
        errors = []

        # 1. Test connection
        try:
            conn_info = self.ha_client.test_connection()
            logger.info(f"HA Connection OK: {conn_info}")
        except Exception as exc:
            error_msg = f"Connection failed: {exc}"
            logger.error(error_msg)
            errors.append(error_msg)

        # 2. Fetch all states
        try:
            states = self.ha_client.get_states()
            if not isinstance(states, list):
                raise HAConnectionError("Failed to fetch entity states")
            logger.info(f"Fetched {len(states)} entity states")
        except Exception as exc:
            error_msg = f"State fetch failed: {exc}"
            logger.error(error_msg)
            errors.append(error_msg)
            # If we can't get states, we can't continue
            return {"status": "partial", "errors": errors}

        # 3. Enrich with device/area metadata (optional - won't fail discovery)
        enriched = self._enrich_states(states)

        # 4. Cache the result
        try:
            count = self.cache.refresh(enriched)
            logger.info(f"Cached {count} entities")
        except Exception as exc:
            error_msg = f"Cache refresh failed: {exc}"
            logger.error(error_msg)
            errors.append(error_msg)

        # 5. Build summary
        domains = set(e["domain"] for e in enriched) if enriched else set()
        areas = set(e.get("area") or "" for e in enriched if e.get("area")) if enriched else set()

        status = "partial" if errors else "success"

        summary = {
            "status": status,
            "total_entities": len(enriched) if enriched else 0,
            "domains": sorted(domains),
            "areas": sorted(areas),
            "cached_at": datetime.now().isoformat(),
            "errors": errors,
        }

        logger.info(f"Discovery complete: {summary}")
        return summary

    def _enrich_states(self, states: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add device and area metadata to each state.

        Handles failures gracefully - if device fetch fails, returns states as-is.
        """
        devices = []
        try:
            devices = self.ha_client.get_devices() or []
            logger.info(f"Fetched {len(devices)} devices for enrichment")
        except Exception as exc:
            logger.warning(f"Could not fetch devices (continuing without device metadata): {exc}")

        # Build a lookup: device_id → area_name
        device_areas: Dict[str, str] = {}
        for dev in devices:
            did = dev.get("id") or dev.get("device_id", "")
            if did and dev.get("area_id"):
                device_areas[did] = dev["area_id"]

        enriched = []
        for state in states:
            entity_id = state.get("entity_id", "")
            if not entity_id:
                continue

            parts = entity_id.split(".")
            domain = parts[0] if len(parts) >= 1 else ""
            entity_type = parts[1] if len(parts) >= 2 else ""

            device_id = state.get("device_id") or ""
            area_name = device_areas.get(device_id, "")

            enriched.append(
                {
                    "entity_id": entity_id,
                    "domain": domain,
                    "entity_type": entity_type,
                    "name": state.get("attributes", {}).get("friendly_name", entity_id),
                    "state": str(state.get("state", "")),
                    "unit_of_measurement": state.get("attributes", {}).get("unit_of_measure"),
                    "device_id": device_id,
                    "area": area_name,
                    "last_changed": state.get("last_changed_iso") or str(state.get("last_changed", "")),
                }
            )

        return enriched

    def get_cached_entities(self) -> List[Dict[str, Any]]:
        """Return currently cached entities."""
        return self.cache.get_all_entities()

    def search_entities(self, query: str) -> List[Dict[str, Any]]:
        """Search cached entities by name or ID."""
        return self.cache.search(query)


class HAConnectionError(Exception):
    """Raised when connection to Home Assistant fails."""

    pass


class HAAPIError(Exception):
    """Raised when the Home Assistant API returns an error."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"HA API Error {status_code}: {message}")
