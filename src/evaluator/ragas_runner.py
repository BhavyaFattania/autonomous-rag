import random
import asyncio
import json
import re
import time
import yaml
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    ContextUtilization,
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)
from ragas.llms import LangchainLLMWrapper
from langchain_openai import ChatOpenAI
from langchain_core.exceptions import OutputParserException
from langchain_core.outputs import LLMResult
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompt_values import StringPromptValue
from ragas.prompt.pydantic_prompt import RagasOutputParser
from ragas.prompt.utils import extract_json
from ragas.run_config import RunConfig
from langchain_openai import OpenAIEmbeddings
from src.models.metrics import SingleRunMetrics
from src.evaluator.ir_metrics import evaluate_ir_metrics
from src.utils.logger import get_logger

log = get_logger("evaluator")


from src.utils.json_repair import install_ragas_output_parser_compat_patch


def _build_ragas_llm() -> LangchainLLMWrapper:
    """
    RAGAS requires a LangChain-compatible LLM.
    We wrap the OpenRouter Qwen3-30B via LangChain's ChatOpenAI interface
    (OpenRouter is OpenAI-compatible).
    """
    import os
    install_ragas_output_parser_compat_patch()
    judge_config = _load_ragas_judge_config()
    model_kwargs = _build_openrouter_model_kwargs(judge_config)
    extra_body = _build_openrouter_extra_body(judge_config)
    model_id = judge_config.get("model_id", "qwen/qwen3.5-flash-02-23")
    log.info(
        "ragas_judge_configured",
        model=model_id,
        response_format=judge_config.get("response_format"),
        exclude_reasoning=judge_config.get("exclude_reasoning"),
    )
    llm = ChatOpenAI(
        model=model_id,
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        temperature=judge_config.get("temperature", 0.0),
        max_tokens=judge_config.get("max_tokens", 4096),
        model_kwargs=model_kwargs,
        extra_body=extra_body,
        default_headers={
            "HTTP-Referer": "https://github.com/autonomous-rag-optimizer",
            "X-Title": "RAG Optimizer",
        },
    )
    return LangchainLLMWrapper(llm, is_finished_parser=_ragas_generation_finished)


def _build_ragas_embeddings(model_name: str) -> OpenAIEmbeddings:
    import os

    return OpenAIEmbeddings(
        model=model_name,
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
    )


def _build_openrouter_model_kwargs(judge_config: dict) -> dict:
    if judge_config.get("response_format") == "json_object":
        return {"response_format": {"type": "json_object"}}
    return {}


def _build_openrouter_extra_body(judge_config: dict) -> dict:
    extra_body = {}
    if judge_config.get("exclude_reasoning", True):
        extra_body["reasoning"] = {"effort": "none", "exclude": True}
    return extra_body


def _load_ragas_judge_config() -> dict:
    try:
        with open("config/model_routing.yaml") as f:
            routing = yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}
    return routing.get("models", {}).get("ragas_judge", {})


def _build_ragas_metrics(metric_names: list[str]):
    available_metrics = {
        "faithfulness": faithfulness,
        "answer_relevancy": answer_relevancy,
        "context_precision": context_precision,
        "context_recall": context_recall,
        "context_utilization": ContextUtilization(),
    }
    return [
        available_metrics[name]
        for name in metric_names
        if name in available_metrics
    ]


def _ragas_generation_finished(response: LLMResult) -> bool:
    finish_reasons = []
    for generation in response.flatten():
        item = generation.generations[0][0]
        reason = None
        if item.generation_info:
            reason = item.generation_info.get("finish_reason")
        message = getattr(item, "message", None)
        if reason is None and message is not None:
            reason = message.response_metadata.get("finish_reason")
        if reason is not None:
            finish_reasons.append(reason)

    if not finish_reasons:
        return True
    if any(reason == "length" for reason in finish_reasons):
        log.warning("ragas_judge_hit_token_limit", finish_reasons=finish_reasons)
    return all(reason in {"stop", "STOP", "MAX_TOKENS", "length"} for reason in finish_reasons)


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
    """
    Run one RAGAS evaluation pass.
    Returns SingleRunMetrics (mean across all questions).
    """
    if answers is None:
        answers = ground_truths
    assert len(questions) == len(answers) == len(contexts) == len(ground_truths)
    question_ids = question_ids or [f"q_{idx}" for idx in range(len(questions))]
    retrieval_results = retrieval_results or _contexts_to_results(contexts)

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
    ragas_metrics = _build_ragas_metrics(
        metric_names
    )
    if not ragas_metrics:
        return fast_metrics
    ragas_llm = _build_ragas_llm()
    ragas_embeddings = (
        _build_ragas_embeddings("openai/text-embedding-3-small")
        if "answer_relevancy" in metric_names
        else None
    )
    loop = asyncio.get_running_loop()
    started = time.perf_counter()
    log.info("ragas_eval_start", questions=len(questions))

    # Do not use asyncio.wait_for here. Cancelling run_in_executor futures
    # interacts poorly with nest_asyncio and ProactorEventLoop on Windows,
    # leading to InvalidStateError + WinError 995.
    # We rely on RAGAS RunConfig.timeout and an adaptive retry to prevent hangs.
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
        try:
            result = await loop.run_in_executor(
                None,
                lambda: evaluate(
                    dataset=dataset,
                    metrics=ragas_metrics,
                    llm=ragas_llm,
                    embeddings=ragas_embeddings,
                    run_config=run_config,
                    raise_exceptions=False,
                    show_progress=False,
                    batch_size=8,
                ),
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


def _safe_mean(df, column: str) -> float:
    if column not in df:
        return 0.0
    value = df[column].mean()
    if value != value:
        return 0.0
    return float(value)

async def evaluator_node(state) -> dict:
    """
    Runs the full RAG pipeline and RAGAS evaluation 3 times.
    Returns eval_results, aggregated_metrics, proposed_weighted_score.
    """
    from src.orchestrator.config_loader import load_run_settings
    from src.models.rag_config import RAGConfig
    from src.models.metrics import AggregatedMetrics
    from src.rag_pipeline.pipeline import retrieve_results
    import asyncio

    settings = load_run_settings()
    config = RAGConfig(**state["validated_config"])
    collection_name = state["validated_config"].get("_collection_name")

    completed = state.get("experiments_completed", 0)
    experiment_number = completed + 1
    full_every = settings["evaluation"].get("full_eval_every_n_experiments", 5)
    use_full_suite = full_every > 0 and experiment_number % full_every == 0
    n_questions = (
        settings["evaluation"].get("full_eval_n_questions", settings["evaluation"]["n_questions"])
        if use_full_suite
        else settings["evaluation"]["n_questions"]
    )
    question_items = _load_eval_question_items(n=n_questions)
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
        metrics=settings["evaluation"].get("ragas_metrics", ["context_recall"]),
    )

    runs: list[SingleRunMetrics] = []
    cost_this_node = 0.0

    n_runs = settings["evaluation"].get("n_eval_runs", 3)
    ragas_timeout = settings["evaluation"].get("max_runtime_sec_per_ragas", 120)
    ragas_timeout_backoff_factor = settings["evaluation"].get("ragas_timeout_backoff_factor", 2.0)
    ragas_max_timeout = settings["evaluation"].get("ragas_max_timeout_sec", 240)
    ragas_timeout_retries = settings["evaluation"].get("ragas_timeout_retries", 1)
    ragas_every = settings["evaluation"].get("ragas_audit_every_n_experiments", 5)
    run_ragas = ragas_every > 0 and experiment_number % ragas_every == 0
    ragas_min_fast_score = None
    if settings["evaluation"].get("ragas_audit_policy") == "competitive":
        tolerance = settings["evaluation"].get("ragas_audit_score_tolerance", 0.02)
        ragas_min_fast_score = state.get("current_best_weighted_score", 0.0) - tolerance
    if use_full_suite and config.reranker == "CohereRerank":
        log.warning("ragas_audit_skipped_for_cohere_full_suite", experiment_number=experiment_number)
        run_ragas = False
        ragas_min_fast_score = None
    for run_num in range(1, n_runs + 1):
        log.info("eval_run_starting", run=run_num, experiment_id=state["experiment_id"])
        try:
            results, run_cost = await asyncio.wait_for(
                retrieve_results(config, questions, collection_name=collection_name),
                timeout=settings["evaluation"]["max_runtime_sec_per_eval"],
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
                metrics=settings["evaluation"].get("ragas_metrics"),
            )
            runs.append(metrics)
            log.info("eval_run_complete", run=run_num, weighted_score=metrics.weighted_score)
        except asyncio.TimeoutError:
            log.error("eval_run_timeout", run=run_num)
            return {
                "status": "FAILED_TIMEOUT",
                "failure_reason": f"Eval run {run_num} timed out after {settings['evaluation']['max_runtime_sec_per_eval']}s",
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


def _load_eval_question_items(n: int) -> list[dict]:
    """Load fixed evaluation question records from data/hotpotqa/questions.jsonl."""
    import json
    from pathlib import Path

    items = []
    lines = Path("data/hotpotqa/questions.jsonl").read_text().strip().splitlines()
    for line in lines[:n]:
        item = json.loads(line)
        items.append({
            "id": item["id"],
            "question": item["question"],
            "answer": item["answer"],
            "supporting_titles": item.get("supporting_titles", []),
        })
    assert len(items) == n, f"Expected {n} questions, got {len(items)}"
    return items


def _load_eval_questions(n: int) -> tuple[list[str], list[str]]:
    """Load fixed evaluation questions from data/hotpotqa/questions.jsonl."""
    items = _load_eval_question_items(n)
    return [item["question"] for item in items], [item["answer"] for item in items]


def _contexts_to_results(contexts: list[list[str]]) -> list[list[dict]]:
    return [
        [
            {
                "node_id": f"legacy_{question_idx}_{rank}",
                "doc_id": f"legacy_{question_idx}_{rank}",
                "title": "",
                "score": 1.0 / (rank + 1),
                "text": text,
            }
            for rank, text in enumerate(context)
        ]
        for question_idx, context in enumerate(contexts)
    ]
