"""Tests for translating a raw LangGraph astream() tick into ExperimentEvents."""

from src.orchestrator.event_adapter import adapt


class _Settings:
    class run:
        cost_hard_ceiling_usd = 10.0


class _FakeCostTracker:
    def __init__(self, total: float):
        self._total = total

    def get_total(self) -> float:
        return self._total


class _FakeProvider:
    def __init__(self, total: float):
        self.cost_tracker = _FakeCostTracker(total)


def test_adapt_ignores_non_dict_values():
    ctx = {"exp_num": 0}
    result = adapt({"__interrupt__": ()}, ctx, _Settings)
    assert result == []


def test_adapt_increments_exp_num_only_on_scientist():
    ctx = {"exp_num": 3}

    result = adapt({"validator": {"status": "RUNNING"}}, ctx, _Settings)
    assert ctx["exp_num"] == 3
    assert result[0].experiment == 3

    result = adapt({"scientist": {"status": "RUNNING", "hypothesis": "h"}}, ctx, _Settings)
    assert ctx["exp_num"] == 4
    assert result[0].experiment == 4
    assert result[0].hypothesis == "h"


def test_adapt_defaults_exp_num_to_zero_when_absent():
    ctx = {}

    result = adapt({"validator": {"status": "RUNNING"}}, ctx, _Settings)
    assert result[0].experiment == 0


def test_adapt_defaults_cost_total_to_zero_without_provider():
    ctx = {"exp_num": 1}
    output = {"status": "ACCEPTED", "aggregated_metrics": {"median_weighted_score": 0.8}}

    [event] = adapt({"acceptance": output}, ctx, _Settings)

    assert event.cost_total_usd == 0.0


def test_adapt_carries_raw_event_for_legacy_fallback():
    ctx = {"exp_num": 1}
    output = {"status": "ACCEPTED", "aggregated_metrics": {"median_weighted_score": 0.8}}

    [event] = adapt({"acceptance": output}, ctx, _Settings, provider=_FakeProvider(0.42))

    assert event.raw_event == {"acceptance": output}
    assert event.metrics == {"median_weighted_score": 0.8}
    assert event.status == "ACCEPTED"
    assert event.cost_total_usd == 0.42


def test_adapt_prefers_proposed_config_falls_back_to_validated_config():
    ctx = {"exp_num": 1}

    [event] = adapt(
        {"scientist": {"status": "RUNNING", "proposed_config": {"chunk_size": 512}}},
        ctx,
        _Settings,
    )
    assert event.config == {"chunk_size": 512}

    [event] = adapt(
        {"validator": {"status": "RUNNING", "validated_config": {"chunk_size": 768}}},
        ctx,
        _Settings,
    )
    assert event.config == {"chunk_size": 768}

    [event] = adapt({"deduplicator": {"status": "RUNNING"}}, ctx, _Settings)
    assert event.config == {}


def test_adapt_uses_node_meta_description_as_message():
    ctx = {"exp_num": 1}

    [event] = adapt({"indexer": {"status": "RUNNING"}}, ctx, _Settings)
    assert event.message == "Building index"

    [event] = adapt({"some_unknown_node": {"status": "RUNNING"}}, ctx, _Settings)
    assert event.message == "some_unknown_node"


def test_adapt_backfills_acceptance_and_recorder_scores_from_real_node_shapes():
    """Reproduces the real LangGraph tick shapes for a full experiment cycle:
    scientist -> ... -> evaluator (produces aggregated_metrics on a RUNNING
    tick) -> acceptance (ACCEPTED, only has current_best_config/
    current_best_weighted_score) -> recorder (has neither field). Both
    acceptance and recorder ticks must end up with a populated
    metrics["median_weighted_score"], since DashboardState.apply() only reads
    scores off of those two node's events."""
    ctx = {}

    adapt(
        {"scientist": {"status": "RUNNING", "proposed_config": {"chunk_size": 512}}}, ctx, _Settings
    )

    aggregated_metrics = {"median_weighted_score": 0.91, "std_dev_weighted_score": 0.01}
    [evaluator_event] = adapt(
        {"evaluator": {"status": "RUNNING", "aggregated_metrics": aggregated_metrics}},
        ctx,
        _Settings,
    )
    assert evaluator_event.metrics == aggregated_metrics

    [acceptance_event] = adapt(
        {
            "acceptance": {
                "status": "ACCEPTED",
                "current_best_config": {"chunk_size": 512, "top_k": 5},
                "current_best_weighted_score": 0.91,
            }
        },
        ctx,
        _Settings,
    )
    assert acceptance_event.metrics == {"median_weighted_score": 0.91}
    assert acceptance_event.config == {"chunk_size": 512, "top_k": 5}

    [recorder_event] = adapt(
        {"recorder": {"status": "ACCEPTED", "experiments_completed": 1}},
        ctx,
        _Settings,
    )
    assert recorder_event.metrics == aggregated_metrics
    assert recorder_event.metrics["median_weighted_score"] == 0.91
    assert recorder_event.config == {"chunk_size": 512, "top_k": 5}


def test_adapt_recorder_does_not_leak_stale_score_from_earlier_experiment():
    """An experiment that fails before reaching the evaluator (e.g. at
    smoke_test) must not have its recorder tick inherit the PREVIOUS
    experiment's evaluator score."""
    ctx = {}

    adapt({"scientist": {"status": "RUNNING"}}, ctx, _Settings)
    adapt(
        {"evaluator": {"status": "RUNNING", "aggregated_metrics": {"median_weighted_score": 0.7}}},
        ctx,
        _Settings,
    )
    adapt(
        {
            "acceptance": {
                "status": "ACCEPTED",
                "current_best_config": {},
                "current_best_weighted_score": 0.7,
            }
        },
        ctx,
        _Settings,
    )
    adapt({"recorder": {"status": "ACCEPTED"}}, ctx, _Settings)

    adapt({"scientist": {"status": "RUNNING"}}, ctx, _Settings)
    adapt({"validator": {"status": "RUNNING"}}, ctx, _Settings)
    [smoke_event] = adapt(
        {"smoke_test": {"status": "FAILED_SMOKE", "failure_reason": "zero results"}}, ctx, _Settings
    )
    assert smoke_event.metrics == {}

    [recorder_event] = adapt(
        {"recorder": {"status": "FAILED_SMOKE", "failure_reason": "zero results"}}, ctx, _Settings
    )
    assert recorder_event.metrics == {}
    assert recorder_event.experiment == 2
