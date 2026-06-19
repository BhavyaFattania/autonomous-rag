try:
    from langfuse.decorators import observe
except ImportError:
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

from src.utils.logger import get_logger
from src.utils.openrouter import call_openrouter

log = get_logger("reflection")

@observe(name="reflection_node")
async def reflection_node(state) -> dict:
    from src.orchestrator.config_loader import load_run_settings

    settings = load_run_settings()
    n = settings["reflection"]["update_every_n_experiments"]
    completed = state.get("experiments_completed", 0)

    if completed == 0 or completed % n != 0:
        return {}

    prompt = _build_reflection_prompt(state)
    try:
        summary = await call_openrouter(
            model_id="deepseek/deepseek-v4-pro",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
            task="reflection",
            reasoning_effort="high",
            temperature=None,
        )
    except Exception as e:
        log.warning("reflection_failed", error=str(e))
        return {}

    return {"reflection_summary": summary.strip()[:4000]}


def _build_reflection_prompt(state) -> str:
    successful = "\n".join(state.get("successful_patterns", [])[-12:]) or "None"
    failed = "\n".join(state.get("failed_patterns", [])[-12:]) or "None"
    best_config = state.get("current_best_config", {})
    best_score = state.get("current_best_weighted_score", 0.0)

    return f"""
You are analyzing a RAG optimization run.

Current best score: {best_score:.4f}
Current best config: {best_config}

Accepted patterns:
{successful}

Rejected or failed patterns:
{failed}

Extract concise, actionable rules for the next scientist prompt. Focus on which
chunking, top_k, hybrid_alpha, reranker, and generator choices appear to help or
hurt. Do not invent evidence. Return 5-8 bullet points only.
""".strip()
