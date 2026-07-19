"""The dashboard's signature element: all 10 workflow nodes rendered as a
single horizontal strip, read left-to-right like a sentence rather than a
node-graph canvas (which doesn't fit a terminal's width). Reuses the existing
NODE_META/STATUS_STYLE vocabulary from overnight_display.py instead of
inventing new iconography."""

from rich.text import Text
from textual.reactive import reactive
from textual.widgets import Static

from src.orchestrator.overnight_display import NODE_META, STATUS_STYLE

PIPELINE_ORDER = [
    "scientist",
    "validator",
    "deduplicator",
    "budget_guard",
    "indexer",
    "smoke_test",
    "evaluator",
    "acceptance",
    "recorder",
    "reflection",
]


class PipelineStrip(Static):
    """Shows all pipeline nodes; the active one is highlighted, completed
    ones take their terminal status color, unvisited ones stay dim."""

    node_states: reactive[dict] = reactive(dict)
    active_node: reactive[str | None] = reactive(None)

    def watch_node_states(self, _states: dict) -> None:
        self._redraw()

    def watch_active_node(self, _node: str | None) -> None:
        self._redraw()

    def apply_event(self, node: str, status: str) -> None:
        states = dict(self.node_states)
        states[node] = status
        self.active_node = node
        self.node_states = states

    def _redraw(self) -> None:
        text = Text()
        for i, node in enumerate(PIPELINE_ORDER):
            emoji, node_style, _ = NODE_META.get(node, ("--", "white", node))
            status = self.node_states.get(node)
            if node == self.active_node and status in (None, "RUNNING", "PENDING"):
                style = f"reverse bold {node_style}"
            elif status is not None:
                style, _ = STATUS_STYLE.get(status, ("dim", "?"))
            else:
                style = "dim"
            text.append(f" {emoji} ", style=style)
            if i < len(PIPELINE_ORDER) - 1:
                text.append("─", style="dim")
        self.update(text)
