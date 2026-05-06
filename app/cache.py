"""Entity cache with SQLite persistence."""

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class EntityCache:
    """SQLite-backed entity state cache with TTL expiration."""

    def __init__(self, db_path: str = "cache.db", ttl_seconds: int = 60) -> None:
        self.db_path = db_path
        self.ttl = timedelta(seconds=ttl_seconds)
        self._conn: Optional[sqlite3.Connection] = None
        
        # For in-memory DBs, create connection once and reuse it
        if db_path == ":memory:":
            self._ensure_db()
        else:
            self._ensure_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Get a database connection. Reuses existing connection for in-memory DBs."""
        # For in-memory databases, reuse the same connection
        if self.db_path == ":memory:" and self._conn is not None:
            return self._conn
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        # Store for in-memory DBs to reuse across calls
        if self.db_path == ":memory:":
            self._conn = conn
        
        return conn

    def _ensure_db(self) -> None:
        """Create cache tables if they don't exist."""
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS entity_cache (
                    entity_id TEXT PRIMARY KEY,
                    state TEXT NOT NULL,
                    attributes TEXT DEFAULT '{}',
                    last_changed TEXT NOT NULL,
                    last_updated TEXT NOT NULL,
                    cached_at TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    area_name TEXT DEFAULT ''
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS state_changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_id TEXT NOT NULL,
                    old_state TEXT NOT NULL,
                    new_state TEXT NOT NULL,
                    changed_at TEXT NOT NULL,
                    area_name TEXT DEFAULT ''
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_entity_cache_domain 
                ON entity_cache(domain)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_state_changes_entity 
                ON state_changes(entity_id, changed_at DESC)
            """)
            conn.commit()

    def get(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get a cached entity if not expired."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM entity_cache WHERE entity_id = ?", (entity_id,)
            ).fetchone()

        if row is None:
            return None

        # Check TTL
        cached_at = datetime.fromisoformat(row["cached_at"])
        if datetime.now() - cached_at > self.ttl:
            self.delete(entity_id)
            return None

        return {
            "entity_id": row["entity_id"],
            "state": row["state"],
            "attributes": json.loads(row["attributes"]),
            "last_changed": datetime.fromisoformat(row["last_changed"]),
            "last_updated": datetime.fromisoformat(row["last_updated"]),
            "domain": row["domain"],
            "area_name": row["area_name"] if row["area_name"] else None,
        }

    def set(self, entity_id: str, state_data: Dict[str, Any]) -> None:
        """Cache an entity state."""
        now = datetime.now()
        attributes_json = json.dumps(state_data.get("attributes", {}))

        with self._get_conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO entity_cache 
                   (entity_id, state, attributes, last_changed, last_updated, cached_at, domain, area_name)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    entity_id,
                    str(state_data.get("state", "")),
                    attributes_json,
                    now.isoformat(),
                    now.isoformat(),
                    now.isoformat(),
                    state_data.get("domain", "unknown"),
                    state_data.get("area_name", ""),
                ),
            )
            conn.commit()

    def set_many(self, entities: List[Dict[str, Any]]) -> int:
        """Batch insert/update multiple entities. Returns count."""
        now = datetime.now()
        values = []
        for entity in entities:
            attributes_json = json.dumps(entity.get("attributes", {}))
            values.append(
                (
                    entity["entity_id"],
                    str(entity.get("state", "")),
                    attributes_json,
                    now.isoformat(),
                    now.isoformat(),
                    now.isoformat(),
                    entity.get("domain", "unknown"),
                    entity.get("area_name", ""),
                )
            )

        with self._get_conn() as conn:
            conn.executemany(
                """INSERT OR REPLACE INTO entity_cache 
                   (entity_id, state, attributes, last_changed, last_updated, cached_at, domain, area_name)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                values,
            )
            conn.commit()

        return len(entities)

    def delete(self, entity_id: str) -> None:
        """Remove an entity from cache."""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM entity_cache WHERE entity_id = ?", (entity_id,))
            conn.commit()

    def clear(self) -> None:
        """Clear all cached entities."""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM entity_cache")
            conn.commit()

    def get_expired(self) -> List[str]:
        """Get list of expired entity IDs."""
        cutoff = (datetime.now() - self.ttl).isoformat()
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT entity_id FROM entity_cache WHERE cached_at < ?", (cutoff,)
            ).fetchall()
        return [row["entity_id"] for row in rows]

    def cleanup_expired(self) -> int:
        """Remove expired entries. Returns count removed."""
        cutoff = (datetime.now() - self.ttl).isoformat()
        with self._get_conn() as conn:
            cursor = conn.execute(
                "DELETE FROM entity_cache WHERE cached_at < ?", (cutoff,)
            )
            conn.commit()
        return cursor.rowcount

    def get_state_changes(self, entity_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent state changes for an entity."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM state_changes WHERE entity_id = ? ORDER BY changed_at DESC LIMIT ?",
                (entity_id, limit),
            ).fetchall()

        return [
            {
                "entity_id": row["entity_id"],
                "old_state": row["old_state"],
                "new_state": row["new_state"],
                "changed_at": datetime.fromisoformat(row["changed_at"]),
                "area_name": row["area_name"] if row["area_name"] else None,
            }
            for row in rows
        ]

    def record_state_change(
        self, entity_id: str, old_state: str, new_state: str, area_name: Optional[str] = None
    ) -> None:
        """Record a state change event."""
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO state_changes (entity_id, old_state, new_state, changed_at, area_name) VALUES (?, ?, ?, ?, ?)",
                (entity_id, old_state, new_state, datetime.now().isoformat(), area_name or ""),
            )
            conn.commit()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._get_conn() as conn:
            count = conn.execute("SELECT COUNT(*) FROM entity_cache").fetchone()[0]
            changes = conn.execute(
                "SELECT COUNT(*) FROM state_changes"
            ).fetchone()[0]

        return {"cached_entities": count, "state_changes_recorded": changes}


# Default cache instance
cache = EntityCache()
