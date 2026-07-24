import aiosqlite

from src.storage.models import NodeEvent
from src.storage.repositories._shared import db_or_connect

_COLUMNS = """
    id, run_id, experiment_uuid, experiment_seq, node, status, timestamp,
    cost_total_usd, message, hypothesis, reasoning, config_json, metrics_json,
    failure_reason, progress_current, progress_total, raw_event_json
"""


def _row_to_node_event(row) -> NodeEvent:
    return NodeEvent(
        id=row[0],
        run_id=row[1],
        experiment_uuid=row[2],
        experiment_seq=row[3],
        node=row[4],
        status=row[5],
        timestamp=row[6],
        cost_total_usd=row[7],
        message=row[8],
        hypothesis=row[9],
        reasoning=row[10],
        config_json=row[11],
        metrics_json=row[12],
        failure_reason=row[13],
        progress_current=row[14],
        progress_total=row[15],
        raw_event_json=row[16],
    )


class NodeEventRepository:
    """DAO for node_events -- the durable per-tick log that lets the
    dashboard show what happened at every pipeline node, not just the
    experiment-level summary recorder_node writes to `experiments`."""

    def __init__(self, db: aiosqlite.Connection | None = None):
        self._db = db

    async def insert(self, event: NodeEvent) -> int:
        async with db_or_connect(self._db) as db:
            cursor = await db.execute(
                """
                INSERT INTO node_events
                (run_id, experiment_uuid, experiment_seq, node, status, timestamp,
                 cost_total_usd, message, hypothesis, reasoning, config_json,
                 metrics_json, failure_reason, progress_current, progress_total,
                 raw_event_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.run_id,
                    event.experiment_uuid,
                    event.experiment_seq,
                    event.node,
                    event.status,
                    event.timestamp,
                    event.cost_total_usd,
                    event.message,
                    event.hypothesis,
                    event.reasoning,
                    event.config_json,
                    event.metrics_json,
                    event.failure_reason,
                    event.progress_current,
                    event.progress_total,
                    event.raw_event_json,
                ),
            )
            return cursor.lastrowid

    async def find_by_experiment_uuid(self, experiment_uuid: str) -> list[NodeEvent]:
        """Full node timeline for one experiment, oldest first (execution order)."""
        async with db_or_connect(self._db) as db:
            cursor = await db.execute(
                f"SELECT {_COLUMNS} FROM node_events WHERE experiment_uuid = ? ORDER BY id ASC",
                (experiment_uuid,),
            )
            rows = await cursor.fetchall()
            return [_row_to_node_event(row) for row in rows]

    async def find_by_run_id(
        self,
        run_id: str,
        node: str | None = None,
        status: str | None = None,
        before_id: int | None = None,
        limit: int = 50,
    ) -> list[NodeEvent]:
        """Paginated log feed for one run, newest first. `before_id` is the
        cursor: pass the last-seen row's id to fetch the next older page."""
        clauses = ["run_id = ?"]
        params: list = [run_id]
        if node:
            clauses.append("node = ?")
            params.append(node)
        if status:
            clauses.append("status = ?")
            params.append(status)
        if before_id is not None:
            clauses.append("id < ?")
            params.append(before_id)
        where = " AND ".join(clauses)
        params.append(limit)

        async with db_or_connect(self._db) as db:
            cursor = await db.execute(
                f"SELECT {_COLUMNS} FROM node_events WHERE {where} ORDER BY id DESC LIMIT ?",
                params,
            )
            rows = await cursor.fetchall()
            return [_row_to_node_event(row) for row in rows]
