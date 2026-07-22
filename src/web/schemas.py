"""Pydantic models for JSON payloads sent to the browser: the WebSocket
broadcast shape (DashboardStateSchema, wrapping the plain-dataclass
DashboardState) and, later in this plan, the REST history response shapes."""

from datetime import datetime

from pydantic import BaseModel

from src.core.dashboard_state import PIPELINE_ORDER, DashboardState


class ExperimentRowSchema(BaseModel):
    experiment: int
    status: str
    score: float
    cost: float


class FailureInfoSchema(BaseModel):
    node: str
    status: str
    failure_reason: str
    timestamp: datetime


class DashboardStateSchema(BaseModel):
    node_states: dict[str, str]
    active_node: str | None
    best_config: dict
    best_score: float
    budget_spent: float
    budget_ceiling: float | None
    history: list[ExperimentRowSchema]
    last_failure: FailureInfoSchema | None
    pipeline_order: list[str]

    @classmethod
    def from_state(cls, state: DashboardState) -> "DashboardStateSchema":
        return cls(
            node_states=state.node_states,
            active_node=state.active_node,
            best_config=state.best_config,
            best_score=state.best_score,
            budget_spent=state.budget_spent,
            budget_ceiling=state.budget_ceiling,
            history=[
                ExperimentRowSchema(
                    experiment=row.experiment,
                    status=row.status,
                    score=row.score,
                    cost=row.cost,
                )
                for row in state.history
            ],
            last_failure=(
                FailureInfoSchema(
                    node=state.last_failure.node,
                    status=state.last_failure.status,
                    failure_reason=state.last_failure.failure_reason,
                    timestamp=state.last_failure.timestamp,
                )
                if state.last_failure is not None
                else None
            ),
            pipeline_order=PIPELINE_ORDER,
        )
