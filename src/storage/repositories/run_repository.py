"""Repository for managing experiment runs.

Simple accessor for the most recent run from the database.
"""

import aiosqlite

from src.storage.models import Run
from src.storage.repositories._shared import db_or_connect


class RunRepository:
    """DAO for runs table — minimal interface for run metadata."""

    def __init__(self, db: aiosqlite.Connection | None = None):
        """Initialize with optional connection; if None, creates connections on-demand."""
        self._db = db

    async def create_run(self, run_id: str, started_at: str) -> None:
        """Insert a new run row. Idempotent: a resumed run reuses the same
        run_id, so a second call for the same run must not crash or
        duplicate the row."""
        async with db_or_connect(self._db) as db:
            await db.execute(
                "INSERT OR IGNORE INTO runs (run_id, started_at) VALUES (?, ?)",
                (run_id, started_at),
            )

    async def finish_run(
        self,
        run_id: str,
        finished_at: str,
        total_cost: float,
        n_experiments: int,
        n_accepted: int,
        best_config: str | None,
        best_score: float | None,
        status: str,
    ) -> None:
        """Update a run row's terminal fields once the run has stopped."""
        async with db_or_connect(self._db) as db:
            await db.execute(
                """
                UPDATE runs
                SET finished_at = ?, total_cost = ?, n_experiments = ?,
                    n_accepted = ?, best_config = ?, best_score = ?, status = ?
                WHERE run_id = ?
                """,
                (
                    finished_at,
                    total_cost,
                    n_experiments,
                    n_accepted,
                    best_config,
                    best_score,
                    status,
                    run_id,
                ),
            )

    async def find_last_run_id(self) -> str | None:
        """Return the most recent run_id, or None if no runs exist."""
        async with db_or_connect(self._db) as db:
            cursor = await db.execute("SELECT run_id FROM runs ORDER BY started_at DESC LIMIT 1")
            row = await cursor.fetchone()
            return row[0] if row else None

    async def list_runs(self, limit: int = 50, offset: int = 0) -> list[Run]:
        """Return runs newest-first, for the web dashboard's history view."""
        async with db_or_connect(self._db) as db:
            cursor = await db.execute(
                """
                SELECT run_id, started_at, finished_at, total_cost, n_experiments,
                       n_accepted, best_config, best_score, status
                FROM runs
                ORDER BY started_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )
            rows = await cursor.fetchall()
            return [
                Run(
                    run_id=row[0],
                    started_at=row[1],
                    finished_at=row[2],
                    total_cost=row[3],
                    n_experiments=row[4],
                    n_accepted=row[5],
                    best_config=row[6],
                    best_score=row[7],
                    status=row[8],
                )
                for row in rows
            ]
