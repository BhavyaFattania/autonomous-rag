"""
Periodic experiment reflection and pattern extraction.

Summarizes recent successes/failures to extract actionable rules for
guiding the next generation of experiments.
"""

from config.loader import load_model_routing

from src.core.provider import Provider
from src.prompts.templates import REFLECTION_TEMPLATE
from src.utils.context_budget import truncate_to_token_budget
from src.utils.function_trace import trace_call
from src.utils.langfuse_compat import observe
from src.utils.logger import get_logger

model_routing = load_model_routing()
reflection_llm = model_routing.reflection
log = get_logger("reflection")

# Roughly equivalent to the previous 4000-character budget, expressed in tokens.
_MAX_REFLECTION_TOKENS = 1000


@observe(name="reflection_node")
@trace_call(log_return=False)
async def reflection_node(state, settings, provider: Provider) -> dict:
    """Periodically call DeepSeek to synthesize successful/failed patterns; returns empty if not triggered."""
    n = settings.reflection.update_every_n_experiments
    completed = state.get("experiments_completed", 0)

    if completed == 0 or completed % n != 0:
        return {}

    prompt = _build_reflection_prompt(state)
    try:
        summary = await provider.llm_client.call(
            model_id=reflection_llm.model_id,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=reflection_llm.max_tokens,
            task=reflection_llm.task,
            reasoning_effort=reflection_llm.reasoning_effort,
            temperature=reflection_llm.temperature,
        )
    except Exception as e:
        log.warning("reflection_failed", error=str(e))
        return {}

    if not isinstance(summary, str):
        log.warning("reflection_unexpected_type", type=type(summary).__name__)
        return {}

    return {"reflection_summary": truncate_to_token_budget(summary.strip(), _MAX_REFLECTION_TOKENS)}


def _build_reflection_prompt(state) -> str:
    """Construct LLM prompt with recent patterns for extraction of actionable rules."""
    successful = "\n".join(state.get("successful_patterns", [])[-12:]) or "None"
    failed = "\n".join(state.get("failed_patterns", [])[-12:]) or "None"
    best_config = state.get("current_best_config", {})
    best_score = state.get("current_best_weighted_score", 0.0)

    return REFLECTION_TEMPLATE.format(
        best_score=best_score,
        best_config=best_config,
        successful=successful,
        failed=failed,
    )
