"""LangChain-backed ILLMClient adapter + ChatOpenAI factory.

Replaces the hand-rolled OpenRouterClient/OpenAIClient. One ChatOpenAI engine
for nodes and the RAGAS judge; cost recorded via CostTrackingCallback.
"""

from __future__ import annotations

from typing import Any

from langchain_core.callbacks import BaseCallbackHandler
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

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
