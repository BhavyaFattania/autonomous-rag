import json

import aiosqlite

from src.storage.models import Experiment, HistoricalRecord
from src.storage.repositories._shared import db_or_connect
from src.utils.function_trace import trace_call


class ExperimentRepository:
    def __init__(self, db: aiosqlite.Connection | None = None):
        self._db = db

    async def insert(self, experiment: Experiment) -> int:
        async with db_or_connect(self._db) as db:
            cursor = await db.execute(
                """
                INSERT INTO experiments
                (experiment_uuid, run_id, config_hash, config_json, hypothesis, status, failure_reason,
                 metrics_json, baseline_score, proposed_score, cost_usd, started_at, finished_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    experiment.experiment_uuid,
                    experiment.run_id,
                    experiment.config_hash,
                    experiment.config_json,
                    experiment.hypothesis,
                    experiment.status,
                    experiment.failure_reason,
                    experiment.metrics_json,
                    experiment.baseline_score,
                    experiment.proposed_score,
                    experiment.cost_usd,
                    experiment.started_at,
                    experiment.finished_at,
                ),
            )
            return cursor.lastrowid

    async def find_by_config_hash(
        self, config_hash: str, exclude_statuses: tuple[str, ...] | None = None
    ) -> int | None:
        exclude = exclude_statuses or ("FAILED_VALIDATION",)
        placeholders = ", ".join("?" for _ in exclude)
        async with db_or_connect(self._db) as db:
            cursor = await db.execute(
                f"""
                SELECT experiment_id FROM experiments
                WHERE config_hash = ?
                  AND status NOT IN ({placeholders})
                LIMIT 1
                """,
                (config_hash, *exclude),
            )
            row = await cursor.fetchone()
            return row[0] if row else None

    async def find_best_historical(
        self, config_hash: str, exclude_statuses: tuple[str, ...] | None = None
    ) -> HistoricalRecord:
        exclude = exclude_statuses or ("FAILED_VALIDATION",)
        placeholders = ", ".join("?" for _ in exclude)
        async with db_or_connect(self._db) as db:
            cursor = await db.execute(
                f"""
                SELECT proposed_score, metrics_json, status, hypothesis
                FROM experiments
                WHERE config_hash = ?
                  AND status NOT IN ({placeholders})
                ORDER BY proposed_score DESC NULLS LAST
                LIMIT 1
                """,
                (config_hash, *exclude),
            )
            row = await cursor.fetchone()
            if not row:
                return HistoricalRecord()
            proposed_score, metrics_json, status, hypothesis = row
            metrics = {}
            if metrics_json:
                try:
                    metrics = json.loads(metrics_json)
                except (json.JSONDecodeError, TypeError):
                    metrics = {}
            return HistoricalRecord(
                score=proposed_score,
                metrics=metrics,
                status=status,
                hypothesis=hypothesis or "",
            )

    @trace_call(log_return=False)
    async def find_used_hashes(self, exclude_statuses: tuple[str, ...] | None = None) -> set[str]:
        exclude = exclude_statuses or ("FAILED_VALIDATION",)
        placeholders = ", ".join("?" for _ in exclude)
        async with db_or_connect(self._db) as db:
            cursor = await db.execute(
                f"""
                SELECT config_hash FROM experiments
                WHERE config_hash IS NOT NULL AND config_hash != ''
                  AND status NOT IN ({placeholders})
                UNION
                SELECT config_hash FROM config_hashes
                """,
                exclude,
            )
            return {row[0] for row in await cursor.fetchall()}
