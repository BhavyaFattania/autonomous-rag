"""
Periodic experiment reflection and pattern extraction.

Summarizes recent successes/failures to extract actionable rules for
guiding the next generation of experiments.
"""

from src.core.provider import Provider
from src.utils.function_trace import trace_call
from src.utils.langfuse_compat import observe
from src.utils.logger import get_logger
from src.utils.openrouter import call_openrouter

log = get_logger("reflection")

_MAX_REFLECTION_CHARS = 4000


def _truncate_to_sentence(text: str, max_chars: int) -> str:
    """Trim text to max_chars by cutting at sentence boundary."""
    if len(text) <= max_chars:
        return text
    window = text[:max_chars]
    for sep in ("\n", ".", "!", "?"):
        idx = window.rfind(sep)
        if idx > max_chars // 2:
            return window[: idx + 1].rstrip()
    return window.rstrip()


@observe(name="reflection_node")
@trace_call(log_return=False)
async def reflection_node(state, settings, provider: Provider | None = None) -> dict:
    """Periodically call DeepSeek to synthesize successful/failed patterns; returns empty if not triggered."""
    n = settings.reflection.update_every_n_experiments
    completed = state.get("experiments_completed", 0)

    if completed == 0 or completed % n != 0:
        return {}

    prompt = _build_reflection_prompt(state)
    try:
        llm = provider.llm_client if provider else None
        if llm:
            summary = await llm.call(
                model_id="deepseek/deepseek-v4-pro",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2048,
                task="reflection",
                reasoning_effort="high",
                temperature=None,
            )
        else:
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

    if not isinstance(summary, str):
        log.warning("reflection_unexpected_type", type=type(summary).__name__)
        return {}

    return {"reflection_summary": _truncate_to_sentence(summary.strip(), _MAX_REFLECTION_CHARS)}


def _build_reflection_prompt(state) -> str:
    """Construct LLM prompt with recent patterns for extraction of actionable rules."""
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
