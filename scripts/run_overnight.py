#!/usr/bin/env python3
"""
Entry point for an overnight run.

Usage:
    python scripts/run_overnight.py --max-exp 20 --max-hours 6
    python scripts/run_overnight.py --max-exp 4 --max-hours 2  # daytime test run
    python scripts/run_overnight.py --dry-run                   # validate env only

Signal handling:
    SIGTERM or Ctrl+C: gracefully pauses after current experiment completes.
    The SQLite checkpoint allows resuming with the same command.
"""

import asyncio
import signal
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone

# Ensure project root is in path so 'src' module can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.rule import Rule
from rich import box
from rich.columns import Columns
from rich.padding import Padding
from rich.style import Style

load_dotenv()

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

console = Console()

_stop_requested = False

# ─── ANSI / Node metadata ────────────────────────────────────────────────────

NODE_META = {
    "scientist":     ("AI", "bold cyan",    "Proposing config"),
    "validator":     ("OK", "bold yellow",  "Validating config"),
    "deduplicator":  ("DU", "bold blue",    "Checking duplicates"),
    "budget_guard":  ("$$", "bold magenta", "Checking budget"),
    "indexer":       ("IX", "bold white",   "Building index"),
    "smoke_test":    ("ST", "bold white",   "Running smoke test"),
    "evaluator":     ("EV", "bold green",   "Evaluating RAG"),
    "acceptance":    ("AC", "bold green",   "Scoring & accepting"),
    "recorder":      ("DB", "bold blue",    "Recording experiment"),
    "reflection":    ("RF", "bold cyan",    "Reflecting on results"),
    "report_writer": ("RP", "bold white",   "Writing final report"),
}

STATUS_STYLE = {
    "RUNNING":            ("bold green",   "*"),
    "PENDING":            ("bold yellow",  "o"),
    "ACCEPTED":           ("bold green",   "+"),
    "COMPETITIVE":        ("bold cyan",    "~"),
    "REJECTED":           ("bold yellow",  "-"),
    "FAILED_SMOKE":       ("bold red",     "x"),
    "FAILED_TIMEOUT":     ("bold red",     "T"),
    "FAILED_DUPLICATE":   ("dim yellow",   "="),
    "FAILED_VALIDATION":  ("bold red",     "!"),
    "FAILED_API_ERROR":   ("bold red",     "x"),
    "BUDGET_EXCEEDED":    ("bold magenta", "$"),
    "INTERRUPTED":        ("bold yellow",  "!"),
}

def _handle_signal(sig, frame):
    global _stop_requested
    console.print("\n[bold yellow]Signal received. Finishing current experiment then stopping...[/]")
    _stop_requested = True

signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT, _handle_signal)


# ─── CLI ─────────────────────────────────────────────────────────────────────

@click.command()
@click.option("--max-exp",   default=20,  type=int,   help="Max experiments to run")
@click.option("--max-hours", default=6.0, type=float, help="Max runtime in hours")
@click.option("--dry-run",   is_flag=True,             help="Validate environment, print config, exit")
@click.option("--resume",    is_flag=True,             help="Resume from last checkpoint")
def main(max_exp, max_hours, dry_run, resume):
    from src.storage.db import init_db
    from src.storage.cost_tracker import initialize as init_cost
    from src.orchestrator.config_loader import load_run_settings
    from src.utils.logger import setup_logging

    setup_logging()

    if dry_run:
        _validate_environment()
        return

    settings = load_run_settings()
    init_cost(
        hard_ceiling=settings["run"]["cost_hard_ceiling_usd"],
        warning_threshold=settings["run"]["cost_warning_threshold_usd"],
    )

    _print_banner(max_exp, max_hours, settings)
    asyncio.run(_run(max_exp, max_hours, resume, settings))


# ─── Run loop ─────────────────────────────────────────────────────────────────

async def _run(max_exp, max_hours, resume, settings):
    from src.storage.db import init_db
    from src.orchestrator.graph import build_graph
    from src.orchestrator.config_loader import load_baseline_config
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

    await init_db()

    run_id = str(uuid.uuid4())
    baseline = load_baseline_config()
    run_start = datetime.now(timezone.utc)
    baseline_override = settings["evaluation"].get("baseline_score_override")
    if baseline_override is not None:
        baseline_score = float(baseline_override)
        baseline_metrics = _empty_metrics()
        console.print(Rule("[bold cyan]Phase 0 baseline override[/]"))
        console.print(f"[bold yellow]Starting baseline score overridden to {baseline_score:.4f}[/]")
    else:
        baseline_score, baseline_metrics = await _evaluate_baseline(baseline, settings)

    initial_state = {
        "run_id":                    run_id,
        "experiment_id":             0,
        "experiment_uuid":           "",
        "baseline_config":           baseline,
        "current_best_config":       baseline,
        "proposed_config":           {},
        "validated_config":          {},
        "hypothesis":                "",
        "scientist_reasoning":       "",
        "reflection_summary":        "",
        "eval_results":              [],
        "aggregated_metrics":        {},
        "current_best_weighted_score": baseline_score,
        "current_best_metrics":      baseline_metrics,
        "proposed_weighted_score":   0.0,
        "status":                    "PENDING",
        "failure_reason":            "",
        "experiment_cost_usd":       0.0,
        "total_cost_usd":            0.0,
        "experiments_completed":     0,
        "experiments_accepted":      0,
        "consecutive_failures":      0,
        "successful_patterns":       [],
        "failed_patterns":           [],
        "run_started_at":            run_start.isoformat(),
        "experiment_started_at":     "",
        "max_experiments":           max_exp,
        "max_hours":                 max_hours,
    }

    settings["run"]["max_experiments"] = max_exp
    settings["run"]["max_hours"] = max_hours

    # Track per-experiment state across events
    _ctx = {"exp_num": 0, "node_times": {}}
    latest_state = dict(initial_state)

    async with AsyncSqliteSaver.from_conn_string("experiments.sqlite") as memory:
        graph = build_graph(checkpointer=memory)
        graph_config = {
            "configurable": {"thread_id": run_id},
            "recursion_limit": max(100, (max_exp * 12) + 50),
        }

        async for event in graph.astream(initial_state, config=graph_config):
            if _stop_requested:
                console.print(Rule("[bold yellow]Run paused by user[/]"))
                break
            for output in event.values():
                if isinstance(output, dict):
                    latest_state.update(output)
            _log_event(event, _ctx, run_start)

    if settings["evaluation"].get("run_final_best_eval", False) and not _stop_requested:
        await _evaluate_final_best(latest_state, settings)


def _empty_metrics() -> dict:
    return {
        "faithfulness": 0.0,
        "answer_relevancy": 0.0,
        "context_recall": 0.0,
        "context_precision": 0.0,
        "context_utilization": 0.0,
        "recall_at_k": 0.0,
        "precision_at_k": 0.0,
        "ndcg_at_k": 0.0,
        "mrr": 0.0,
    }


async def _evaluate_baseline(baseline: dict, settings: dict) -> tuple[float, dict]:
    from src.models.rag_config import RAGConfig
    from src.models.metrics import AggregatedMetrics
    from src.evaluator.ragas_runner import run_single_eval, _load_eval_question_items
    from src.rag_pipeline.pipeline import retrieve_results
    from src.utils.hashing import get_config_hash
    import json

    console.print(Rule("[bold cyan]Phase 0 baseline evaluation[/]"))
    config = RAGConfig(**baseline)
    n_questions = settings["evaluation"]["n_questions"]
    n_runs = settings["evaluation"].get("n_eval_runs", 3)
    cache_dir = Path("data/eval_cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_key = get_config_hash({
        "phase": "baseline",
        "scoring_version": "ir_plus_ragas_context_v4_cached_only",
        "config": baseline,
        "n_questions": n_questions,
        "n_runs": n_runs,
        "ragas_metrics": settings["evaluation"].get("ragas_metrics", ["context_recall"]),
        "ragas_audit_every_n_experiments": settings["evaluation"].get("ragas_audit_every_n_experiments", 5),
    })
    cache_path = cache_dir / f"{cache_key}.json"
    if cache_path.exists():
        data = json.loads(cache_path.read_text(encoding="utf-8"))
        console.print(f"[bold green]Baseline cache hit: {data['median_weighted_score']:.4f}[/]")
        return data["median_weighted_score"], data["best_metrics"]

    question_items = _load_eval_question_items(n=n_questions)
    question_ids = [item["id"] for item in question_items]
    questions = [item["question"] for item in question_items]
    ground_truths = [item["answer"] for item in question_items]
    supporting_titles = [item.get("supporting_titles", []) for item in question_items]
    if not any(supporting_titles):
        console.print(
            "[bold yellow]Warning:[/] questions.jsonl has no supporting_titles; "
            "IR scores use answer-string fallback and may be inflated."
        )
    runs = []

    for run_num in range(1, n_runs + 1):
        results, _ = await asyncio.wait_for(
            retrieve_results(config, questions),
            timeout=settings["evaluation"]["max_runtime_sec_per_eval"],
        )
        contexts = [[item.get("text", "") for item in items] for items in results]
        metrics = await run_single_eval(
            questions,
            None,
            contexts,
            ground_truths,
            retrieval_results=results,
            question_ids=question_ids,
            supporting_titles=supporting_titles,
            run_ragas=False,
            timeout_sec=settings["evaluation"].get("max_runtime_sec_per_ragas", 120),
            metrics=settings["evaluation"].get("ragas_metrics"),
        )
        runs.append(metrics)
        console.print(f"  Baseline run {run_num}: weighted={metrics.weighted_score:.4f}")

    aggregated = AggregatedMetrics.from_runs(runs)
    best_metrics = {
        "faithfulness": aggregated.median_faithfulness,
        "answer_relevancy": aggregated.median_answer_relevancy,
        "context_recall": aggregated.median_context_recall,
        "context_precision": aggregated.median_context_precision,
        "context_utilization": aggregated.median_context_utilization,
        "recall_at_k": aggregated.median_recall_at_k,
        "precision_at_k": aggregated.median_precision_at_k,
        "ndcg_at_k": aggregated.median_ndcg_at_k,
        "mrr": aggregated.median_mrr,
    }
    console.print(f"[bold green]Baseline median score: {aggregated.median_weighted_score:.4f}[/]")
    cache_path.write_text(
        json.dumps({
            "median_weighted_score": aggregated.median_weighted_score,
            "best_metrics": best_metrics,
        }, indent=2),
        encoding="utf-8",
    )
    return aggregated.median_weighted_score, best_metrics


async def _evaluate_final_best(state: dict, settings: dict) -> None:
    from src.models.rag_config import RAGConfig
    from src.models.metrics import AggregatedMetrics
    from src.evaluator.ragas_runner import run_single_eval, _load_eval_question_items
    from src.rag_pipeline.pipeline import retrieve_results

    best_config = state.get("current_best_config") or state.get("baseline_config")
    if not best_config:
        console.print("[bold yellow]No best config available for final evaluation.[/]")
        return

    console.print(Rule("[bold cyan]Final best-config evaluation[/]"))
    config = RAGConfig(**best_config)
    n_questions = settings["evaluation"].get(
        "final_best_eval_n_questions",
        settings["evaluation"].get("full_eval_n_questions", settings["evaluation"]["n_questions"]),
    )
    n_runs = settings["evaluation"].get("final_best_eval_runs", settings["evaluation"].get("n_eval_runs", 1))
    question_items = _load_eval_question_items(n=n_questions)
    question_ids = [item["id"] for item in question_items]
    questions = [item["question"] for item in question_items]
    ground_truths = [item["answer"] for item in question_items]
    supporting_titles = [item.get("supporting_titles", []) for item in question_items]

    runs = []
    for run_num in range(1, n_runs + 1):
        results, _ = await asyncio.wait_for(
            retrieve_results(config, questions),
            timeout=settings["evaluation"]["max_runtime_sec_per_eval"],
        )
        contexts = [[item.get("text", "") for item in items] for items in results]
        metrics = await run_single_eval(
            questions,
            None,
            contexts,
            ground_truths,
            retrieval_results=results,
            question_ids=question_ids,
            supporting_titles=supporting_titles,
            run_ragas=True,
            timeout_sec=settings["evaluation"].get("max_runtime_sec_per_ragas", 120),
            timeout_backoff_factor=settings["evaluation"].get("ragas_timeout_backoff_factor", 2.0),
            max_timeout_sec=settings["evaluation"].get("ragas_max_timeout_sec", 240),
            timeout_retries=settings["evaluation"].get("ragas_timeout_retries", 1),
            metrics=settings["evaluation"].get("ragas_metrics"),
        )
        runs.append(metrics)
        console.print(f"  Final eval run {run_num}: weighted={metrics.weighted_score:.4f}")

    aggregated = AggregatedMetrics.from_runs(runs)
    console.print(f"[bold green]Final best weighted score: {aggregated.median_weighted_score:.4f}[/]")
    _print_metrics(
        aggregated.model_dump(),
        aggregated.median_weighted_score,
        state.get("current_best_weighted_score", 0.0),
    )


# ─── Rich display ─────────────────────────────────────────────────────────────

def _print_banner(max_exp: int, max_hours: float, settings: dict):
    console.print()
    console.print(Panel.fit(
        "[bold cyan]Autonomous RAG Optimizer[/]\n"
        f"[dim]Max experiments: [white]{max_exp}[/]  |  "
        f"Max hours: [white]{max_hours}h[/]  |  "
        f"Budget ceiling: [white]${settings['run']['cost_hard_ceiling_usd']:.2f}[/][/]",
        border_style="cyan",
        padding=(0, 2),
    ))
    console.print()


def _log_event(event: dict, ctx: dict, run_start: datetime):
    for node_name, output in event.items():
        if not isinstance(output, dict):
            continue

        emoji, style, description = NODE_META.get(node_name, ("--", "white", node_name))
        status = output.get("status", "?")
        status_style, status_icon = STATUS_STYLE.get(status, ("white", "?"))
        total_cost = output.get("total_cost_usd", 0.0)
        elapsed = (datetime.now(timezone.utc) - run_start).total_seconds()

        # Print a separator when scientist fires (new experiment)
        if node_name == "scientist":
            ctx["exp_num"] += 1
            console.print()
            console.print(Rule(
                f"[bold cyan]Experiment #{ctx['exp_num']}[/]  [dim]{_fmt_elapsed(elapsed)}[/]",
                style="cyan"
            ))

            # Print the hypothesis if present
            hypothesis = output.get("hypothesis", "")
            if hypothesis:
                console.print(Padding(
                    f"[bold]Hypothesis:[/] [italic]{hypothesis}[/]",
                    (0, 2)
                ))
            reasoning = output.get("scientist_reasoning", "")
            if reasoning:
                console.print(Padding(
                    f"[bold dim]Scientist reasoning:[/] [dim]{reasoning}[/]",
                    (0, 2)
                ))

            # Print the proposed config if present
            config = output.get("proposed_config", {})
            if config:
                _print_config_table(config)

        # Node status line
        node_label = Text()
        node_label.append(f"  {emoji}  ", style=style)
        node_label.append(f"{node_name:<16}", style=f"bold {style}")
        node_label.append(f" {status_icon} ", style=status_style)
        node_label.append(f"{status:<22}", style=status_style)
        node_label.append(f"  cost ${total_cost:.4f}", style="dim green")

        # Append failure reason inline
        failure = output.get("failure_reason", "")
        if failure:
            node_label.append(f"  warn {failure[:80]}", style="bold red")

        console.print(node_label)

        # Print eval metrics when evaluator/acceptance fires
        metrics = output.get("aggregated_metrics", {})
        if metrics and node_name in ("acceptance", "evaluator"):
            _print_metrics(metrics, output.get("proposed_weighted_score", 0.0),
                           output.get("current_best_weighted_score", 0.0))

        # Summary line after recorder
        if node_name == "recorder":
            completed = output.get("experiments_completed", 0)
            accepted = output.get("experiments_accepted", 0)
            failures = output.get("consecutive_failures", 0)
            console.print(
                f"  [dim]Completed: [white]{completed}[/]  "
                f"Accepted: [green]{accepted}[/]  "
                f"Consecutive failures: [yellow]{failures}[/][/]"
            )


def _print_config_table(config: dict):
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold dim",
                  padding=(0, 1), border_style="dim")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="white")
    for k, v in config.items():
        if v is None:
            table.add_row(k, "[dim]None[/]")
        else:
            table.add_row(k, str(v))
    console.print(Padding(table, (0, 4)))


def _print_metrics(metrics: dict, proposed: float, best: float):
    delta = proposed - best
    delta_str = f"+{delta:.4f}" if delta >= 0 else f"{delta:.4f}"
    delta_style = "bold green" if delta >= 0 else "bold red"

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold dim",
                  padding=(0, 1), border_style="dim")
    table.add_column("Metric", style="cyan")
    table.add_column("Score", style="white", justify="right")

    for k, v in metrics.items():
        if isinstance(v, float):
            table.add_row(k, f"{v:.4f}")

    table.add_row("-" * 12, "-" * 8)
    table.add_row("[bold]Weighted Score[/]", f"[bold]{proposed:.4f}[/]")
    table.add_row("vs Best", f"[{delta_style}]{delta_str}[/]")

    console.print(Padding(table, (0, 4)))


def _fmt_elapsed(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


# ─── Dry-run validation ───────────────────────────────────────────────────────

def _validate_environment():
    import os
    required = ["OPENROUTER_API_KEY"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        console.print(f"[bold red]x Missing environment variables: {missing}[/]")
        sys.exit(1)
    console.print("[bold green]+[/] Environment variables present.")
    data_path = Path("data/hotpotqa/questions.jsonl")
    if not data_path.exists():
        console.print(f"[bold red]x {data_path} not found. Run: python data/hotpotqa/setup_hotpotqa.py[/]")
        sys.exit(1)
    console.print("[bold green]+[/] HotpotQA data present.")
    console.print("[bold green]+[/] Dry run passed. Safe to run overnight.")


if __name__ == "__main__":
    main()
