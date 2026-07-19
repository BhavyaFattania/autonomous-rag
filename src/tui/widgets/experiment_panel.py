"""The dashboard's hero panel: the current experiment's hypothesis, reasoning,
config diff against the best-known config, and — the only node with genuine
sub-progress today — a real completion-percentage bar while the indexer runs."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import ProgressBar, Static

from src.core.events import ExperimentEvent
from src.tui.formatting import compute_config_diff


class ExperimentPanel(Vertical):
    """Hero panel: shape changes with whichever node is active, rather than
    showing four static, equally-weighted boxes."""

    hypothesis_text: reactive[str] = reactive("")
    reasoning_text: reactive[str] = reactive("")
    config_diff_rows: reactive[list] = reactive(list)

    def compose(self) -> ComposeResult:
        yield Static("", id="hypothesis")
        yield Static("", id="reasoning")
        yield Static("", id="config-diff")
        yield ProgressBar(id="indexer-progress", show_eta=False)

    def apply_event(self, event: ExperimentEvent, best_config: dict) -> None:
        if event.node == "scientist" and event.hypothesis:
            self.hypothesis_text = event.hypothesis
            self.reasoning_text = event.reasoning
            self.query_one("#hypothesis", Static).update(f"Hypothesis: {event.hypothesis}")
            self.query_one("#reasoning", Static).update(f"Reasoning: {event.reasoning}")

        if (
            event.node == "indexer"
            and event.progress_total is not None
            and event.progress_current is not None
        ):
            bar = self.query_one("#indexer-progress", ProgressBar)
            bar.update(total=event.progress_total, progress=event.progress_current)

        if event.config:
            self.config_diff_rows = compute_config_diff(event.config, best_config)
            lines = [f"{field}: {value} ({note})" for field, value, note in self.config_diff_rows]
            self.query_one("#config-diff", Static).update("\n".join(lines))
