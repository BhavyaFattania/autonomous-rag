"""Tests for converting DashboardState (a plain dataclass) into a
JSON-serializable Pydantic schema for the WebSocket broadcast."""

from src.core.dashboard_state import DashboardState, ExperimentRow, FailureInfo
from src.web.schemas import DashboardStateSchema


def test_from_state_carries_over_scalar_fields():
    state = DashboardState(
        active_node="indexer",
        best_config={"chunk_size": 512},
        best_score=0.87,
        budget_spent=1.5,
        budget_ceiling=10.0,
    )
    state.node_states["scientist"] = "ACCEPTED"

    schema = DashboardStateSchema.from_state(state)

    assert schema.active_node == "indexer"
    assert schema.best_config == {"chunk_size": 512}
    assert schema.best_score == 0.87
    assert schema.budget_spent == 1.5
    assert schema.budget_ceiling == 10.0
    assert schema.node_states == {"scientist": "ACCEPTED"}


def test_from_state_converts_history_rows():
    state = DashboardState()
    state.history.append(ExperimentRow(experiment=5, status="ACCEPTED", score=0.8, cost=0.03))

    schema = DashboardStateSchema.from_state(state)

    assert len(schema.history) == 1
    assert schema.history[0].experiment == 5
    assert schema.history[0].status == "ACCEPTED"
    assert schema.history[0].score == 0.8
    assert schema.history[0].cost == 0.03


def test_from_state_converts_last_failure_when_present():
    from datetime import UTC, datetime

    state = DashboardState()
    state.last_failure = FailureInfo(
        node="smoke_test",
        status="FAILED_SMOKE",
        failure_reason="zero results",
        timestamp=datetime.now(UTC),
    )

    schema = DashboardStateSchema.from_state(state)

    assert schema.last_failure is not None
    assert schema.last_failure.node == "smoke_test"
    assert schema.last_failure.failure_reason == "zero results"


def test_from_state_last_failure_none_when_absent():
    schema = DashboardStateSchema.from_state(DashboardState())
    assert schema.last_failure is None


def test_from_state_includes_pipeline_order():
    schema = DashboardStateSchema.from_state(DashboardState())
    assert schema.pipeline_order == [
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


def test_schema_round_trips_through_json():
    state = DashboardState(best_score=0.5)
    schema = DashboardStateSchema.from_state(state)

    as_json = schema.model_dump_json()
    reloaded = DashboardStateSchema.model_validate_json(as_json)

    assert reloaded == schema
