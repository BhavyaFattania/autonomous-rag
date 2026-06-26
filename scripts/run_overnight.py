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
import sys
import subprocess
from pathlib import Path

def _ensure_venv():
    in_venv = sys.prefix != sys.base_prefix or hasattr(sys, "real_prefix")
    if not in_venv:
        project_root = Path(__file__).resolve().parent.parent
        if sys.platform.startswith("win"):
            venv_python = project_root / "venv" / "Scripts" / "python.exe"
        else:
            venv_python = project_root / "venv" / "bin" / "python"
        if venv_python.exists():
            # Re-execute this script using the venv python interpreter
            args = [str(venv_python)] + sys.argv
            sys.exit(subprocess.call(args))

_ensure_venv()

import asyncio
import signal
import uuid
from datetime import datetime, timezone

# Ensure project root is in path so 'src' module can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import click
from dotenv import load_dotenv

from rich.rule import Rule

from src.orchestrator.overnight_display import (
    console, print_banner, log_event,
)
from src.orchestrator.overnight_eval import empty_metrics, evaluate_baseline, evaluate_final_best

load_dotenv()

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

_stop_requested = False

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
    from src.storage.database import Database
    from src.storage.cost_tracker import initialize as init_cost
    from src.utils.config_loader import load_run_settings
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

    print_banner(max_exp, max_hours, settings)
    asyncio.run(_run(max_exp, max_hours, resume, settings))


# ─── Run loop ─────────────────────────────────────────────────────────────────

async def _run(max_exp, max_hours, resume, settings):
    from src.storage.database import Database
    from src.orchestrator.graph import build_graph
    from src.utils.config_loader import load_baseline_config
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
    from src.storage.cost_tracker import get_total
    from src.storage.repositories.run_repository import RunRepository

    await Database().init()

    run_id = None
    if resume:
        try:
            run_id = await RunRepository().find_last_run_id()
            if run_id:
                console.print(f"[bold yellow]Resuming previous run with ID: {run_id}[/]")
        except Exception as e:
            console.print(f"[bold red]Failed to fetch last run ID for resume: {e}[/]")

    if not run_id:
        run_id = str(uuid.uuid4())

    baseline = load_baseline_config()
    run_start = datetime.now(timezone.utc)
    baseline_override = settings["evaluation"].get("baseline_score_override")
    if baseline_override is not None:
        baseline_score = float(baseline_override)
        baseline_metrics = empty_metrics()
        console.print(Rule("[bold cyan]Phase 0 baseline override[/]"))
        console.print(f"[bold yellow]Starting baseline score overridden to {baseline_score:.4f}[/]")
    else:
        baseline_score, baseline_metrics = await evaluate_baseline(baseline, settings)

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
        "total_cost_usd":            get_total(),
        "experiments_completed":     0,
        "experiments_accepted":      0,
        "consecutive_failures":      0,
        "experiments_repeated":      0,
        "experiments_competitive":   0,
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

        try:
            from langfuse.langchain import CallbackHandler
            langfuse_handler = CallbackHandler()
            callbacks = [langfuse_handler]
        except ImportError:
            callbacks = []

        graph_config = {
            "configurable": {"thread_id": run_id},
            "recursion_limit": max(100, (max_exp * 12) + 50),
            "callbacks": callbacks,
        }

        state_exists = False
        if resume:
            try:
                state_val = await graph.aget_state(graph_config)
                if state_val and state_val.values:
                    state_exists = True
                    console.print(f"[bold green]Found active checkpoint for run {run_id}. Resuming...[/]")
                    previous_cost = state_val.values.get("total_cost_usd", 0.0)
                    from src.storage.cost_tracker import initialize as init_cost
                    init_cost(
                        hard_ceiling=settings["run"]["cost_hard_ceiling_usd"],
                        warning_threshold=settings["run"]["cost_warning_threshold_usd"],
                        start_cost=previous_cost
                    )
                    await graph.aupdate_state(
                        graph_config,
                        {"max_experiments": max_exp, "max_hours": max_hours},
                    )
            except Exception as e:
                console.print(f"[bold red]Error loading checkpoint: {e}[/]")

        state_to_stream = None if state_exists else initial_state
        async for event in graph.astream(state_to_stream, config=graph_config):
            if _stop_requested:
                console.print(Rule("[bold yellow]Run paused by user[/]"))
                break
            for output in event.values():
                if isinstance(output, dict):
                    latest_state.update(output)
            log_event(event, _ctx, run_start)

    if settings["evaluation"].get("run_final_best_eval", False) and not _stop_requested:
        await evaluate_final_best(latest_state, settings)




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
