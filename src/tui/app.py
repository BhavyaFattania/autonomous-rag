"""Textual dashboard for overnight optimization runs. Replaces the scrolling
Rich console log with a persistent, non-scrolling view driven by ExperimentEvents
pulled off an asyncio.Queue fed by the EventBus."""

import asyncio

from textual.app import App, ComposeResult
from textual.widgets import Static

from src.core.events import ExperimentEvent


class RagOptimizerApp(App):
    """Consumes one subscriber queue from an EventBus and renders it as a
    persistent dashboard. Widgets are added incrementally in later tasks;
    this skeleton proves the queue-to-screen plumbing."""

    def __init__(self, events: "asyncio.Queue[ExperimentEvent]") -> None:
        super().__init__()
        self._events = events

    def compose(self) -> ComposeResult:
        yield Static("Waiting for first event...", id="status")

    async def on_mount(self) -> None:
        self.run_worker(self._consume_events(), exclusive=True)

    async def _consume_events(self) -> None:
        while True:
            event = await self._events.get()
            self.query_one("#status", Static).update(f"{event.node}: {event.status}")
