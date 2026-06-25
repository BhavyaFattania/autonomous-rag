import asyncio
import json
from pathlib import Path

from rich.rule import Rule

from src.data.question_loader import load_eval_question_items
from src.models.rag_config import RAGConfig
from src.models.metrics import AggregatedMetrics
from src.evaluator.ragas_runner import run_single_eval
from src.rag_pipeline.pipeline import retrieve_results
from src.utils.hashing import get_config_hash
from src.orchestrator.overnight_display import console, print_metrics

CACHE_DIR = Path("data/eval_cache")


def empty_metrics() -> dict:
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


async def evaluate_baseline(baseline: dict, settings: dict) -> tuple[float, dict]:
    console.print(Rule("[bold cyan]Phase 0 baseline evaluation[/]"))
    config = RAGConfig(**baseline)
    n_questions = settings["evaluation"]["n_questions"]
    n_runs = settings["evaluation"].get("n_eval_runs", 3)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_key = get_config_hash({
        "phase": "baseline",
        "scoring_version": "ir_plus_ragas_context_v4_cached_only",
        "config": baseline,
        "n_questions": n_questions,
        "n_runs": n_runs,
        "ragas_metrics": settings["evaluation"].get("ragas_metrics", ["context_recall"]),
        "ragas_audit_every_n_experiments": settings["evaluation"].get("ragas_audit_every_n_experiments", 5),
    })
    cache_path = CACHE_DIR / f"{cache_key}.json"
    if cache_path.exists():
        data = json.loads(cache_path.read_text(encoding="utf-8"))
        console.print(f"[bold green]Baseline cache hit: {data['median_weighted_score']:.4f}[/]")
        return data["median_weighted_score"], data["best_metrics"]

    question_items = load_eval_question_items(n=n_questions)
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
            questions, None, contexts, ground_truths,
            retrieval_results=results, question_ids=question_ids,
            supporting_titles=supporting_titles, run_ragas=False,
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
        json.dumps({"median_weighted_score": aggregated.median_weighted_score, "best_metrics": best_metrics}, indent=2),
        encoding="utf-8",
    )
    return aggregated.median_weighted_score, best_metrics


async def evaluate_final_best(state: dict, settings: dict) -> None:
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
    question_items = load_eval_question_items(n=n_questions)
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
            questions, None, contexts, ground_truths,
            retrieval_results=results, question_ids=question_ids,
            supporting_titles=supporting_titles, run_ragas=True,
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
    print_metrics(
        aggregated.model_dump(),
        aggregated.median_weighted_score,
        state.get("current_best_weighted_score", 0.0),
    )
