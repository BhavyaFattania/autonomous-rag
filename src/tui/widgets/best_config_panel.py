"""Pinned 'current champion' card -- always visible, updated whenever a new
experiment beats the previous best score."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static


class BestConfigPanel(Vertical):
    def compose(self) -> ComposeResult:
        yield Static("No accepted experiment yet.", id="best-text")

    def apply_best(self, config: dict, score: float) -> None:
        fields = "\n".join(f"{key}: {value}" for key, value in config.items())
        self.query_one("#best-text", Static).update(f"Best score: {score:.3f}\n{fields}")
