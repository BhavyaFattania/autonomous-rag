import asyncio


from src.data.question_loader import load_eval_question_items
from src.evaluator.ragas_runner import run_single_eval
from src.models.metrics import AggregatedMetrics, SingleRunMetrics
from src.models.rag_config import RAGConfig
from src.rag_pipeline.pipeline import retrieve_results
from src.utils.logger import get_logger

log = get_logger("evaluator")


async def evaluator_node(state, settings, env=None, model_routing=None) -> dict:
    eval_settings = settings.evaluation
    config = RAGConfig(**state["validated_config"])
    collection_name = state["validated_config"].get("_collection_name")

    completed = state.get("experiments_completed", 0)
    experiment_number = completed + 1
    full_every = eval_settings.full_eval_every_n_experiments
    use_full_suite = full_every > 0 and experiment_number % full_every == 0
    n_questions = (
        eval_settings.full_eval_n_questions if use_full_suite else eval_settings.n_questions
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
        log.warning(
            "ragas_audit_skipped_for_cohere_full_suite", experiment_number=experiment_number
        )
        run_ragas = False
        ragas_min_fast_score = None
    for run_num in range(1, n_runs + 1):
        log.info("eval_run_starting", run=run_num, experiment_id=state["experiment_id"])
        try:
            results, run_cost = await asyncio.wait_for(
                retrieve_results(
                    config, questions, settings, collection_name=collection_name, env=env
                ),
                timeout=eval_settings.max_runtime_sec_per_eval,
            )
            contexts = [[item.get("text", "") for item in items] for items in results]
            cost_this_node += run_cost
            metrics = await run_single_eval(
                questions,
                None,
                contexts,
                ground_truths,
                retrieval_results=results,
                question_ids=question_ids,
                supporting_titles=supporting_titles,
                run_ragas=run_ragas,
                ragas_min_fast_score=ragas_min_fast_score,
                timeout_sec=ragas_timeout,
                timeout_backoff_factor=ragas_timeout_backoff_factor,
                max_timeout_sec=ragas_max_timeout,
                timeout_retries=ragas_timeout_retries,
                metrics=eval_settings.ragas_metrics,
                env=env,
            )
            runs.append(metrics)
            log.info("eval_run_complete", run=run_num, weighted_score=metrics.weighted_score)
        except TimeoutError:
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
