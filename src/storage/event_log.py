"""Durable node-level event log: an independent EventBus subscriber that
persists every ExperimentEvent tick to SQLite, so the web dashboard can show
what happened at each pipeline node -- reasoning, config, timing, failures --
long after the live WebSocket tick that carried it is gone. Runs alongside,
and fully decoupled from, the web dashboard's own consume_events() consumer:
a persistence failure here must never affect the live run or its UI."""

import json

from src.core.events import EventBus, ExperimentEvent
from src.storage.models import NodeEvent
from src.storage.repositories.node_event_repository import NodeEventRepository
from src.storage.write_coordinator import WriteCoordinator, write_transaction
from src.utils.logger import get_logger

log = get_logger("event_log")


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


async def persist_events(
    bus: EventBus, run_id: str, writer: WriteCoordinator | None = None
) -> None:
    """Runs for the lifetime of the run: pulls every ExperimentEvent off its
    own EventBus queue and writes it to the node_events table.

    Every write goes through the shared WriteCoordinator, so this background
    consumer and the pipeline nodes never hold write transactions concurrently
    -- which is what previously produced `database is locked` and forced the
    old retry loop. A malformed or unwritable tick is still logged and skipped,
    matching consume_events()'s "one bad tick doesn't kill the loop" behavior."""
    queue = bus.subscribe()
    while True:
        event = await queue.get()
        try:
            async with write_transaction(writer) as db:
                await NodeEventRepository(db).insert(_to_node_event(event, run_id))
                await db.commit()
        except Exception:
            log.exception("node_event_persist_failed", node=event.node, experiment=event.experiment)
