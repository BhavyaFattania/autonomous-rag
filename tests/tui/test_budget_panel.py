"""Tests for the budget panel: spent/remaining and a real percentage bar
against the hard ceiling (not the indexer's progress -- this is cost, not chunks)."""

import pytest
from src.tui.widgets.budget_panel import BudgetPanel
from textual.app import App, ComposeResult
from textual.widgets import ProgressBar, Static


class _HarnessApp(App):
    def compose(self) -> ComposeResult:
        yield BudgetPanel(id="budget")


@pytest.mark.asyncio
async def test_apply_totals_updates_spent_and_remaining_text():
    app = _HarnessApp()
    async with app.run_test():
        panel = app.query_one("#budget", BudgetPanel)

        panel.apply_totals(spent=1.24, ceiling=3.00)

        text = str(app.query_one("#budget-text", Static).content)
        assert "$1.24" in text
        assert "$1.76" in text  # remaining = ceiling - spent


@pytest.mark.asyncio
async def test_apply_totals_updates_progress_bar_percentage():
    app = _HarnessApp()
    async with app.run_test():
        panel = app.query_one("#budget", BudgetPanel)

        panel.apply_totals(spent=1.5, ceiling=3.00)

        bar = app.query_one("#budget-bar", ProgressBar)
        assert bar.total == 3.00
        assert bar.progress == 1.5


@pytest.mark.asyncio
async def test_zero_ceiling_does_not_crash():
    app = _HarnessApp()
    async with app.run_test():
        panel = app.query_one("#budget", BudgetPanel)

        panel.apply_totals(spent=0.0, ceiling=0.0)  # must not raise ZeroDivisionError

        bar = app.query_one("#budget-bar", ProgressBar)
        assert bar.total == 0.0
