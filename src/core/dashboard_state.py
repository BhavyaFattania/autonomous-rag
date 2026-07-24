"""Plain-Python state derived from ExperimentEvents -- no Textual or web
framework imports, so DashboardState.apply() is unit-testable in isolation
and is the seam where a malformed event's blast radius is contained to
"one state update failed," not "the whole dashboard worker died mid-run."
Used by src/web/live.py (the WebSocket broadcaster)."""

from dataclasses import dataclass, field
from datetime import datetime

from src.core.events import ExperimentEvent

PIPELINE_ORDER = [
    "scientist",
    "validator",
    "deduplicator",
    "budget_guard",
    "indexer",
    "smoke_test",
    "evaluator",
    "acceptance",
    "recorder",
    "reflection",
]

_FAILURE_STATUSES = {"BUDGET_EXCEEDED", "INTERRUPTED"}


@dataclass
class FailureInfo:
    node: str
    status: str
    failure_reason: str
    timestamp: datetime


@dataclass
class ExperimentRow:
    experiment: int
    status: str
    score: float
    cost: float
    experiment_uuid: str = ""


@dataclass
class DashboardState:
    node_states: dict = field(default_factory=dict)
    active_node: str | None = None
    current_experiment_uuid: str | None = None
    best_config: dict = field(default_factory=dict)
    best_score: float = 0.0
    budget_spent: float = 0.0
    budget_ceiling: float | None = None
    history: list = field(default_factory=list)
    last_failure: FailureInfo | None = None

    def apply(self, event: ExperimentEvent) -> None:
        self.node_states[event.node] = event.status
        self.active_node = event.node
        if event.experiment_uuid:
            self.current_experiment_uuid = event.experiment_uuid

        weighted_score = event.metrics.get("median_weighted_score")
        if event.status == "ACCEPTED" and weighted_score is not None:
            self.best_config = event.config
            self.best_score = weighted_score

        if event.node == "budget_guard":
            self.budget_spent = event.cost_total_usd
            self.budget_ceiling = event.cost_ceiling_usd

        if event.node == "recorder":
            self.history.append(
                ExperimentRow(
                    experiment=event.experiment,
                    status=event.status,
                    score=weighted_score or 0.0,
                    cost=event.cost_total_usd,
                    experiment_uuid=event.experiment_uuid,
                )
            )

        if event.status in _FAILURE_STATUSES or event.status.startswith("FAILED_"):
            self.last_failure = FailureInfo(
                node=event.node,
                status=event.status,
                failure_reason=event.failure_reason,
                timestamp=event.timestamp,
            )
