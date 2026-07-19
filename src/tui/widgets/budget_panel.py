"""Budget panel: spent/remaining against the hard cost ceiling, with a real
percentage bar (this tracks USD spent, not the indexer's chunk-embedding
progress -- the two ProgressBars measure different things)."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import ProgressBar, Static


class BudgetPanel(Vertical):
    def compose(self) -> ComposeResult:
        yield Static("", id="budget-text")
        yield ProgressBar(id="budget-bar", show_eta=False)

    def apply_totals(self, spent: float, ceiling: float) -> None:
        remaining = max(ceiling - spent, 0.0)
        self.query_one("#budget-text", Static).update(
            f"Spent: ${spent:.2f}   Remaining: ${remaining:.2f}   Ceiling: ${ceiling:.2f}"
        )
        bar = self.query_one("#budget-bar", ProgressBar)
        bar.update(total=ceiling, progress=spent)
