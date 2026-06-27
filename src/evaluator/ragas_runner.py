import asyncio
import time
from datasets import Dataset
from ragas import evaluate as ragas_evaluate
from ragas.run_config import RunConfig
from src.models.metrics import SingleRunMetrics
from src.data.question_loader import load_eval_question_items
from src.evaluator.ir_metrics import evaluate_ir_metrics
from src.evaluator.ragas_setup import build_ragas_llm, build_ragas_embeddings, build_ragas_metrics
from src.rag_pipeline.pipeline import contexts_to_results
from src.utils.logger import get_logger

from config.loader import load_model_routing, load_env
log = get_logger("evaluator")


def _safe_mean(df, column: str) -> float:
    if column not in df:
        return 0.0
    value = df[column].mean()
    if value != value:
        return 0.0
    return float(value)


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
) -> SingleRunMetrics:
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
        ragas_min_fast_score is not None
        and fast_metrics.weighted_score >= ragas_min_fast_score
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
    ragas_metrics = build_ragas_metrics(metric_names)
    if not ragas_metrics:
        return fast_metrics
    ragas_llm = build_ragas_llm(model_routing=load_model_routing(), env=load_env())
    ragas_embeddings = (
        build_ragas_embeddings("openai/text-embedding-3-small", env=load_env())
        if "answer_relevancy" in metric_names
        else None
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
            max_retries=0,
            max_wait=5,
            max_workers=worker_count,
        )

        def _run_evaluate(loop_for_thread, cfg=run_config):
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
            result = await loop.run_in_executor(
                None, _run_evaluate, worker_loop,
            )
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


async def evaluator_node(state, settings, env=None, model_routing=None) -> dict:
    from src.models.rag_config import RAGConfig
    from src.models.metrics import AggregatedMetrics
    from src.rag_pipeline.pipeline import retrieve_results, contexts_to_results
    import asyncio

    eval_settings = settings.evaluation
    config = RAGConfig(**state["validated_config"])
    collection_name = state["validated_config"].get("_collection_name")

    completed = state.get("experiments_completed", 0)
    experiment_number = completed + 1
    full_every = eval_settings.full_eval_every_n_experiments
    use_full_suite = full_every > 0 and experiment_number % full_every == 0
    n_questions = (
        eval_settings.full_eval_n_questions
        if use_full_suite
        else eval_settings.n_questions
    )
    question_items = load_eval_question_items(n=n_questions)
    question_ids = [item["id"] for item in question_items]
    questions = [item["question"] for item in question_items]
    ground_truths = [item["answer"] for item in question_items]
    supporting_titles = [item.get("supporting_titles", []) for item in question_items]
    if not any(supporting_titles):
        log.warning(
            "ir_eval_using_answer_string_fallback",
            reason="questions.jsonl has no supporting_titles",
        )
    log.info(
        "eval_question_set_selected",
        experiment_number=experiment_number,
        questions=n_questions,
        full_suite=use_full_suite,
        metrics=eval_settings.ragas_metrics,
    )

    runs: list[SingleRunMetrics] = []
    cost_this_node = 0.0

    n_runs = eval_settings.n_eval_runs
    ragas_timeout = eval_settings.max_runtime_sec_per_ragas
    ragas_timeout_backoff_factor = eval_settings.ragas_timeout_backoff_factor
    ragas_max_timeout = eval_settings.ragas_max_timeout_sec
    ragas_timeout_retries = eval_settings.ragas_timeout_retries
    ragas_every = eval_settings.ragas_audit_every_n_experiments
    run_ragas = ragas_every > 0 and experiment_number % ragas_every == 0
    ragas_min_fast_score = None
    if eval_settings.ragas_audit_policy == "competitive":
        tolerance = eval_settings.ragas_audit_score_tolerance
        ragas_min_fast_score = state.get("current_best_weighted_score", 0.0) - tolerance
    if use_full_suite and config.reranker == "CohereRerank":
        log.warning("ragas_audit_skipped_for_cohere_full_suite", experiment_number=experiment_number)
        run_ragas = False
        ragas_min_fast_score = None
    for run_num in range(1, n_runs + 1):
        log.info("eval_run_starting", run=run_num, experiment_id=state["experiment_id"])
        try:
            results, run_cost = await asyncio.wait_for(
                retrieve_results(config, questions, settings, collection_name=collection_name, env=env),
                timeout=eval_settings.max_runtime_sec_per_eval,
            )
            contexts = [[item.get("text", "") for item in items] for items in results]
            cost_this_node += run_cost
            metrics = await run_single_eval(
                questions, None, contexts, ground_truths,
                retrieval_results=results, question_ids=question_ids,
                supporting_titles=supporting_titles,
                run_ragas=run_ragas, ragas_min_fast_score=ragas_min_fast_score,
                timeout_sec=ragas_timeout, timeout_backoff_factor=ragas_timeout_backoff_factor,
                max_timeout_sec=ragas_max_timeout, timeout_retries=ragas_timeout_retries,
                metrics=eval_settings.ragas_metrics,
            )
            runs.append(metrics)
            log.info("eval_run_complete", run=run_num, weighted_score=metrics.weighted_score)
        except asyncio.TimeoutError:
            log.error("eval_run_timeout", run=run_num)
            return {
                "status": "FAILED_TIMEOUT",
                "failure_reason": f"Eval run {run_num} timed out after {eval_settings.max_runtime_sec_per_eval}s",
                "experiment_cost_usd": cost_this_node,
            }
        except Exception as e:
            log.error("eval_run_error", run=run_num, error=str(e))
            return {
                "status": "FAILED_API_ERROR",
                "failure_reason": f"Eval run {run_num} failed: {e}",
                "experiment_cost_usd": cost_this_node,
            }

    aggregated = AggregatedMetrics.from_runs(runs)
    log.info(
        "eval_complete",
        median_weighted_score=aggregated.median_weighted_score,
        std_dev=aggregated.std_dev_weighted_score,
    )

    return {
        "eval_results": [r.model_dump() for r in runs],
        "aggregated_metrics": aggregated.model_dump(),
        "proposed_weighted_score": aggregated.median_weighted_score,
        "current_best_weighted_score": state.get("current_best_weighted_score", 0.0),
        "experiment_cost_usd": state.get("experiment_cost_usd", 0.0) + cost_this_node,
        "status": "RUNNING",
    }
