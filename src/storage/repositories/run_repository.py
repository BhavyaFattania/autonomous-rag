from typing import Optional

import aiosqlite

from src.storage.repositories._shared import db_or_connect


class RunRepository:
    def __init__(self, db: Optional[aiosqlite.Connection] = None):
        self._db = db

    async def find_last_run_id(self) -> Optional[str]:
        async with db_or_connect(self._db) as db:
            cursor = await db.execute(
                "SELECT run_id FROM runs ORDER BY started_at DESC LIMIT 1"
            )
            row = await cursor.fetchone()
            return row[0] if row else None
