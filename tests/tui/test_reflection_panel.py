"""Tests for the reflection panel. Reflection only fires every N experiments
(settings.reflection.update_every_n_experiments), so the label must say which
experiment it's from rather than implying it updates every tick."""

import pytest
from src.tui.widgets.reflection_panel import ReflectionPanel
from textual.app import App, ComposeResult
from textual.widgets import Static


class _HarnessApp(App):
    def compose(self) -> ComposeResult:
        yield ReflectionPanel(id="reflection")


@pytest.mark.asyncio
async def test_apply_reflection_shows_summary_and_experiment_number():
    app = _HarnessApp()
    async with app.run_test():
        panel = app.query_one("#reflection", ReflectionPanel)

        panel.apply_reflection("Hybrid retrieval is now the focus.", experiment_num=18)

        text = str(app.query_one("#reflection-text", Static).content)
        assert "Hybrid retrieval is now the focus." in text
        assert "#18" in text


@pytest.mark.asyncio
async def test_no_reflection_yet_shows_placeholder():
    app = _HarnessApp()
    async with app.run_test():
        text = str(app.query_one("#reflection-text", Static).content)
        assert "No reflection yet" in text
