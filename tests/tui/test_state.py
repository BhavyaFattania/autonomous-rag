"""Tests for DashboardState.apply() -- the crash-isolation seam that turns a
raw ExperimentEvent into a plain-Python state object the app can render
from, testable without a Textual pilot."""

from datetime import UTC, datetime

from src.core.events import ExperimentEvent
from src.tui.state import DashboardState


def _event(**overrides) -> ExperimentEvent:
    defaults = dict(
        experiment=1,
        node="scientist",
        status="RUNNING",
        timestamp=datetime.now(UTC),
        cost_total_usd=0.0,
    )
    defaults.update(overrides)
    return ExperimentEvent(**defaults)


def test_apply_tracks_node_states_and_active_node():
    state = DashboardState()
    state.apply(_event(node="scientist", status="RUNNING"))
    state.apply(_event(node="scientist", status="ACCEPTED"))
    state.apply(_event(node="validator", status="RUNNING"))

    assert state.node_states["scientist"] == "ACCEPTED"
    assert state.node_states["validator"] == "RUNNING"
    assert state.active_node == "validator"


def test_apply_updates_best_config_on_accepted_with_score():
    state = DashboardState()
    state.apply(
        _event(
            node="acceptance",
            status="ACCEPTED",
            config={"chunk_size": 768},
            metrics={"median_weighted_score": 0.87},
        )
    )

    assert state.best_config == {"chunk_size": 768}
    assert state.best_score == 0.87


def test_apply_ignores_accepted_without_score():
    state = DashboardState()
    state.apply(_event(node="acceptance", status="ACCEPTED", config={"chunk_size": 768}))

    assert state.best_config == {}
    assert state.best_score == 0.0


def test_apply_tracks_budget_from_budget_guard_node():
    state = DashboardState()
    state.apply(
        _event(node="budget_guard", status="RUNNING", cost_total_usd=1.5, cost_ceiling_usd=10.0)
    )

    assert state.budget_spent == 1.5
    assert state.budget_ceiling == 10.0


def test_apply_appends_history_row_on_recorder():
    state = DashboardState()
    state.apply(
        _event(
            node="recorder",
            status="ACCEPTED",
            experiment=5,
            cost_total_usd=0.03,
            metrics={"median_weighted_score": 0.8},
        )
    )

    assert len(state.history) == 1
    row = state.history[0]
    assert row.experiment == 5
    assert row.status == "ACCEPTED"
    assert row.score == 0.8
    assert row.cost == 0.03


def test_apply_defaults_history_score_to_zero_when_absent():
    state = DashboardState()
    state.apply(_event(node="recorder", status="REJECTED", experiment=6, cost_total_usd=0.01))

    assert state.history[0].score == 0.0


def test_apply_sets_last_failure_on_failed_status():
    state = DashboardState()
    state.apply(
        _event(
            node="smoke_test",
            status="FAILED_SMOKE",
            failure_reason="Query returned zero results",
        )
    )

    assert state.last_failure is not None
    assert state.last_failure.node == "smoke_test"
    assert state.last_failure.status == "FAILED_SMOKE"
    assert state.last_failure.failure_reason == "Query returned zero results"


def test_apply_sets_last_failure_on_budget_exceeded_and_interrupted():
    state = DashboardState()
    state.apply(_event(node="budget_guard", status="BUDGET_EXCEEDED"))
    assert state.last_failure.status == "BUDGET_EXCEEDED"

    state.apply(_event(node="scientist", status="INTERRUPTED"))
    assert state.last_failure.status == "INTERRUPTED"


def test_apply_leaves_last_failure_none_on_success_statuses():
    state = DashboardState()
    state.apply(_event(node="scientist", status="RUNNING"))
    state.apply(_event(node="acceptance", status="ACCEPTED"))

    assert state.last_failure is None


def test_last_failure_is_overwritten_by_the_most_recent_failure():
    state = DashboardState()
    state.apply(_event(node="smoke_test", status="FAILED_SMOKE", failure_reason="first"))
    state.apply(_event(node="evaluator", status="FAILED_API_ERROR", failure_reason="second"))

    assert state.last_failure.node == "evaluator"
    assert state.last_failure.failure_reason == "second"
