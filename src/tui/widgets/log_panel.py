"""Collapsible structured-log tail. Off by default (the hero panel carries
the story); expand with the 'l' key for raw debugging."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Log


class LogPanel(Vertical):
    def compose(self) -> ComposeResult:
        yield Log(id="log-widget", max_lines=500)

    def append_line(self, text: str) -> None:
        self.query_one(Log).write_line(text)
