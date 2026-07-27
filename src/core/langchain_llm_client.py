"""LangChain-backed ILLMClient adapter + ChatOpenAI factory.

Replaces the hand-rolled OpenRouterClient/OpenAIClient. One ChatOpenAI engine
for nodes and the RAGAS judge; cost recorded via CostTrackingCallback.
"""

from __future__ import annotations

from typing import Any

import openai
from langchain_core.callbacks import BaseCallbackHandler
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from src.core.cost_callback import CostTrackingCallback
from src.core.interfaces import ICostTracker
from src.utils.langfuse_compat import observe
from src.utils.logger import get_logger
from src.utils.openrouter import _extract_reasoning_text

log = get_logger("langchain_llm_client")

_OPENAI_REASONING_PREFIXES = ("o1", "o3", "o4")


def _is_openai_reasoning_model(model_id: str) -> bool:
    return model_id.startswith(_OPENAI_REASONING_PREFIXES)


def _model_kwargs_for(
    provider: str,
    reasoning_effort: str | None,
    temperature: float | None,
    response_format: str | None,
    model_id: str,
) -> dict[str, Any]:
    """Build the ChatOpenAI model_kwargs that reproduce the current payloads.

    - OpenRouter reasoning: nested {"reasoning": {"effort": ...}} in extra_body,
      and temperature omitted.
    - OpenAI o-series: top-level reasoning_effort, temperature omitted.
    - Otherwise: temperature passed, no reasoning.
    - json_object: response_format set.
    """
    model_kwargs: dict[str, Any] = {}
    reasoning_active = False

    if reasoning_effort:
        if provider == "openai" and _is_openai_reasoning_model(model_id):
            model_kwargs["reasoning_effort"] = reasoning_effort
            reasoning_active = True
        elif provider != "openai":  # OpenRouter-style nested reasoning
            model_kwargs["extra_body"] = {"reasoning": {"effort": reasoning_effort}}
            reasoning_active = True

    if not reasoning_active and temperature is not None:
        model_kwargs["temperature"] = temperature

    if response_format == "json_object":
        model_kwargs["response_format"] = {"type": "json_object"}

    return model_kwargs


def build_chat_model(
    provider: str,
    model_id: str,
    api_key: str,
    base_url: str,
    default_headers: dict,
    max_tokens: int,
    reasoning_effort: str | None,
    temperature: float | None,
    response_format: str | None,
    callbacks: list[BaseCallbackHandler],
) -> ChatOpenAI:
    mk = _model_kwargs_for(provider, reasoning_effort, temperature, response_format, model_id)
    temp = mk.pop("temperature", None)
    extra_body = mk.pop("extra_body", None)
    top_reasoning_effort = mk.pop("reasoning_effort", None)
    return ChatOpenAI(
        model=model_id,
        base_url=base_url,
        api_key=SecretStr(api_key),
        default_headers=default_headers or None,
        max_completion_tokens=max_tokens,
        temperature=temp,
        extra_body=extra_body,
        reasoning_effort=top_reasoning_effort,
        model_kwargs=mk,
        callbacks=callbacks or None,
    )


class LLMClientError(Exception):
    pass


class LangChainLLMClient:
    """ILLMClient implementation backed by langchain-openai ChatOpenAI."""

    def __init__(
        self,
        provider: str,
        api_key: str,
        base_url: str,
        default_headers: dict,
        cost_tracker: ICostTracker | None = None,
        pricing: dict[str, tuple[float, float]] | None = None,
    ):
        self._provider = provider
        self._api_key = api_key
        self._base_url = base_url
        self._default_headers = default_headers
        self._cost_tracker: ICostTracker | None = cost_tracker
        self._pricing = pricing

    def _callbacks(self) -> list[BaseCallbackHandler]:
        if self._cost_tracker is None:
            return []
        return [CostTrackingCallback(self._cost_tracker, self._provider, pricing=self._pricing)]

    async def _invoke(
        self,
        model_id: str,
        messages: list[dict],
        max_tokens: int,
        reasoning_effort: str | None,
        temperature: float | None,
        response_format: str | None,
    ) -> Any:
        chat = build_chat_model(
            provider=self._provider,
            model_id=model_id,
            api_key=self._api_key,
            base_url=self._base_url,
            default_headers=self._default_headers,
            max_tokens=max_tokens,
            reasoning_effort=reasoning_effort,
            temperature=temperature,
            response_format=response_format,
            callbacks=self._callbacks(),
        )
        return await chat.ainvoke(messages)

    @observe(name="langchain_llm_call")
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
            message = await self._invoke(
                model_id, messages, max_tokens, reasoning_effort, temperature, response_format
            )
        except (
            Exception
        ) as exc:  # rate-limit / transient -> single fallback, mirrors current 429 path
            if fallback_model_id and _is_rate_limit(exc):
                log.warning("rate_limit_fallback", primary=model_id, fallback=fallback_model_id)
                message = await self._invoke(
                    fallback_model_id, messages, max_tokens, None, temperature, response_format
                )
            else:
                raise

        content = message.content if isinstance(message.content, str) else str(message.content)
        finish_reason = (message.response_metadata or {}).get("finish_reason")
        if not content:
            raise LLMClientError(f"Empty content for {model_id}; finish_reason={finish_reason}")
        if finish_reason == "length":
            log.warning("completion_truncated", model=model_id, task=task, max_tokens=max_tokens)
        if return_reasoning:
            return {"content": content, "reasoning": _reasoning_from_message(message)}
        return content


def _is_rate_limit(exc: Exception) -> bool:
    if isinstance(exc, openai.RateLimitError):
        return True
    return "ratelimit" in type(exc).__name__.lower()


def _reasoning_from_message(message: Any) -> str:
    reasoning = message.additional_kwargs.get("reasoning")
    if isinstance(reasoning, str) and reasoning.strip():
        return reasoning.strip()
    # reuse the OpenRouter reasoning_details parser on the raw dict shape
    return _extract_reasoning_text(message.additional_kwargs)
