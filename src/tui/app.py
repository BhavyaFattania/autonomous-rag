"""Textual dashboard for overnight optimization runs. Replaces the scrolling
Rich console log with a persistent, non-scrolling view driven by ExperimentEvents
pulled off an asyncio.Queue fed by the EventBus. Event application goes through
DashboardState first (crash-isolated, unit-testable); widget updates are each
wrapped independently so one bad event degrades at most one panel instead of
killing the worker loop for the rest of an unattended overnight run."""

import asyncio

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Static

from src.core.events import ExperimentEvent
from src.core.dashboard_state import DashboardState, FailureInfo
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
        Binding("e", "show_export_hint", "Export"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, events: "asyncio.Queue[ExperimentEvent]", run_id: str = "") -> None:
        super().__init__()
        self._events = events
        self._run_id = run_id
        self._state = DashboardState()

    def compose(self) -> ComposeResult:
        yield PipelineStrip(id="pipeline")
        yield Static("", id="failure-banner")
        with Horizontal():
            with Vertical():
                yield BestConfigPanel(id="best")
                yield BudgetPanel(id="budget")
            yield ExperimentPanel(id="experiment")
            with Vertical():
                yield ReflectionPanel(id="reflection")
                yield HistoryTable(id="history")
        yield LogPanel(id="logs")
        yield Static(f"Run: {self._run_id or '(none)'}", id="run-id")
        yield Static("", id="status")

    async def on_mount(self) -> None:
        self.query_one("#failure-banner", Static).styles.display = "none"
        self.run_worker(self._consume_events(), exclusive=True)

    async def _consume_events(self) -> None:
        while True:
            event = await self._events.get()
            self._apply_event(event)

    def _apply_event(self, event: ExperimentEvent) -> None:
        try:
            self._state.apply(event)
        except Exception as exc:
            self._safe_log(f"[state error] {exc}")
            return

        state = self._state
        self._safe(
            lambda: self.query_one("#status", Static).update(f"{event.node}: {event.status}")
        )
        self._safe(
            lambda: self.query_one("#pipeline", PipelineStrip).apply_event(event.node, event.status)
        )
        self._safe(
            lambda: self.query_one("#experiment", ExperimentPanel).apply_event(
                event, state.best_config
            )
        )

        log_line = f"{event.timestamp:%H:%M:%S} {event.node} {event.message}"
        if event.failure_reason:
            log_line += f" — {event.failure_reason}"
        self._safe(lambda: self.query_one("#logs", LogPanel).append_line(log_line))

        if event.status == "ACCEPTED" and state.best_score:
            self._safe(
                lambda: self.query_one("#best", BestConfigPanel).apply_best(
                    state.best_config, state.best_score
                )
            )

        if event.node == "budget_guard":
            self._safe(
                lambda: self.query_one("#budget", BudgetPanel).apply_totals(
                    spent=state.budget_spent, ceiling=state.budget_ceiling or 0.0
                )
            )

        if event.node == "reflection" and event.reasoning:
            self._safe(
                lambda: self.query_one("#reflection", ReflectionPanel).apply_reflection(
                    event.reasoning, event.experiment
                )
            )

        if event.node == "recorder" and state.history:
            row = state.history[-1]
            self._safe(
                lambda: self.query_one("#history", HistoryTable).add_experiment(
                    experiment=row.experiment, status=row.status, score=row.score, cost=row.cost
                )
            )

        if state.last_failure is not None:
            self._safe(lambda: self._show_failure_banner(state.last_failure))

    def _show_failure_banner(self, failure: FailureInfo) -> None:
        banner = self.query_one("#failure-banner", Static)
        banner.update(f"FAILED: {failure.node} {failure.status} — {failure.failure_reason}")
        banner.styles.display = "block"

    def _safe(self, fn) -> None:
        try:
            fn()
        except Exception as exc:
            self._safe_log(f"[render error] {exc}")

    def _safe_log(self, text: str) -> None:
        try:
            self.query_one("#logs", LogPanel).append_line(text)
        except Exception:
            pass

    def action_focus_panel(self, panel_id: str) -> None:
        self.query_one(f"#{panel_id}").focus()

    def action_show_export_hint(self) -> None:
        cmd = f"python scripts/export_experiments.py --run-id {self._run_id} --format json"
        self._safe_log(f"Export this run: {cmd}")

    def action_noop(self) -> None:
        pass
