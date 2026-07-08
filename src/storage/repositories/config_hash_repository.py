"""Repository for managing config hashes and their lifecycle.

Tracks configuration hashes with scoring and TTL-based cleanup to avoid redundant experiments.
"""

from datetime import UTC, datetime, timedelta

import aiosqlite

from src.storage.repositories._shared import db_or_connect


class ConfigHashRepository:
    """DAO for config_hashes table — tracks seen configurations and their scores."""

    def __init__(self, db: aiosqlite.Connection | None = None):
        """Initialize with optional connection; if None, creates connections on-demand."""
        self._db = db

    async def insert(self, config_hash: str, first_seen: str | None = None):
        """Insert a new config hash with optional first_seen timestamp (defaults to now)."""
        first_seen = first_seen or datetime.now(UTC).isoformat()
        async with db_or_connect(self._db) as db:
            await db.execute(
                """
                INSERT INTO config_hashes (config_hash, first_seen, score)
                VALUES (?, ?, NULL)
                """,
                (config_hash, first_seen),
            )

    async def update_score(self, config_hash: str, score: float):
        """Update score to the max of current and new value (prevents score decrease)."""
        async with db_or_connect(self._db) as db:
            await db.execute(
                """
                UPDATE config_hashes
                SET score = MAX(COALESCE(score, 0.0), ?)
                WHERE config_hash = ?
                """,
                (score, config_hash),
            )

    async def find_all_used(self) -> set[str]:
        """Return set of all tracked config hashes."""
        async with db_or_connect(self._db) as db:
            cursor = await db.execute("SELECT config_hash FROM config_hashes")
            return {row[0] for row in await cursor.fetchall()}

    async def delete_stale(
        self, ttl_days: int = 7, exclude_statuses: tuple[str, ...] | None = None
    ) -> int:
        """Delete config hashes older than ttl_days with no score, unless referenced by active experiments."""
        exclude = exclude_statuses or ("FAILED_VALIDATION",)
        placeholders = ", ".join("?" for _ in exclude)
        cutoff = (datetime.now(UTC) - timedelta(days=ttl_days)).isoformat()
        async with db_or_connect(self._db) as db:
            result = await db.execute(
                f"""
                DELETE FROM config_hashes
                WHERE first_seen < ?
                  AND score IS NULL
                  AND config_hash NOT IN (
                      SELECT config_hash FROM experiments
                      WHERE status NOT IN ({placeholders})
                  )
                """,
                (cutoff, *exclude),
            )
            return result.rowcount or 0
