"""Tests for translating a raw LangGraph astream() tick into ExperimentEvents."""

from src.orchestrator.event_adapter import adapt


def test_adapt_ignores_non_dict_values():
    ctx = {"exp_num": 0}
    result = adapt({"__interrupt__": ()}, ctx)
    assert result == []


def test_adapt_increments_exp_num_only_on_scientist(monkeypatch):
    import src.orchestrator.event_adapter as event_adapter

    monkeypatch.setattr(event_adapter, "get_total", lambda: 0.0)
    ctx = {"exp_num": 3}

    result = adapt({"validator": {"status": "RUNNING"}}, ctx)
    assert ctx["exp_num"] == 3
    assert result[0].experiment == 3

    result = adapt({"scientist": {"status": "RUNNING", "hypothesis": "h"}}, ctx)
    assert ctx["exp_num"] == 4
    assert result[0].experiment == 4
    assert result[0].hypothesis == "h"


def test_adapt_defaults_exp_num_to_zero_when_absent(monkeypatch):
    import src.orchestrator.event_adapter as event_adapter

    monkeypatch.setattr(event_adapter, "get_total", lambda: 0.0)
    ctx = {}

    result = adapt({"validator": {"status": "RUNNING"}}, ctx)
    assert result[0].experiment == 0


def test_adapt_carries_raw_event_for_legacy_fallback(monkeypatch):
    import src.orchestrator.event_adapter as event_adapter

    monkeypatch.setattr(event_adapter, "get_total", lambda: 0.42)
    ctx = {"exp_num": 1}
    output = {"status": "ACCEPTED", "aggregated_metrics": {"median_weighted_score": 0.8}}

    [event] = adapt({"acceptance": output}, ctx)

    assert event.raw_event == {"acceptance": output}
    assert event.metrics == {"median_weighted_score": 0.8}
    assert event.status == "ACCEPTED"
    assert event.cost_total_usd == 0.42


def test_adapt_prefers_proposed_config_falls_back_to_validated_config(monkeypatch):
    import src.orchestrator.event_adapter as event_adapter

    monkeypatch.setattr(event_adapter, "get_total", lambda: 0.0)
    ctx = {"exp_num": 1}

    [event] = adapt(
        {"scientist": {"status": "RUNNING", "proposed_config": {"chunk_size": 512}}}, ctx
    )
    assert event.config == {"chunk_size": 512}

    [event] = adapt(
        {"validator": {"status": "RUNNING", "validated_config": {"chunk_size": 768}}}, ctx
    )
    assert event.config == {"chunk_size": 768}

    [event] = adapt({"deduplicator": {"status": "RUNNING"}}, ctx)
    assert event.config == {}


def test_adapt_uses_node_meta_description_as_message(monkeypatch):
    import src.orchestrator.event_adapter as event_adapter

    monkeypatch.setattr(event_adapter, "get_total", lambda: 0.0)
    ctx = {"exp_num": 1}

    [event] = adapt({"indexer": {"status": "RUNNING"}}, ctx)
    assert event.message == "Building index"

    [event] = adapt({"some_unknown_node": {"status": "RUNNING"}}, ctx)
    assert event.message == "some_unknown_node"
