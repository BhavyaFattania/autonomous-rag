"""
OpenAI HTTP client.

Adapter (GoF): normalizes OpenAI's native chat-completions API into the same
`ILLMClient.call()` contract `OpenRouterClient` already satisfies, so nodes
consuming `provider.llm_client` never need to know which provider is live.
"""

from __future__ import annotations

import os

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.core.interfaces import ICostTracker
from src.storage.cost_tracker import add_cost
from src.utils.langfuse_compat import observe
from src.utils.logger import get_logger

log = get_logger("openai_client")

OPENAI_BASE_URL = "https://api.openai.com/v1"
RETRYABLE_STATUS_CODES = {500, 502, 503, 504}
NON_RETRYABLE_STATUS_CODES = {400, 401, 403, 422}

# Reasoning-effort ("o-series") models take no custom temperature and use a
# top-level `reasoning_effort` field instead of OpenRouter's nested
# `{"reasoning": {"effort": ...}}` shape.
REASONING_MODEL_PREFIXES = ("o1", "o3", "o4")


class OpenAIError(Exception):
    pass


class OpenAIRateLimitError(OpenAIError):
    pass


class OpenAINonRetryableError(OpenAIError):
    pass


class OpenAIClient:
    """HTTP client for OpenAI's chat-completions API with retry and cost tracking."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = OPENAI_BASE_URL,
        pricing: dict[str, tuple[float, float]] | None = None,
        cost_tracker: ICostTracker | None = None,
    ):
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self._base_url = base_url
        # Lazily loaded from config/openai_pricing.yaml on first use unless
        # injected (tests / callers with their own pricing source pass this).
        self._pricing = pricing
        # When given, receives every call's cost directly — this is what
        # Provider.cost_tracker should be wired to, so cost tracking doesn't
        # depend on the module-level default tracker in src.storage.cost_tracker
        # lining up with it by coincidence. Falls back to that singleton (via
        # add_cost()) when omitted, matching OpenRouterClient's behavior.
        self._cost_tracker = cost_tracker

    def build_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def _report_cost(self, usd: float) -> None:
        if self._cost_tracker is not None:
            self._cost_tracker.add_cost(usd)
        else:
            add_cost(usd)

    def _get_pricing(self) -> dict[str, tuple[float, float]]:
        if self._pricing is None:
            from config.loader import load_openai_pricing

            self._pricing = load_openai_pricing()
        return self._pricing

    def compute_cost(self, model_id: str, prompt_tokens: int, completion_tokens: int) -> float:
        pricing = self._get_pricing()
        if model_id not in pricing:
            log.warning(
                "openai_pricing_missing",
                model=model_id,
                hint="add it to config/openai_pricing.yaml; cost recorded as $0 until then",
            )
            return 0.0
        price_in, price_out = pricing[model_id]
        return (prompt_tokens / 1_000_000) * price_in + (completion_tokens / 1_000_000) * price_out

    async def fetch_available_models(self) -> set[str]:
        """Live model IDs from OpenAI's catalog (GET /v1/models). Used to
        validate configured models still exist — OpenAI's API has no pricing
        endpoint, so this checks availability only, not price."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self._base_url}/models", headers=self.build_headers())

        if response.status_code != 200:
            raise OpenAIError(
                f"Failed to list models: HTTP {response.status_code}: {response.text[:300]}"
            )

        data = response.json()
        return {item["id"] for item in data.get("data", [])}

    async def validate_models(self, required_model_ids: list[str]) -> list[str]:
        """Check only the models this project actually references (not
        OpenAI's full catalog) against the live model list. Returns the
        subset of `required_model_ids` that OpenAI no longer serves, logging
        a warning if any are missing."""
        available = await self.fetch_available_models()
        missing = [m for m in required_model_ids if m not in available]
        if missing:
            log.warning("openai_models_unavailable", missing=missing)
        return missing

    @retry(
        retry=retry_if_exception_type(OpenAIError),
        stop=stop_after_attempt(1),
        wait=wait_exponential(multiplier=1, min=1, max=16),
        reraise=True,
    )
    async def _call_once(
        self,
        model_id: str,
        messages: list[dict],
        max_tokens: int,
        reasoning_effort: str | None,
        temperature: float | None,
        task: str,
        return_reasoning: bool = False,
        response_format: str | None = None,
    ) -> str | dict:
        if not self._api_key:
            raise OpenAINonRetryableError("OPENAI_API_KEY not set.")

        payload = _build_payload(
            model_id, messages, max_tokens, reasoning_effort, temperature, response_format
        )

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self._base_url}/chat/completions",
                headers=self.build_headers(),
                json=payload,
            )

        if response.status_code == 429:
            raise OpenAIRateLimitError(f"Rate limit on {model_id}")

        if response.status_code in NON_RETRYABLE_STATUS_CODES:
            raise OpenAINonRetryableError(f"HTTP {response.status_code}: {response.text[:300]}")

        if response.status_code in RETRYABLE_STATUS_CODES:
            raise OpenAIError(f"HTTP {response.status_code}: {response.text[:300]}")

        if response.status_code != 200:
            raise OpenAIError(f"HTTP {response.status_code}: {response.text[:300]}")

        data = response.json()

        try:
            choice = data["choices"][0]
            message = choice["message"]
            content = message["content"]
        except (KeyError, IndexError) as e:
            raise OpenAIError(f"Unexpected response shape: {e}") from e
        finish_reason = choice.get("finish_reason")

        usage = data.get("usage", {})
        cost = self.compute_cost(
            model_id,
            usage.get("prompt_tokens", 0),
            usage.get("completion_tokens", 0),
        )
        self._report_cost(cost)

        log.debug(
            "openai_call_complete",
            model=model_id,
            task=task,
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            cost_usd=round(cost, 6),
            finish_reason=finish_reason,
        )
        if not content:
            raise OpenAIError(
                f"OpenAI returned empty content for {model_id}; finish_reason={finish_reason}"
            )
        if finish_reason == "length":
            log.warning(
                "openai_completion_truncated",
                model=model_id,
                task=task,
                max_tokens=max_tokens,
                completion_tokens=usage.get("completion_tokens"),
            )

        if return_reasoning:
            # OpenAI's chat-completions API does not return reasoning text
            # (unlike OpenRouter's `reasoning`/`reasoning_details` fields).
            return {"content": content, "reasoning": ""}
        return content

    async def call(
        self,
        model_id: str,
        messages: list[dict],
        max_tokens: int,
        task: str,
        reasoning_effort: str | None = None,
        temperature: float | None = 0.1,
        fallback_model_id: str | None = None,
        return_reasoning: bool = False,
        response_format: str | None = None,
    ) -> str | dict:
        try:
            return await self._call_once(
                model_id,
                messages,
                max_tokens,
                reasoning_effort,
                temperature,
                task,
                return_reasoning=return_reasoning,
                response_format=response_format,
            )
        except OpenAIRateLimitError:
            if fallback_model_id:
                log.warning("rate_limit_fallback", primary=model_id, fallback=fallback_model_id)
                return await self._call_once(
                    fallback_model_id,
                    messages,
                    max_tokens,
                    reasoning_effort=None,
                    temperature=temperature,
                    task=f"{task}_fallback",
                    return_reasoning=return_reasoning,
                    response_format=response_format,
                )
            raise


def _build_payload(
    model_id: str,
    messages: list[dict],
    max_tokens: int,
    reasoning_effort: str | None,
    temperature: float | None,
    response_format: str | None = None,
) -> dict:
    payload: dict = {
        "model": model_id,
        "messages": messages,
        "max_tokens": max_tokens,
    }
    is_reasoning_model = model_id.startswith(REASONING_MODEL_PREFIXES)
    if reasoning_effort and is_reasoning_model:
        payload["reasoning_effort"] = reasoning_effort
    elif temperature is not None and not is_reasoning_model:
        payload["temperature"] = temperature
    if response_format == "json_object":
        payload["response_format"] = {"type": "json_object"}
    return payload


@observe(name="call_openai")
async def call_openai(
    client: OpenAIClient,
    model_id: str,
    messages: list[dict],
    max_tokens: int,
    task: str,
    reasoning_effort: str | None = None,
    temperature: float | None = 0.1,
    fallback_model_id: str | None = None,
    return_reasoning: bool = False,
    response_format: str | None = None,
) -> str | dict:
    """Thin traced wrapper. Unlike `call_openrouter`, takes an explicit client
    rather than a module-level default — the OpenAI adapter has no legacy
    call sites that bypass `Provider`, so it doesn't need a global singleton."""
    return await client.call(
        model_id,
        messages,
        max_tokens,
        task,
        reasoning_effort=reasoning_effort,
        temperature=temperature,
        fallback_model_id=fallback_model_id,
        return_reasoning=return_reasoning,
        response_format=response_format,
    )
