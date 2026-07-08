"""Repository for managing experiment runs.

Simple accessor for the most recent run from the database.
"""

import aiosqlite

from src.storage.repositories._shared import db_or_connect


class RunRepository:
    """DAO for runs table — minimal interface for run metadata."""

    def __init__(self, db: aiosqlite.Connection | None = None):
        """Initialize with optional connection; if None, creates connections on-demand."""
        self._db = db

    async def find_last_run_id(self) -> str | None:
        """Return the most recent run_id, or None if no runs exist."""
        async with db_or_connect(self._db) as db:
            cursor = await db.execute("SELECT run_id FROM runs ORDER BY started_at DESC LIMIT 1")
            row = await cursor.fetchone()
            return row[0] if row else None
