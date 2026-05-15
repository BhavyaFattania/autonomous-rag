import random
import asyncio
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall, context_precision
from ragas.llms import LangchainLLMWrapper
from langchain_openai import ChatOpenAI
from src.models.metrics import SingleRunMetrics
from src.utils.logger import get_logger

log = get_logger("evaluator")


def _build_ragas_llm() -> LangchainLLMWrapper:
    """
    RAGAS requires a LangChain-compatible LLM.
    We wrap the OpenRouter Qwen3-30B via LangChain's ChatOpenAI interface
    (OpenRouter is OpenAI-compatible).
    """
    import os
    llm = ChatOpenAI(
        model="qwen/qwen3-30b-a3b",
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        temperature=0.0,
        max_tokens=256,
    )
    return LangchainLLMWrapper(llm)


async def run_single_eval(
    questions: list[str],
    answers: list[str],
    contexts: list[list[str]],
    ground_truths: list[str],
) -> SingleRunMetrics:
    """
    Run one RAGAS evaluation pass.
    Returns SingleRunMetrics (mean across all questions).
    """
    assert len(questions) == len(answers) == len(contexts) == len(ground_truths)

    data = {
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    }
    dataset = Dataset.from_dict(data)
    ragas_llm = _build_ragas_llm()

    result = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
        llm=ragas_llm,
        raise_exceptions=False,        # Don't crash on single-question failures
    )

    df = result.to_pandas()

    return SingleRunMetrics(
        faithfulness=float(df["faithfulness"].mean()),
        answer_relevancy=float(df["answer_relevancy"].mean()),
        context_recall=float(df["context_recall"].mean()),
        context_precision=float(df["context_precision"].mean()),
    )

async def evaluator_node(state) -> dict:
    """
    Runs the full RAG pipeline and RAGAS evaluation 3 times.
    Returns eval_results, aggregated_metrics, proposed_weighted_score.
    """
    from src.orchestrator.config_loader import load_run_settings
    from src.models.rag_config import RAGConfig
    from src.models.metrics import AggregatedMetrics
    from src.rag_pipeline.pipeline import run_pipeline
    import asyncio

    settings = load_run_settings()
    config = RAGConfig(**state["validated_config"])

    questions, ground_truths = _load_eval_questions(
        n=settings["evaluation"]["n_questions"]
    )

    runs: list[SingleRunMetrics] = []
    cost_this_node = 0.0

    for run_num in range(1, 4):
        log.info("eval_run_starting", run=run_num, experiment_id=state["experiment_id"])
        try:
            answers, contexts, run_cost = await asyncio.wait_for(
                run_pipeline(config, questions),
                timeout=settings["evaluation"]["max_runtime_sec_per_eval"],
            )
            cost_this_node += run_cost
            metrics = await run_single_eval(questions, answers, contexts, ground_truths)
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
        "experiment_cost_usd": state.get("experiment_cost_usd", 0.0) + cost_this_node,
        "status": "RUNNING",
    }


def _load_eval_questions(n: int) -> tuple[list[str], list[str]]:
    """Load fixed evaluation questions from data/hotpotqa/questions.jsonl."""
    import json
    from pathlib import Path
    questions, ground_truths = [], []
    lines = Path("data/hotpotqa/questions.jsonl").read_text().strip().splitlines()
    for line in lines[:n]:
        item = json.loads(line)
        questions.append(item["question"])
        ground_truths.append(item["answer"])
    assert len(questions) == n, f"Expected {n} questions, got {len(questions)}"
    return questions, ground_truths
