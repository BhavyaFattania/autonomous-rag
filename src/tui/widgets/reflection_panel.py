"""Reflection is cadence-gated (settings.reflection.update_every_n_experiments),
not per-experiment -- the label always says which experiment it's from so the
UI never implies a live update that didn't happen."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static


class ReflectionPanel(Vertical):
    def compose(self) -> ComposeResult:
        yield Static("No reflection yet.", id="reflection-text")

    def apply_reflection(self, summary: str, experiment_num: int) -> None:
        self.query_one("#reflection-text", Static).update(
            f"Reflection (last @ #{experiment_num}):\n{summary}"
        )
