# src/utils/openrouter.py

import os
import asyncio
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.storage.cost_tracker import add_cost, BudgetExceededError
from src.utils.logger import get_logger

log = get_logger("openrouter")

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
RETRYABLE_STATUS_CODES = {500, 502, 503, 504}
NON_RETRYABLE_STATUS_CODES = {400, 401, 403, 422}

# Token pricing per 1M tokens: (input_price, output_price)
MODEL_PRICING = {
    "deepseek/deepseek-v4-pro":         (0.435, 0.870),
    "deepseek/deepseek-v4-flash":       (0.140, 0.280),
    "deepseek/deepseek-v4-flash:free":  (0.000, 0.000),
    "qwen/qwen3-30b-a3b":              (0.100, 0.300),
    "qwen/qwen3.5-flash-02-23":        (0.065, 0.260),
    "openai/gpt-oss-20b":              (0.050, 0.200),
}


class OpenRouterError(Exception):
    pass

class OpenRouterRateLimitError(OpenRouterError):
    """Raised specifically on HTTP 429 so callers can switch to fallback model."""
    pass

class OpenRouterNonRetryableError(OpenRouterError):
    pass


def compute_cost(model_id: str, prompt_tokens: int, completion_tokens: int) -> float:
    price_in, price_out = MODEL_PRICING.get(model_id, (0.0, 0.0))
    return (
        (prompt_tokens / 1_000_000) * price_in
        + (completion_tokens / 1_000_000) * price_out
    )


def _build_payload(
    model_id: str,
    messages: list[dict],
    max_tokens: int,
    reasoning_effort: str | None,
    temperature: float | None,
) -> dict:
    """
    Builds the JSON payload for an OpenRouter call.
    When reasoning_effort is set, omits ALL sampling parameters (temperature etc.)
    because DeepSeek V4 thinking mode does not support them.
    """
    payload: dict = {
        "model": model_id,
        "messages": messages,
        "max_tokens": max_tokens,
    }
    if reasoning_effort:
        # Reasoning mode: no sampling params allowed
        payload["reasoning"] = {"effort": reasoning_effort}
        # temperature, top_p, etc. must be absent
    else:
        # Normal mode: sampling params allowed
        if temperature is not None:
            payload["temperature"] = temperature
    return payload


@retry(
    retry=retry_if_exception_type(OpenRouterError),
    stop=stop_after_attempt(1),
    wait=wait_exponential(multiplier=1, min=1, max=16),
    reraise=True,
)
async def _call_once(
    model_id: str,
    messages: list[dict],
    max_tokens: int,
    reasoning_effort: str | None,
    temperature: float | None,
    task: str,
    return_reasoning: bool = False,
) -> str | dict:
    """
    Single OpenRouter call with retry on transient errors.
    Raises OpenRouterRateLimitError on 429 (no retry — caller handles fallback).
    Returns the assistant content string.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise OpenRouterNonRetryableError("OPENROUTER_API_KEY not set.")

    payload = _build_payload(model_id, messages, max_tokens, reasoning_effort, temperature)

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/autonomous-rag-optimizer",
                "X-Title": "RAG Optimizer",
            },
            json=payload,
        )

    if response.status_code == 429:
        # Do NOT retry here — raise special exception so caller can use fallback model
        raise OpenRouterRateLimitError(f"Rate limit on {model_id}")

    if response.status_code in NON_RETRYABLE_STATUS_CODES:
        raise OpenRouterNonRetryableError(f"HTTP {response.status_code}: {response.text[:300]}")

    if response.status_code in RETRYABLE_STATUS_CODES:
        raise OpenRouterError(f"HTTP {response.status_code}: {response.text[:300]}")

    if response.status_code != 200:
        raise OpenRouterError(f"HTTP {response.status_code}: {response.text[:300]}")

    data = response.json()

    try:
        choice = data["choices"][0]
        message = choice["message"]
        content = message["content"]
    except (KeyError, IndexError) as e:
        raise OpenRouterError(f"Unexpected response shape: {e}")
    finish_reason = choice.get("finish_reason")
    reasoning_text = _extract_reasoning_text(message)

    # Track cost
    usage = data.get("usage", {})
    cost = compute_cost(
        model_id,
        usage.get("prompt_tokens", 0),
        usage.get("completion_tokens", 0),
    )
    add_cost(cost)  # Raises BudgetExceededError if ceiling hit

    log.debug(
        "openrouter_call_complete",
        model=model_id,
        task=task,
        prompt_tokens=usage.get("prompt_tokens"),
        completion_tokens=usage.get("completion_tokens"),
        cost_usd=round(cost, 6),
        finish_reason=finish_reason,
    )
    if not content:
        raise OpenRouterError(
            f"OpenRouter returned empty content for {model_id}; finish_reason={finish_reason}"
        )
    if finish_reason == "length":
        log.warning(
            "openrouter_completion_truncated",
            model=model_id,
            task=task,
            max_tokens=max_tokens,
            completion_tokens=usage.get("completion_tokens"),
        )

    if return_reasoning:
        return {"content": content, "reasoning": reasoning_text}
    return content


def _extract_reasoning_text(message: dict) -> str:
    reasoning = message.get("reasoning")
    if isinstance(reasoning, str):
        return reasoning.strip()
    details = message.get("reasoning_details")
    if not isinstance(details, list):
        return ""
    parts = []
    for item in details:
        if not isinstance(item, dict):
            continue
        for key in ("text", "content", "reasoning"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                parts.append(value.strip())
                break
    return "\n".join(parts)


try:
    from langfuse.decorators import observe
except ImportError:
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

@observe(name="call_openrouter")
async def call_openrouter(
    model_id: str,
    messages: list[dict],
    max_tokens: int,
    task: str,
    reasoning_effort: str | None = None,
    temperature: float | None = 0.1,
    fallback_model_id: str | None = None,
    return_reasoning: bool = False,
) -> str | dict:
    """
    Public entry point for all OpenRouter calls.
    If model_id gets a 429 AND fallback_model_id is provided, retries with fallback.
    BudgetExceededError propagates up — never caught here.
    """
    try:
        return await _call_once(
            model_id,
            messages,
            max_tokens,
            reasoning_effort,
            temperature,
            task,
            return_reasoning=return_reasoning,
        )
    except OpenRouterRateLimitError:
        if fallback_model_id:
            log.warning("rate_limit_fallback", primary=model_id, fallback=fallback_model_id)
            return await _call_once(
                fallback_model_id, messages, max_tokens,
                reasoning_effort=None,  # fallback is always non-reasoning
                temperature=temperature,
                task=f"{task}_fallback",
                return_reasoning=return_reasoning,
            )
        raise
