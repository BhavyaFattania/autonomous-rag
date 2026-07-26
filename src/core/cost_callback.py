"""LangChain callback that records per-call USD into the injected cost tracker.

Attached to every ChatOpenAI (nodes AND the RAGAS judge) so judge spend is
finally counted. raise_error=True lets a BudgetExceededError raised by
cost_tracker.add_cost() propagate out of the LLM call, matching the pre-existing
node-level `except BudgetExceededError` handling.
"""

from __future__ import annotations

from typing import Any

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from src.core.interfaces import ICostTracker
from src.core.pricing import compute_cost
from src.utils.logger import get_logger

log = get_logger("cost_callback")


def _usage_from_result(response: LLMResult) -> tuple[str | None, int, int]:
    """Extract (model_id, prompt_tokens, completion_tokens) from an LLMResult."""
    model_id = (response.llm_output or {}).get("model_name")
    for gen_list in response.generations:
        for gen in gen_list:
            msg = getattr(gen, "message", None)
            usage = getattr(msg, "usage_metadata", None) if msg is not None else None
            if usage:
                return (
                    model_id,
                    int(usage.get("input_tokens", 0)),
                    int(usage.get("output_tokens", 0)),
                )
    token_usage = (response.llm_output or {}).get("token_usage", {})
    return (
        model_id,
        int(token_usage.get("prompt_tokens", 0)),
        int(token_usage.get("completion_tokens", 0)),
    )


class CostTrackingCallback(BaseCallbackHandler):
    raise_error = True  # propagate BudgetExceededError from add_cost

    def __init__(self, cost_tracker: ICostTracker, provider: str):
        self._cost_tracker = cost_tracker
        self._provider = provider

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        model_id, prompt_tokens, completion_tokens = _usage_from_result(response)
        if not model_id:
            log.warning("cost_callback_no_model_name")
            return
        cost = compute_cost(self._provider, model_id, prompt_tokens, completion_tokens)
        self._cost_tracker.add_cost(cost)
