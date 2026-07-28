"""RAGAS evaluation orchestration and IR metric computation.

Runs full evaluation pipeline: IR metrics (recall/precision/NDCG) + RAGAS metrics (faithfulness/relevancy).
Handles timeouts with exponential backoff and worker scaling.
"""

import asyncio
import time

from config.loader import load_env, load_model_routing
from datasets import Dataset
from ragas import evaluate as ragas_evaluate
from ragas.run_config import RunConfig

from src.evaluator.ir_metrics import evaluate_ir_metrics
from src.evaluator.ragas_setup import build_ragas_embeddings, build_ragas_llm, build_ragas_metrics
from src.models.metrics import SingleRunMetrics
from src.rag_pipeline.pipeline import contexts_to_results
from src.utils.logger import get_logger

log = get_logger("evaluator")


def _safe_mean(df, column: str) -> float:
    """Extract mean of column from pandas DataFrame, returning 0.0 if missing or NaN."""
    if column not in df:
        return 0.0
    value = df[column].mean()
    if value != value:
        return 0.0
    return float(value)


def _all_rows_failed(df, column: str) -> bool:
    """True when every row for this metric is NaN (the judge never produced a
    single valid score) rather than a mix that happens to average out."""
    if column not in df or len(df) == 0:
        return False
    return bool(df[column].isna().all())


def _metric_availability_warning(df, metric_names: list[str], questions: int) -> str | None:
    """Describe judge metrics that RAGAS could not score without failing the run."""
    all_failed = [name for name in metric_names if _all_rows_failed(df, name)]
    partial_failed = [
        name
        for name in metric_names
        if name in df and name not in all_failed and bool(df[name].isna().any())
    ]
    if not all_failed and not partial_failed:
        return None

    details = []
    if all_failed:
        details.append(f"no usable scores for {', '.join(all_failed)}")
    if partial_failed:
        details.append(f"partial scoring failures for {', '.join(partial_failed)}")
    return (
        f"RAGAS judge warning across {questions} question(s): {'; '.join(details)}. "
        "Unavailable values are represented as 0.0 and must not be interpreted as quality scores."
    )


async def run_single_eval(
    questions: list[str],
    answers: list[str] | None,
    contexts: list[list[str]],
    ground_truths: list[str],
    retrieval_results: list[list[dict]] | None = None,
    question_ids: list[str] | None = None,
    supporting_titles: list[list[str]] | None = None,
    run_ragas: bool = True,
    ragas_min_fast_score: float | None = None,
    timeout_sec: int = 120,
    timeout_backoff_factor: float = 2.0,
    max_timeout_sec: int = 240,
    timeout_retries: int = 1,
    metrics: list[str] | None = None,
    env: dict | None = None,
    warning_messages: list[str] | None = None,
    provider=None,
) -> SingleRunMetrics:
    """Run IR metrics immediately, then conditionally run RAGAS metrics with retry logic.

    Returns early with IR-only scores if run_ragas=False and score below threshold.
    Retries with backoff and reduced worker count on timeout.
    """
    if answers is None:
        answers = ground_truths
    assert len(questions) == len(answers) == len(contexts) == len(ground_truths)
    question_ids = question_ids or [f"q_{idx}" for idx in range(len(questions))]
    retrieval_results = retrieval_results or contexts_to_results(contexts)

    ir_scores = evaluate_ir_metrics(
        question_ids=question_ids,
        retrieval_results=retrieval_results,
        ground_truths=ground_truths,
        supporting_titles=supporting_titles,
        k=max(len(items) for items in retrieval_results) if retrieval_results else 0,
    )

    fast_metrics = SingleRunMetrics(**ir_scores)
    should_run_ragas = run_ragas or (
        ragas_min_fast_score is not None and fast_metrics.weighted_score >= ragas_min_fast_score
    )
    if not should_run_ragas:
        return fast_metrics

    data = {
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    }
    dataset = Dataset.from_dict(data)
    metric_names = metrics or ["context_precision", "context_recall", "context_utilization"]
    ragas_metrics = (
        provider.build_ragas_metrics(metric_names)
        if provider
        else build_ragas_metrics(metric_names)
    )
    if not ragas_metrics:
        return fast_metrics
    ragas_llm = (
        provider.build_ragas_llm()
        if provider
        else build_ragas_llm(load_model_routing(), env=env or load_env())
    )
    ragas_embeddings = None
    if "answer_relevancy" in metric_names:
        ragas_embeddings = (
            provider.build_ragas_embeddings()
            if provider
            else build_ragas_embeddings(load_model_routing(), env=env or load_env())
        )
    loop = asyncio.get_running_loop()
    started = time.perf_counter()
    log.info("ragas_eval_start", questions=len(questions))

    result = None
    worker_count = min(3, len(questions))
    current_timeout = timeout_sec
    for attempt in range(timeout_retries + 1):
        run_config = RunConfig(
            timeout=current_timeout,
            # ragas swallows every per-job exception (raise_exceptions=False below)
            # into a NaN row instead of raising, so it never reaches the
            # `except TimeoutError` below — max_retries=0 previously disabled
            # the only retry mechanism that can actually see those errors
            # (ragas's own internal tenacity retry, which covers any Exception
            # including transient APIConnectionError, not just timeouts).
            max_retries=2,
            max_wait=5,
            max_workers=worker_count,
        )

        def _run_evaluate(loop_for_thread, cfg):
            asyncio.set_event_loop(loop_for_thread)
            return ragas_evaluate(
                dataset=dataset,
                metrics=ragas_metrics,
                llm=ragas_llm,
                embeddings=ragas_embeddings,
                run_config=cfg,
                raise_exceptions=False,
                show_progress=False,
                batch_size=8,
            )

        try:
            worker_loop = asyncio.new_event_loop()
            result = await loop.run_in_executor(None, _run_evaluate, worker_loop, run_config)
            break
        except TimeoutError:
            if attempt >= timeout_retries:
                raise
            next_timeout = min(int(current_timeout * timeout_backoff_factor), max_timeout_sec)
            next_workers = max(1, worker_count - 1)
            log.warning(
                "ragas_eval_retry_after_timeout",
                attempt=attempt + 1,
                timeout_sec=current_timeout,
                next_timeout_sec=next_timeout,
                workers=worker_count,
                next_workers=next_workers,
            )
            current_timeout = next_timeout
            worker_count = next_workers

    log.info("ragas_eval_complete", elapsed_sec=round(time.perf_counter() - started, 2))

    assert result is not None, "result should be set if we reach here"
    df = result.to_pandas()
    availability_warning = _metric_availability_warning(df, metric_names, len(questions))
    if availability_warning:
        log.warning("ragas_judge_metrics_unavailable", warning=availability_warning)
        if warning_messages is not None:
            warning_messages.append(availability_warning)

    metric_values = {
        name: _safe_mean(df, name)
        for name in (
            "faithfulness",
            "answer_relevancy",
            "context_recall",
            "context_precision",
            "context_utilization",
        )
    }

    return SingleRunMetrics(
        **metric_values,
        **ir_scores,
    )
