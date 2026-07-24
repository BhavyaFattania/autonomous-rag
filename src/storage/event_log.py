"""Durable node-level event log: an independent EventBus subscriber that
persists every ExperimentEvent tick to SQLite, so the web dashboard can show
what happened at each pipeline node -- reasoning, config, timing, failures --
long after the live WebSocket tick that carried it is gone. Runs alongside,
and fully decoupled from, the web dashboard's own consume_events() consumer:
a persistence failure here must never affect the live run or its UI."""

import asyncio
import json
import sqlite3

from src.core.events import EventBus, ExperimentEvent
from src.storage.models import NodeEvent
from src.storage.repositories.node_event_repository import NodeEventRepository
from src.utils.logger import get_logger

log = get_logger("event_log")

_LOCK_RETRY_ATTEMPTS = 4
_LOCK_RETRY_BASE_DELAY_SEC = 0.25


def _to_node_event(event: ExperimentEvent, run_id: str) -> NodeEvent:
    return NodeEvent(
        run_id=run_id,
        experiment_uuid=event.experiment_uuid,
        experiment_seq=event.experiment,
        node=event.node,
        status=event.status,
        timestamp=event.timestamp.isoformat(),
        cost_total_usd=event.cost_total_usd,
        message=event.message,
        hypothesis=event.hypothesis,
        reasoning=event.reasoning,
        config_json=json.dumps(event.config) if event.config else None,
        metrics_json=json.dumps(event.metrics) if event.metrics else None,
        failure_reason=event.failure_reason,
        progress_current=event.progress_current,
        progress_total=event.progress_total,
        raw_event_json=json.dumps(event.raw_event, default=str) if event.raw_event else None,
    )


async def _insert_with_lock_retry(repo: NodeEventRepository, node_event: NodeEvent) -> None:
    """recorder_node() and this consumer each open their own ad-hoc SQLite
    connection (see repositories/_shared.py's _AutoCommitContext), so a tick
    landing at the same moment recorder_node() is mid-transaction can still
    hit `database is locked` even with a busy_timeout configured -- observed
    directly in a real run, on the acceptance/recorder ticks specifically.
    Retries with backoff instead of dropping the tick on the first collision."""
    for attempt in range(_LOCK_RETRY_ATTEMPTS):
        try:
            await repo.insert(node_event)
            return
        except sqlite3.OperationalError as e:
            is_last_attempt = attempt == _LOCK_RETRY_ATTEMPTS - 1
            if "locked" not in str(e).lower() or is_last_attempt:
                raise
            await asyncio.sleep(_LOCK_RETRY_BASE_DELAY_SEC * (2**attempt))


async def persist_events(bus: EventBus, run_id: str) -> None:
    """Runs for the lifetime of the run: pulls every ExperimentEvent off its
    own EventBus queue and writes it to the node_events table. A malformed
    or unwritable tick (including a lock collision that outlasts the retries
    above) is logged and skipped -- matches consume_events()'s "one bad tick
    doesn't kill the loop" crash-isolation behavior."""
    queue = bus.subscribe()
    repo = NodeEventRepository()
    while True:
        event = await queue.get()
        try:
            await _insert_with_lock_retry(repo, _to_node_event(event, run_id))
        except Exception:
            log.exception("node_event_persist_failed", node=event.node, experiment=event.experiment)
