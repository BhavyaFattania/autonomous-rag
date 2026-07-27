# tests/test_cost_callback.py
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, LLMResult
from src.core.cost_callback import CostTrackingCallback


class _Tracker:
    def __init__(self):
        self.total = 0.0

    def add_cost(self, usd):
        self.total += usd
        return self.total


def _llm_result(model_id, prompt_tokens, completion_tokens):
    msg = AIMessage(
        content="hi",
        usage_metadata={
            "input_tokens": prompt_tokens,
            "output_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    )
    return LLMResult(
        generations=[[ChatGeneration(message=msg)]],
        llm_output={"model_name": model_id},
    )


def test_callback_records_cost_from_usage_metadata():
    tracker = _Tracker()
    cb = CostTrackingCallback(cost_tracker=tracker, provider="openrouter")
    cb.on_llm_end(_llm_result("deepseek/deepseek-v4-pro", 1_000_000, 1_000_000))
    assert round(tracker.total, 4) == round(0.435 + 0.870, 4)


def test_callback_raise_error_is_true():
    # so BudgetExceededError from add_cost propagates out of ainvoke
    cb = CostTrackingCallback(cost_tracker=_Tracker(), provider="openai")
    assert cb.raise_error is True


def test_callback_uses_injected_pricing_map():
    tracker = _Tracker()
    injected = {"some/model": (3.0, 5.0)}
    cb = CostTrackingCallback(cost_tracker=tracker, provider="openrouter", pricing=injected)
    cb.on_llm_end(_llm_result("some/model", 1_000_000, 1_000_000))
    assert round(tracker.total, 4) == round(3.0 + 5.0, 4)
