"""
RAG-OPT :: Autonomous RAG Optimizer — Terminal Dashboard
----------------------------------------------------------
A UI-only mockup (no real API calls / no real optimizer loop).
Flow: Auth -> Model Select -> Dashboard.

Run:
    pip install textual --break-system-packages
    python3 rag_optimizer_tui.py
"""

import random
from datetime import datetime

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    ProgressBar,
    RadioButton,
    RadioSet,
    RichLog,
    Select,
    Static,
)

# ----------------------------------------------------------------------
# Static reference data (all cosmetic — nothing here calls a real API)
# ----------------------------------------------------------------------

PROVIDERS = ["Anthropic", "OpenAI", "Google", "Azure OpenAI", "Local (Ollama)"]

SCIENTIST_MODELS = [
    "claude-opus-4-8",
    "claude-sonnet-5",
    "gpt-5.1",
    "gemini-2.5-pro",
]
EVALUATOR_MODELS = [
    "claude-sonnet-5",
    "gpt-5.1-mini",
    "claude-haiku-4-5",
]
EMBEDDING_MODELS = [
    "voyage-3-large",
    "text-embedding-3-large",
    "bge-m3",
]
TARGET_METRICS = [
    ("faithfulness", "faithfulness"),
    ("context_recall", "context_recall"),
    ("answer_relevancy", "answer_relevancy"),
    ("composite_score", "composite_score"),
]

NODES = [
    ("SCIENTIST", "propose rag config"),
    ("VALIDATOR", "schema + bounds check"),
    ("DEDUPLICATOR", "config hash check"),
    ("BUDGET_GUARD", "api cost check"),
    ("INDEX_BUILDER", "chromadb index"),
    ("SMOKE_TESTS", "basic queries"),
    ("EVALUATOR_NODE", "ragas + llm scoring"),
    ("ACCEPTANCE", "score comparison"),
    ("RECORDER", "persist results"),
    ("REFLECTION", "pattern analysis"),
]

LOG_POOL = [
    ("INIT", "sqlite wal mode enabled — db/optimizer.db"),
    ("INIT", "baseline cache hit — score=0.742"),
    ("GRAPH", "scientist: proposed chunk_size=512, overlap=64, top_k=8"),
    ("GRAPH", "validator: config within bounds — OK"),
    ("GRAPH", "deduplicator: hash 7f2a1c not seen before — UNIQUE"),
    ("GRAPH", "budget_guard: est. cost $0.34 — under ceiling"),
    ("GRAPH", "index_builder: chromadb collection rebuilt (1,204 chunks)"),
    ("GRAPH", "smoke_tests: 5/5 basic queries returned non-empty context"),
    ("EVAL", "evaluator_node: dispatching 12 eval questions to worker pool"),
    ("EVAL", "ragas: faithfulness=0.81 context_recall=0.77"),
    ("EVAL", "llm-judge: answer_relevancy=0.85"),
    ("GRAPH", "acceptance: 0.812 > baseline 0.742 — ACCEPTED"),
    ("GRAPH", "recorder: experiment #14 persisted to db"),
    ("GRAPH", "reflection: overlap>64 correlates with recall gains on this corpus"),
    ("WARN", "budget_guard: cumulative spend at 61% of ceiling"),
    ("GRAPH", "scientist: proposed top_k=12, rerank=true"),
]

TICKER_SEED = [
    ("#11", "REJECTED", "0.706", "-0.036"),
    ("#12", "REJECTED", "0.719", "-0.023"),
    ("#13", "ACCEPTED", "0.781", "+0.039"),
    ("#14", "ACCEPTED", "0.812", "+0.031"),
]


# ----------------------------------------------------------------------
# Screen 1 — Auth
# ----------------------------------------------------------------------


class AuthScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with VerticalScroll(id="auth-screen"):
            with Container(id="auth-card"):
                yield Static("user@rag-optimizer:~$ init auth", classes="prompt-line")
                yield Static("RAG · OPTIMIZER", id="wordmark")
                yield Static("autonomous overnight tuning runner — v0.4.2-nightly", id="subtitle")
                yield Static("▓▒░" * 20, id="rule")

                yield Label("PROVIDER", classes="field-label")
                with RadioSet(id="provider-set"):
                    for i, p in enumerate(PROVIDERS):
                        yield RadioButton(p, value=(i == 0))

                yield Label("API_KEY", classes="field-label")
                yield Input(
                    placeholder="sk-••••••••••••••••••••••••",
                    password=True,
                    id="api-key",
                )

                yield Label("BASE_URL  (optional — azure / local only)", classes="field-label dim")
                yield Input(placeholder="https://...", id="base-url")

                yield Static("", classes="spacer")
                yield Button("[ ENTER ]  authenticate →", id="auth-continue", variant="primary")
                yield Static(
                    "key is held in-memory for this session only. nothing is logged.",
                    id="auth-footnote",
                )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "auth-continue":
            self.app.push_screen(ModelSelectScreen())


# ----------------------------------------------------------------------
# Screen 2 — Model selection
# ----------------------------------------------------------------------


class ModelSelectScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with VerticalScroll(id="model-screen"):
            yield Static("user@rag-optimizer:~$ select models", classes="prompt-line")
            yield Static("▓▒░" * 20, id="rule")

            with Horizontal(id="model-columns"):
                with Vertical(classes="model-col"):
                    yield Label("SCIENTIST", classes="col-title")
                    yield Static("proposes rag configs each iteration", classes="col-sub")
                    with RadioSet(id="scientist-set"):
                        for i, m in enumerate(SCIENTIST_MODELS):
                            yield RadioButton(m, value=(i == 1))

                with Vertical(classes="model-col"):
                    yield Label("EVALUATOR / JUDGE", classes="col-title")
                    yield Static("ragas + llm scoring of each config", classes="col-sub")
                    with RadioSet(id="evaluator-set"):
                        for i, m in enumerate(EVALUATOR_MODELS):
                            yield RadioButton(m, value=(i == 0))

                with Vertical(classes="model-col"):
                    yield Label("EMBEDDING MODEL", classes="col-title")
                    yield Static("used by index_builder for chromadb", classes="col-sub")
                    with RadioSet(id="embedding-set"):
                        for i, m in enumerate(EMBEDDING_MODELS):
                            yield RadioButton(m, value=(i == 0))

            yield Static("▓▒░" * 20, id="rule2")
            yield Label("RUN PARAMETERS", classes="col-title")
            with Horizontal(id="run-params"):
                with Vertical(classes="param-field"):
                    yield Label("MAX_EXPERIMENTS", classes="field-label")
                    yield Input(value="40", id="max-experiments")
                with Vertical(classes="param-field"):
                    yield Label("COST_CEILING_USD", classes="field-label")
                    yield Input(value="15.00", id="cost-ceiling")
                with Vertical(classes="param-field"):
                    yield Label("TARGET_METRIC", classes="field-label")
                    yield Select(TARGET_METRICS, value="faithfulness", id="target-metric")

            yield Static("", classes="spacer")
            with Horizontal(id="model-actions"):
                yield Button("← back", id="model-back")
                yield Button(
                    "[ EXECUTE ]  launch overnight run →", id="model-launch", variant="primary"
                )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "model-launch":
            self.app.push_screen(DashboardScreen())
        elif event.button.id == "model-back":
            self.app.pop_screen()


# ----------------------------------------------------------------------
# Screen 3 — Dashboard
# ----------------------------------------------------------------------


class DashboardScreen(Screen):
    elapsed = reactive(0)
    active_idx = reactive(4)  # start mid-pipeline so the demo feels "in progress"
    experiment_no = reactive(14)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Container(id="dash"):
            # ---- top status bar ----
            with Horizontal(id="statusbar"):
                yield Static("RUN #a7f3c1", classes="stat-chip")
                yield Static("00:00:00", id="clock-chip", classes="stat-chip")
                yield Static("● RUNNING", id="status-chip", classes="stat-chip status-running")
                yield Static("COST  $4.62 / $15.00", id="cost-chip", classes="stat-chip")

            # ---- init strip ----
            with Horizontal(id="init-strip"):
                yield Static("✓ SQLITE+WAL", classes="chip chip-init")
                yield Static("✓ COST_TRACKER", classes="chip chip-init")
                yield Static("✓ CONFIG_LOADED", classes="chip chip-init")
                yield Static("✓ BASELINE 0.742", classes="chip chip-init")

            # ---- main grid: loop panel + evaluator panel ----
            with Horizontal(id="main-grid"):

                with Vertical(id="loop-panel", classes="panel panel-graph"):
                    yield Static("AUTONOMOUS LANGGRAPH LOOP", classes="panel-title")
                    yield Static("EXPERIMENT 14 / 40", id="exp-counter", classes="panel-sub")

                    with Vertical(id="node-list"):
                        for i, (name, sub) in enumerate(NODES):
                            yield Static(
                                self._node_line(i, name, sub), id=f"node-{i}", classes="node-row"
                            )

                    yield Static("ACCEPTANCE STAIRCASE", classes="panel-sub top-gap")
                    yield Static("▁▂▂▃▃▄▃▅▄▆▅▇▆█", id="staircase", classes="sparkline")

                    yield Static("RECENT RESULTS", classes="panel-sub top-gap")
                    yield RichLog(id="ticker", max_lines=6, wrap=False, markup=True)

                with Vertical(id="eval-panel", classes="panel panel-eval"):
                    yield Static("EVALUATOR PIPELINE", classes="panel-title")
                    yield Static(
                        'Q: "what is the refund window for annual plans?"',
                        id="eval-question",
                        classes="panel-sub",
                    )

                    yield Static("faithfulness      0.81", classes="metric-label")
                    yield ProgressBar(total=100, show_eta=False, id="bar-faith")
                    yield Static("context_recall    0.77", classes="metric-label")
                    yield ProgressBar(total=100, show_eta=False, id="bar-recall")
                    yield Static("answer_relevancy  0.85", classes="metric-label")
                    yield ProgressBar(total=100, show_eta=False, id="bar-relevancy")

                    yield Static("WORKER POOL (8)", classes="panel-sub top-gap")
                    with Horizontal(id="worker-pool"):
                        for i in range(8):
                            yield Static("▉", id=f"worker-{i}", classes="worker worker-idle")

                    yield Static("REFLECTION — pattern analysis", classes="panel-sub top-gap")
                    yield Static(
                        "chunk_overlap > 64 correlates with +0.03 recall\n"
                        "on this corpus. next proposals will bias upward.",
                        id="reflection-box",
                        classes="reflection-box",
                    )

            # ---- log tail ----
            yield Static("LIVE LOG", classes="panel-title log-title")
            yield RichLog(id="log-tail", max_lines=200, wrap=False, markup=True, highlight=False)

            # ---- footer stat bar ----
            with Horizontal(id="footer-stats"):
                with Vertical(classes="stat-card"):
                    yield Static("BEST SCORE", classes="stat-key")
                    yield Static("0.812", classes="stat-val stat-val-eval")
                with Vertical(classes="stat-card"):
                    yield Static("Δ vs BASELINE", classes="stat-key")
                    yield Static("+0.070", classes="stat-val stat-val-eval")
                with Vertical(classes="stat-card"):
                    yield Static("EXPERIMENTS LEFT", classes="stat-key")
                    yield Static("26", id="exp-left", classes="stat-val stat-val-graph")
                with Vertical(classes="stat-card"):
                    yield Static("BUDGET LEFT", classes="stat-key")
                    yield Static("$10.38", id="budget-left", classes="stat-val stat-val-warn")

        yield Footer()

    # -- helpers -----------------------------------------------------

    def _node_line(self, i: int, name: str, sub: str) -> str:
        if i < self.active_idx:
            icon = "✓"
        elif i == self.active_idx:
            icon = "▸"
        else:
            icon = "·"
        return f"{icon}  {name:<16} {sub}"

    def _refresh_nodes(self) -> None:
        for i, (name, sub) in enumerate(NODES):
            node = self.query_one(f"#node-{i}", Static)
            node.update(self._node_line(i, name, sub))
            node.remove_class("node-done", "node-active", "node-pending")
            if i < self.active_idx:
                node.add_class("node-done")
            elif i == self.active_idx:
                node.add_class("node-active")
            else:
                node.add_class("node-pending")

    # -- lifecycle -----------------------------------------------------

    def on_mount(self) -> None:
        self._refresh_nodes()
        self.query_one("#bar-faith", ProgressBar).update(progress=81)
        self.query_one("#bar-recall", ProgressBar).update(progress=77)
        self.query_one("#bar-relevancy", ProgressBar).update(progress=85)

        ticker = self.query_one("#ticker", RichLog)
        for eid, status, score, delta in TICKER_SEED:
            color = "eval" if status == "ACCEPTED" else "error"
            ticker.write(f"[{color}]{eid}  {status:<9}[/{color}] {score}  {delta}")

        log = self.query_one("#log-tail", RichLog)
        log.write("[dim]-- log stream attached --[/dim]")

        self.set_interval(1.0, self._tick_clock)
        self.set_interval(2.6, self._tick_pipeline)
        self.set_interval(1.7, self._tick_log)
        self.set_interval(2.2, self._tick_workers)

    def _tick_clock(self) -> None:
        self.elapsed += 1
        h, rem = divmod(self.elapsed, 3600)
        m, s = divmod(rem, 60)
        self.query_one("#clock-chip", Static).update(f"{h:02d}:{m:02d}:{s:02d}")

    def _tick_pipeline(self) -> None:
        self.active_idx = (self.active_idx + 1) % len(NODES)
        if self.active_idx == 0:
            self.experiment_no += 1
            self.query_one("#exp-counter", Static).update(f"EXPERIMENT {self.experiment_no} / 40")
        self._refresh_nodes()

    def _tick_log(self) -> None:
        tag, msg = random.choice(LOG_POOL)
        color = {"INIT": "init", "GRAPH": "graph", "EVAL": "eval", "WARN": "warn"}[tag]
        ts = datetime.now().strftime("%H:%M:%S")
        log = self.query_one("#log-tail", RichLog)
        log.write(f"[dim]{ts}[/dim]  [{color}]{tag:<5}[/{color}]  {msg}")

    def _tick_workers(self) -> None:
        for i in range(8):
            w = self.query_one(f"#worker-{i}", Static)
            active = random.random() > 0.4
            w.set_class(active, "worker-active")
            w.set_class(not active, "worker-idle")

    def on_key(self, event: events.Key) -> None:
        if event.key == "b":
            self.app.pop_screen()


# ----------------------------------------------------------------------
# App
# ----------------------------------------------------------------------


class RagOptimizerApp(App):
    TITLE = "RAG-OPT"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("b", "back", "Back"),
    ]

    CSS = """
    Screen {
        background: #0a0d0b;
        color: #d6ded4;
    }

    * {
        scrollbar-color: #3a4038;
        scrollbar-background: #10130f;
    }

    /* ---------- shared ---------- */

    .prompt-line {
        color: #6b736a;
        padding: 1 2 0 2;
    }

    .field-label {
        color: #6b736a;
        text-style: bold;
        padding: 1 2 0 2;
    }
    .field-label.dim { color: #454c44; }

    .spacer { height: 1; }

    #rule, #rule2 {
        color: #262b24;
        padding: 0 2;
    }

    Button {
        margin: 0 2;
        min-width: 30;
        background: #141813;
        color: #d6ded4;
        border: tall #3a4038;
    }
    Button:hover { background: #1b201a; }
    Button.-primary {
        background: #1b2a20;
        color: #74e0a6;
        border: tall #396b4f;
    }

    Input {
        margin: 0 2;
        background: #10130f;
        color: #d6ded4;
        border: tall #262b24;
    }
    Input:focus { border: tall #82b6e8; }

    RadioSet {
        margin: 0 2;
        background: #10130f;
        border: round #262b24;
        padding: 0 1;
    }
    RadioButton { color: #d6ded4; }

    /* ---------- auth screen ---------- */

    #auth-screen {
        align: center middle;
    }
    #auth-card {
        width: 74;
        border: round #3a4038;
        background: #10130f;
        padding: 1 0;
    }
    #wordmark {
        text-style: bold;
        color: #74e0a6;
        text-align: center;
        padding: 1 0 0 0;
    }
    #subtitle {
        color: #6b736a;
        text-align: center;
        padding: 0 0 1 0;
    }
    #auth-footnote {
        color: #454c44;
        padding: 1 2 0 2;
    }

    /* ---------- model select screen ---------- */

    #model-screen { padding: 1 2; }
    #model-columns { height: auto; padding-top: 1; }
    .model-col {
        width: 1fr;
        margin: 0 1;
    }
    .col-title {
        text-style: bold;
        color: #82b6e8;
    }
    .col-sub {
        color: #454c44;
        padding-bottom: 1;
    }
    #run-params { height: auto; padding-top: 1; }
    .param-field { width: 1fr; margin: 0 1; }
    #model-actions { padding-top: 1; height: auto; }
    Select { margin: 0 2; }

    /* ---------- dashboard ---------- */

    #dash { padding: 0 1; }

    #statusbar {
        height: 3;
        background: #10130f;
        border: round #262b24;
        padding: 0 1;
    }
    .stat-chip {
        content-align: center middle;
        width: 1fr;
        color: #d6ded4;
    }
    .status-running { color: #74e0a6; text-style: bold; }

    #init-strip { height: 3; padding: 1 0; }
    .chip {
        width: auto;
        margin: 0 1;
        padding: 0 2;
        background: #14180f;
        color: #e3b78f;
        border: round #6b5847;
    }

    #main-grid { height: 1fr; }

    .panel {
        border: round #262b24;
        padding: 0 1;
        margin: 0 1 0 0;
        height: 1fr;
    }
    .panel-graph { width: 2fr; border: round #3f5468; }
    .panel-eval { width: 1fr; border: round #396b4f; }

    .panel-title {
        text-style: bold;
        color: #d6ded4;
        background: #141813;
        padding: 0 1;
    }
    .log-title { margin: 1 0 0 0; }
    .panel-sub { color: #6b736a; padding: 1 0 0 0; }
    .top-gap { padding-top: 1; }

    #node-list { padding-top: 1; height: auto; }
    .node-row { padding: 0 1; }
    .node-done { color: #396b4f; }
    .node-active { color: #82b6e8; text-style: bold; }
    .node-pending { color: #454c44; }

    .sparkline { color: #74e0a6; padding-top: 0; }

    #ticker { height: 8; border: round #262b24; margin-top: 0; }

    .metric-label { color: #6b736a; padding-top: 1; }
    ProgressBar { width: 1fr; }
    ProgressBar > .bar--bar { color: #74e0a6; }
    ProgressBar > .bar--complete { color: #396b4f; }

    #worker-pool { height: 3; padding-top: 1; }
    .worker { width: 3; content-align: center middle; }
    .worker-active { color: #74e0a6; }
    .worker-idle { color: #262b24; }

    .reflection-box {
        color: #d6ded4;
        background: #10130f;
        border: round #396b4f;
        padding: 1;
        margin-top: 1;
    }

    #log-tail {
        height: 10;
        border: round #262b24;
        margin-top: 0;
    }

    #footer-stats { height: 5; padding-top: 1; }
    .stat-card {
        width: 1fr;
        border: round #262b24;
        margin: 0 1 0 0;
        align: center middle;
    }
    .stat-key { color: #454c44; text-align: center; width: 100%; }
    .stat-val { text-style: bold; text-align: center; width: 100%; }
    .stat-val-eval { color: #74e0a6; }
    .stat-val-graph { color: #82b6e8; }
    .stat-val-warn { color: #e8c468; }
    """

    def on_mount(self) -> None:
        self.push_screen(AuthScreen())

    def action_back(self) -> None:
        if len(self.screen_stack) > 1:
            self.pop_screen()


if __name__ == "__main__":
    RagOptimizerApp().run()
