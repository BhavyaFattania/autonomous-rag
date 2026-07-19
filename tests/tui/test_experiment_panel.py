"""Tests for the hero panel: hypothesis/reasoning, config diff, and the
real indexer completion-percentage progress bar."""

from datetime import UTC, datetime

import pytest
from src.core.events import ExperimentEvent
from src.tui.widgets.experiment_panel import ExperimentPanel
from textual.app import App, ComposeResult
from textual.widgets import ProgressBar


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


class _HarnessApp(App):
    def compose(self) -> ComposeResult:
        yield ExperimentPanel(id="panel")


@pytest.mark.asyncio
async def test_scientist_event_shows_hypothesis_and_reasoning():
    app = _HarnessApp()
    async with app.run_test():
        panel = app.query_one("#panel", ExperimentPanel)

        panel.apply_event(
            _event(
                node="scientist",
                hypothesis="Hybrid retrieval should recover precision.",
                reasoning="Prior semantic-only runs plateaued.",
            ),
            best_config={},
        )

        assert "Hybrid retrieval" in panel.hypothesis_text
        assert "plateaued" in panel.reasoning_text


@pytest.mark.asyncio
async def test_indexer_progress_updates_real_progress_bar():
    app = _HarnessApp()
    async with app.run_test():
        panel = app.query_one("#panel", ExperimentPanel)

        panel.apply_event(
            _event(node="indexer", progress_current=64, progress_total=150),
            best_config={},
        )

        bar = app.query_one("#indexer-progress", ProgressBar)
        assert bar.progress == 64
        assert bar.total == 150


@pytest.mark.asyncio
async def test_non_indexer_event_does_not_touch_progress_bar():
    app = _HarnessApp()
    async with app.run_test():
        panel = app.query_one("#panel", ExperimentPanel)

        panel.apply_event(
            _event(node="indexer", progress_current=64, progress_total=150), best_config={}
        )
        panel.apply_event(_event(node="validator", status="RUNNING"), best_config={})

        bar = app.query_one("#indexer-progress", ProgressBar)
        assert bar.progress == 64
        assert bar.total == 150


@pytest.mark.asyncio
async def test_config_diff_rows_computed_against_best_config():
    app = _HarnessApp()
    async with app.run_test():
        panel = app.query_one("#panel", ExperimentPanel)

        panel.apply_event(
            _event(node="validator", config={"chunk_size": 768, "retriever": "hybrid"}),
            best_config={"chunk_size": 512, "retriever": "hybrid"},
        )

        assert panel.config_diff_rows == [
            ("chunk_size", 768, "↑ from 512"),
            ("retriever", "hybrid", "same"),
        ]
