"""Tests for the pipeline-strip signature widget: all 10 real workflow nodes
rendered left-to-right, current node highlighted, completed nodes colored by
their terminal status."""

import pytest
from src.tui.widgets.pipeline_strip import PIPELINE_ORDER, PipelineStrip
from textual.app import App, ComposeResult


class _HarnessApp(App):
    def compose(self) -> ComposeResult:
        yield PipelineStrip(id="strip")


def test_pipeline_order_matches_graph_execution_order():
    assert PIPELINE_ORDER == [
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


@pytest.mark.asyncio
async def test_apply_event_marks_node_active_and_running():
    app = _HarnessApp()
    async with app.run_test():
        strip = app.query_one("#strip", PipelineStrip)

        strip.apply_event("scientist", "RUNNING")

        assert strip.active_node == "scientist"
        assert strip.node_states["scientist"] == "RUNNING"


@pytest.mark.asyncio
async def test_apply_event_accumulates_across_nodes():
    app = _HarnessApp()
    async with app.run_test():
        strip = app.query_one("#strip", PipelineStrip)

        strip.apply_event("scientist", "RUNNING")
        strip.apply_event("scientist", "ACCEPTED")
        strip.apply_event("validator", "RUNNING")

        assert strip.node_states["scientist"] == "ACCEPTED"
        assert strip.node_states["validator"] == "RUNNING"
        assert strip.active_node == "validator"
