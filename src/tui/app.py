"""Textual dashboard for overnight optimization runs. Replaces the scrolling
Rich console log with a persistent, non-scrolling view driven by ExperimentEvents
pulled off an asyncio.Queue fed by the EventBus."""

import asyncio

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Static

from src.core.events import ExperimentEvent
from src.tui.widgets.best_config_panel import BestConfigPanel
from src.tui.widgets.budget_panel import BudgetPanel
from src.tui.widgets.experiment_panel import ExperimentPanel
from src.tui.widgets.history_table import HistoryTable
from src.tui.widgets.log_panel import LogPanel
from src.tui.widgets.pipeline_strip import PipelineStrip
from src.tui.widgets.reflection_panel import ReflectionPanel


class RagOptimizerApp(App):
    """Consumes one subscriber queue from an EventBus and renders it as a
    persistent dashboard."""

    CSS_PATH = "app.tcss"

    BINDINGS = [
        Binding("1", "focus_panel('pipeline')", "Workflow"),
        Binding("2", "focus_panel('logs')", "Logs"),
        Binding("3", "focus_panel('experiment')", "Metrics"),
        Binding("4", "focus_panel('history')", "History"),
        Binding("5", "focus_panel('best')", "Best config"),
        Binding("tab", "focus_next", "Next panel", show=False),
        Binding("slash", "focus_panel('history')", "Search", key_display="/"),
        Binding("r", "focus_panel('reflection')", "Reflection"),
        Binding("b", "focus_panel('best')", "Best config"),
        Binding("space", "noop", "Pause (not yet wired to the run)"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, events: "asyncio.Queue[ExperimentEvent]") -> None:
        super().__init__()
        self._events = events
        self._best_config: dict = {}
        self._best_score: float = 0.0

    def compose(self) -> ComposeResult:
        yield PipelineStrip(id="pipeline")
        with Horizontal():
            with Vertical():
                yield BestConfigPanel(id="best")
                yield BudgetPanel(id="budget")
            yield ExperimentPanel(id="experiment")
            with Vertical():
                yield ReflectionPanel(id="reflection")
                yield HistoryTable(id="history")
        yield LogPanel(id="logs")
        yield Static("", id="status")

    async def on_mount(self) -> None:
        self.run_worker(self._consume_events(), exclusive=True)

    async def _consume_events(self) -> None:
        while True:
            event = await self._events.get()
            self._apply_event(event)

    def _apply_event(self, event: ExperimentEvent) -> None:
        self.query_one("#status", Static).update(f"{event.node}: {event.status}")
        self.query_one("#pipeline", PipelineStrip).apply_event(event.node, event.status)
        self.query_one("#experiment", ExperimentPanel).apply_event(event, self._best_config)
        self.query_one("#logs", LogPanel).append_line(
            f"{event.timestamp:%H:%M:%S} {event.node} {event.message}"
        )

        weighted_score = event.metrics.get("median_weighted_score")
        if event.status == "ACCEPTED" and weighted_score is not None:
            self._best_config = event.config
            self._best_score = weighted_score
            self.query_one("#best", BestConfigPanel).apply_best(event.config, weighted_score)

        if event.node == "budget_guard":
            self.query_one("#budget", BudgetPanel).apply_totals(
                spent=event.cost_total_usd, ceiling=event.cost_total_usd
            )

        if event.node == "reflection" and event.reasoning:
            self.query_one("#reflection", ReflectionPanel).apply_reflection(
                event.reasoning, event.experiment
            )

        if event.node == "recorder":
            self.query_one("#history", HistoryTable).add_experiment(
                experiment=event.experiment,
                status=event.status,
                score=weighted_score or 0.0,
                cost=event.cost_total_usd,
            )

    def action_focus_panel(self, panel_id: str) -> None:
        self.query_one(f"#{panel_id}").focus()

    def action_noop(self) -> None:
        pass
