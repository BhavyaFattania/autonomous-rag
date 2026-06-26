from typing import Optional
from datetime import datetime, timezone, timedelta

import aiosqlite

from src.storage.database import Database
from src.storage.repositories.experiment_repository import _db_or_connect


class ConfigHashRepository:
    def __init__(self, db: Optional[aiosqlite.Connection] = None):
        self._db = db

    async def insert(self, config_hash: str, first_seen: Optional[str] = None):
        first_seen = first_seen or datetime.now(timezone.utc).isoformat()
        async with _db_or_connect(self._db) as db:
            await db.execute(
                """
                INSERT INTO config_hashes (config_hash, first_seen, score)
                VALUES (?, ?, NULL)
                """,
                (config_hash, first_seen),
            )

    async def update_score(self, config_hash: str, score: float):
        async with _db_or_connect(self._db) as db:
            await db.execute(
                """
                UPDATE config_hashes
                SET score = MAX(COALESCE(score, 0.0), ?)
                WHERE config_hash = ?
                """,
                (score, config_hash),
            )

    async def find_all_used(self) -> set[str]:
        async with _db_or_connect(self._db) as db:
            cursor = await db.execute("SELECT config_hash FROM config_hashes")
            return {row[0] for row in await cursor.fetchall()}

    async def delete_stale(
        self, ttl_days: int = 7, exclude_statuses: Optional[tuple[str, ...]] = None
    ) -> int:
        exclude = exclude_statuses or ("FAILED_VALIDATION",)
        placeholders = ", ".join("?" for _ in exclude)
        cutoff = (datetime.now(timezone.utc) - timedelta(days=ttl_days)).isoformat()
        async with _db_or_connect(self._db) as db:
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
