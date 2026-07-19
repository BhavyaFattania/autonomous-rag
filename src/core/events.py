"""Normalized event model and publish-subscribe bus for broadcasting experiment
progress to independent consumers (the TUI, the legacy console log, and future
sinks such as SQLite or a web dashboard's WebSocket relay) without the
orchestration loop knowing any of them exist.
"""

import asyncio
from datetime import datetime

from pydantic import BaseModel


class ExperimentEvent(BaseModel):
    """One normalized tick: either a LangGraph node transition, or a
    sub-progress update (e.g. indexer embedding batches) between ticks."""

    experiment: int
    node: str
    status: str
    timestamp: datetime
    cost_total_usd: float
    cost_ceiling_usd: float | None = None
    message: str = ""
    hypothesis: str = ""
    reasoning: str = ""
    config: dict = {}
    metrics: dict = {}
    failure_reason: str = ""
    progress_current: int | None = None
    progress_total: int | None = None
    raw_event: dict = {}


class EventBus:
    """Publish-subscribe broker. Each subscriber gets its own queue so a slow
    consumer (a redrawing TUI) never blocks a fast one (a log writer), and
    vice versa."""

    def __init__(self) -> None:
        self._queues: list[asyncio.Queue[ExperimentEvent]] = []

    def subscribe(self) -> "asyncio.Queue[ExperimentEvent]":
        queue: asyncio.Queue[ExperimentEvent] = asyncio.Queue()
        self._queues.append(queue)
        return queue

    def publish(self, event: ExperimentEvent) -> None:
        for queue in self._queues:
            queue.put_nowait(event)
