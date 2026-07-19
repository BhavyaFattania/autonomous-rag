"""Scrollable experiment history: newest on top, so the dashboard reads as
'what just happened' rather than needing the user to scroll to the bottom."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable


class HistoryTable(Vertical):
    def compose(self) -> ComposeResult:
        # Distinct id from the outer widget's -- query_one() in this Textual
        # version resolves a "#foo" selector to the first matching node and
        # then type-checks it, rather than filtering candidates by type first,
        # so a shared id between parent and child doesn't disambiguate them.
        table: DataTable[str] = DataTable(id="history-table")
        table.add_columns("Experiment", "Status", "Score", "Cost")
        yield table

    def add_experiment(self, experiment: int, status: str, score: float, cost: float) -> None:
        table = self.query_one(DataTable)
        table.add_row(f"#{experiment}", status, f"{score:.3f}", f"${cost:.3f}", key=str(experiment))
        table.move_cursor(row=0)
        table.sort(key=lambda row: -int(row[0].lstrip("#")))
