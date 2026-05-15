import asyncio
from src.utils.openrouter import call_openrouter
from src.utils.logger import get_logger

log = get_logger("smoke_test")


async def smoke_test_node(state) -> dict:
    """
    Runs 5 questions through the proposed pipeline.
    Uses Qwen3.5-Flash to validate outputs are coherent (not empty, not errors).
    This is NOT a quality check — it only verifies the pipeline runs without crashing
    and returns non-empty, non-error strings.
    """
    from src.models.rag_config import RAGConfig
    from src.rag_pipeline.pipeline import run_pipeline

    config = RAGConfig(**state["validated_config"])
    questions, ground_truths = _load_smoke_questions(n=3)

    try:
        answers, contexts, cost = await asyncio.wait_for(
            run_pipeline(config, questions),
            timeout=180.0,   # 3-minute timeout for smoke test
        )
    except asyncio.TimeoutError:
        return {"status": "FAILED_SMOKE", "failure_reason": "Smoke test timed out after 180s"}
    except Exception as e:
        import traceback
        traceback.print_exc() # Show the full error in the terminal
        return {"status": "FAILED_SMOKE", "failure_reason": f"Pipeline error: {e}"}

    # Validate outputs using Qwen3.5-Flash
    for i, (q, a) in enumerate(zip(questions, answers)):
        if not a or len(a.strip()) < 5:
            return {
                "status": "FAILED_SMOKE",
                "failure_reason": f"Question {i+1} returned empty answer: '{a}'"
            }

        validation_prompt = f"""Question: {q}
Answer: {a}

Is this answer a coherent English sentence that attempts to answer the question?
Respond with ONLY "YES" or "NO"."""

        verdict = await call_openrouter(
            model_id="qwen/qwen3.5-flash-02-23",
            messages=[{"role": "user", "content": validation_prompt}],
            max_tokens=5,
            task="smoke_test",
            reasoning_effort=None,
            temperature=0.0,
        )

        if verdict.strip().upper() not in ("YES", "YES."):
            return {
                "status": "FAILED_SMOKE",
                "failure_reason": f"Question {i+1} failed coherence check. Answer: '{a[:100]}'"
            }

    log.info("smoke_test_passed", n_questions=3)
    return {
        "status": "RUNNING",
        "experiment_cost_usd": state.get("experiment_cost_usd", 0.0) + cost,
    }


def _load_smoke_questions(n: int = 5) -> tuple[list[str], list[str]]:
    """Load first N questions from the fixed eval set."""
    import json
    from pathlib import Path
    questions, answers = [], []
    lines = Path("data/hotpotqa/questions.jsonl").read_text().strip().splitlines()
    for line in lines[:n]:
        item = json.loads(line)
        questions.append(item["question"])
        answers.append(item["answer"])
    return questions, answers
