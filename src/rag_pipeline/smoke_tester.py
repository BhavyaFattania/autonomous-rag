import asyncio

from src.data.question_loader import load_eval_questions
from src.utils.logger import get_logger

log = get_logger("smoke_test")


async def smoke_test_node(state, settings) -> dict:
    """
    Verify retrieval runs without crashing and returns non-empty contexts.
    This is not a quality gate and intentionally avoids LLM generation.
    """
    from src.models.rag_config import RAGConfig
    from src.rag_pipeline.pipeline import retrieve_contexts

    config = RAGConfig(**state["validated_config"])
    questions, _ = load_eval_questions(n=settings.evaluation.smoke_test_n_questions)
    collection_name = state["validated_config"].get("_collection_name")

    try:
        contexts, cost = await asyncio.wait_for(
            retrieve_contexts(config, questions, settings, collection_name=collection_name),
            timeout=180.0,
        )
    except TimeoutError:
        return {"status": "FAILED_SMOKE", "failure_reason": "Smoke test timed out after 180s"}
    except Exception as e:
        import traceback

        traceback.print_exc()
        return {"status": "FAILED_SMOKE", "failure_reason": f"Pipeline error: {e}"}

    for i, context in enumerate(contexts):
        if not context or not any((item or "").strip() for item in context):
            return {
                "status": "FAILED_SMOKE",
                "failure_reason": f"Question {i+1} returned empty retrieval context",
            }

    log.info("smoke_test_passed", n_questions=len(questions))
    return {
        "status": "RUNNING",
        "experiment_cost_usd": state.get("experiment_cost_usd", 0.0) + cost,
    }
