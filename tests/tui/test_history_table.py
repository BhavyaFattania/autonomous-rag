"""Tests for the experiment history table: newest experiment on top, colored
by outcome, matching the DataTable-row-select-to-expand interaction model."""

import pytest
from src.tui.widgets.history_table import HistoryTable
from textual.app import App, ComposeResult
from textual.widgets import DataTable


class _HarnessApp(App):
    def compose(self) -> ComposeResult:
        yield HistoryTable(id="history")


@pytest.mark.asyncio
async def test_add_experiment_inserts_row_at_top():
    app = _HarnessApp()
    async with app.run_test():
        history = app.query_one("#history", HistoryTable)
        table = app.query_one("#history-table", DataTable)

        history.add_experiment(experiment=20, status="ACCEPTED", score=0.85, cost=0.03)
        history.add_experiment(experiment=21, status="RUNNING", score=0.0, cost=0.0)

        first_row = table.get_row_at(0)
        assert first_row[0] == "#21"


@pytest.mark.asyncio
async def test_add_experiment_formats_score_and_cost():
    app = _HarnessApp()
    async with app.run_test():
        history = app.query_one("#history", HistoryTable)

        history.add_experiment(experiment=12, status="ACCEPTED", score=0.844, cost=0.031)

        table = app.query_one("#history-table", DataTable)
        row = table.get_row_at(0)
        assert tuple(row) == ("#12", "ACCEPTED", "0.844", "$0.031")
