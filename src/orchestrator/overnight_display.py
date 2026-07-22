"""Rich terminal UI utilities for live workflow event display and experiment metrics visualization."""

from rich import box
from rich.console import Console
from rich.padding import Padding
from rich.table import Table

console = Console()

NODE_META = {
    "scientist": ("AI", "bold cyan", "Proposing config"),
    "validator": ("OK", "bold yellow", "Validating config"),
    "deduplicator": ("DU", "bold blue", "Checking duplicates"),
    "budget_guard": ("$$", "bold magenta", "Checking budget"),
    "indexer": ("IX", "bold white", "Building index"),
    "smoke_test": ("ST", "bold white", "Running smoke test"),
    "evaluator": ("EV", "bold green", "Evaluating RAG"),
    "acceptance": ("AC", "bold green", "Scoring & accepting"),
    "recorder": ("DB", "bold blue", "Recording experiment"),
    "reflection": ("RF", "bold cyan", "Reflecting on results"),
    "report_writer": ("RP", "bold white", "Writing final report"),
}

STATUS_STYLE = {
    "RUNNING": ("bold green", "*"),
    "PENDING": ("bold yellow", "o"),
    "ACCEPTED": ("bold green", "+"),
    "COMPETITIVE": ("bold cyan", "~"),
    "REJECTED": ("bold yellow", "-"),
    "FAILED_SMOKE": ("bold red", "x"),
    "FAILED_TIMEOUT": ("bold red", "T"),
    "FAILED_DUPLICATE": ("dim yellow", "="),
    "FAILED_VALIDATION": ("bold red", "!"),
    "FAILED_API_ERROR": ("bold red", "x"),
    "BUDGET_EXCEEDED": ("bold magenta", "$"),
    "INTERRUPTED": ("bold yellow", "!"),
}


def print_banner(max_exp: int, max_hours: float, settings):
    console.print()
    from rich.panel import Panel as RichPanel

    ceiling = settings.run.cost_hard_ceiling_usd
    console.print(
        RichPanel.fit(
            "[bold cyan]Autonomous RAG Optimizer[/]\n"
            f"[dim]Max experiments: [white]{max_exp}[/]  |  "
            f"Max hours: [white]{max_hours}h[/]  |  "
            f"Budget ceiling: [white]${ceiling:.2f}[/][/]",
            border_style="cyan",
            padding=(0, 2),
        )
    )
    console.print()


def print_config_table(config: dict):

    table = Table(
        box=box.SIMPLE,
        show_header=True,
        header_style="bold dim",
        padding=(0, 1),
        border_style="dim",
    )
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="white")
    for k, v in config.items():
        if v is None:
            table.add_row(k, "[dim]None[/]")
        else:
            table.add_row(k, str(v))
    console.print(Padding(table, (0, 4)))


def print_metrics(metrics: dict, proposed: float, best: float):
    delta = proposed - best
    delta_str = f"+{delta:.4f}" if delta >= 0 else f"{delta:.4f}"
    delta_style = "bold green" if delta >= 0 else "bold red"

    table = Table(
        box=box.SIMPLE,
        show_header=True,
        header_style="bold dim",
        padding=(0, 1),
        border_style="dim",
    )
    table.add_column("Metric", style="cyan")
    table.add_column("Score", style="white", justify="right")

    for k, v in metrics.items():
        if isinstance(v, float):
            table.add_row(k, f"{v:.4f}")

    table.add_row("-" * 12, "-" * 8)
    table.add_row("[bold]Weighted Score[/]", f"[bold]{proposed:.4f}[/]")
    table.add_row("vs Best", f"[{delta_style}]{delta_str}[/]")

    console.print(Padding(table, (0, 4)))


def fmt_elapsed(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"
