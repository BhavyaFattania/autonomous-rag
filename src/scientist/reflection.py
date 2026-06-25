from src.utils.langfuse_compat import observe
from src.utils.logger import get_logger
from src.utils.openrouter import call_openrouter

log = get_logger("reflection")

_MAX_REFLECTION_CHARS = 4000


def _truncate_to_sentence(text: str, max_chars: int) -> str:
    """Truncate text at a sentence boundary to avoid cut-off bullet points."""
    if len(text) <= max_chars:
        return text
    # Walk backwards from the limit to find the last sentence-ending punctuation.
    window = text[:max_chars]
    for sep in ("\n", ".", "!", "?"):
        idx = window.rfind(sep)
        if idx > max_chars // 2:  # Ensure we keep at least half the content
            return window[: idx + 1].rstrip()
    # No clean boundary found — fall back to the raw limit.
    return window.rstrip()


@observe(name="reflection_node")
async def reflection_node(state) -> dict:
    from src.utils.config_loader import load_run_settings

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

    return {"reflection_summary": _truncate_to_sentence(summary.strip(), _MAX_REFLECTION_CHARS)}


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
