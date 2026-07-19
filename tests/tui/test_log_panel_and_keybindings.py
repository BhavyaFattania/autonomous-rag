"""Tests for the collapsible log tail and the app's keybindings."""

import pytest
from src.tui.widgets.log_panel import LogPanel
from textual.app import App, ComposeResult
from textual.widgets import Log


class _HarnessApp(App):
    def compose(self) -> ComposeResult:
        yield LogPanel(id="logs")


@pytest.mark.asyncio
async def test_append_line_adds_to_log_widget():
    app = _HarnessApp()
    async with app.run_test():
        panel = app.query_one("#logs", LogPanel)

        panel.append_line("14:22:03 indexer building hybrid collection...")

        log_widget = app.query_one(Log)
        assert "building hybrid collection" in "\n".join(log_widget.lines)
