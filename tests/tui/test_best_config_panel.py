"""Tests for the pinned best-configuration card."""

import pytest
from src.tui.widgets.best_config_panel import BestConfigPanel
from textual.app import App, ComposeResult
from textual.widgets import Static


class _HarnessApp(App):
    def compose(self) -> ComposeResult:
        yield BestConfigPanel(id="best")


@pytest.mark.asyncio
async def test_apply_best_shows_score_and_fields():
    app = _HarnessApp()
    async with app.run_test():
        panel = app.query_one("#best", BestConfigPanel)

        panel.apply_best(
            config={"retriever": "hybrid", "embedding_model": "baai/bge-m3"}, score=0.873
        )

        text = str(app.query_one("#best-text", Static).content)
        assert "0.873" in text
        assert "hybrid" in text
        assert "baai/bge-m3" in text


@pytest.mark.asyncio
async def test_apply_best_overwrites_previous_champion():
    app = _HarnessApp()
    async with app.run_test():
        panel = app.query_one("#best", BestConfigPanel)

        panel.apply_best(config={"retriever": "dense"}, score=0.80)
        panel.apply_best(config={"retriever": "hybrid"}, score=0.873)

        text = str(app.query_one("#best-text", Static).content)
        assert "hybrid" in text
        assert "dense" not in text
