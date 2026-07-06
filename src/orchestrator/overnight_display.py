from datetime import UTC, datetime

from rich import box
from rich.console import Console
from rich.padding import Padding
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

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


def log_event(event: dict, ctx: dict, run_start: datetime):
    from src.storage.cost_tracker import get_total

    for node_name, output in event.items():
        if not isinstance(output, dict):
            continue

        emoji, style, description = NODE_META.get(node_name, ("--", "white", node_name))
        status = output.get("status", "?")
        status_style, status_icon = STATUS_STYLE.get(status, ("white", "?"))
        total_cost = get_total()
        elapsed = (datetime.now(UTC) - run_start).total_seconds()

        if node_name == "scientist":
            ctx["exp_num"] += 1
            console.print()
            console.print(
                Rule(
                    f"[bold cyan]Experiment #{ctx['exp_num']}[/]  [dim]{fmt_elapsed(elapsed)}[/]",
                    style="cyan",
                )
            )

            hypothesis = output.get("hypothesis", "")
            if hypothesis:
                console.print(Padding(f"[bold]Hypothesis:[/] [italic]{hypothesis}[/]", (0, 2)))
            reasoning = output.get("scientist_reasoning", "")
            if reasoning:
                console.print(
                    Padding(f"[bold dim]Scientist reasoning:[/] [dim]{reasoning}[/]", (0, 2))
                )

            config = output.get("proposed_config", {})
            if config:
                print_config_table(config)

        node_label = Text()
        node_label.append(f"  {emoji}  ", style=style)
        node_label.append(f"{node_name:<16}", style=f"bold {style}")
        node_label.append(f" {status_icon} ", style=status_style)
        node_label.append(f"{status:<22}", style=status_style)
        node_label.append(f"  cost ${total_cost:.4f}", style="dim green")

        failure = output.get("failure_reason", "")
        if failure:
            node_label.append(f"  warn {failure[:80]}", style="bold red")

        console.print(node_label)

        metrics = output.get("aggregated_metrics", {})
        if metrics and node_name in ("acceptance", "evaluator"):
            print_metrics(
                metrics,
                output.get("proposed_weighted_score", 0.0),
                output.get("current_best_weighted_score", 0.0),
            )

        if node_name == "recorder":
            completed = output.get("experiments_completed", 0)
            accepted = output.get("experiments_accepted", 0)
            failures = output.get("consecutive_failures", 0)
            repeated = output.get("experiments_repeated", 0)
            competitive = output.get("experiments_competitive", 0)
            console.print(
                f"  [dim]Completed: [white]{completed}[/]  "
                f"Accepted: [green]{accepted}[/]  "
                f"Competitive: [cyan]{competitive}[/]  "
                f"Repeated: [blue]{repeated}[/]  "
                f"Consecutive failures: [yellow]{failures}[/][/]"
            )


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
