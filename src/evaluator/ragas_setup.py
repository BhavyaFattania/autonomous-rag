"""Setup and configuration for RAGAS evaluation framework.

Provides utilities for building RAGAS-compatible LLM wrappers, embeddings, metrics,
and response validation. Provider-aware: `ModelConfig.provider` (default
"openrouter") picks the API key env var (via `src.core.provider_factory`) and
any provider-specific request quirks, so the judge/embedding model can be
served by OpenRouter, OpenAI, or a future provider without touching call sites.
"""

import os
from collections.abc import Callable

from config.models import ModelRouting
from langchain_core.outputs import LLMResult
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import (
    ContextUtilization,
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)

from src.core.provider_factory import required_env_var
from src.utils.json_repair import install_ragas_output_parser_compat_patch
from src.utils.logger import get_logger
from src.utils.openrouter import build_openrouter_headers

log = get_logger("evaluator")


def _resolve_api_key(provider: str, env: dict | None, api_key: str | None) -> str:
    """Resolve the API key for `provider`, preferring an explicit override.

    Raises `ValueError` (via `required_env_var`) for a provider unknown to
    `src.core.provider_factory`, rather than silently falling back to OpenRouter.
    """
    if api_key:
        return api_key
    env_var = required_env_var(provider)
    resolved = env.get(env_var) if env else os.environ[env_var]
    assert resolved is not None, f"{env_var} not found in env"
    return resolved


def build_ragas_llm(
    model_routing=ModelRouting, env=None, api_key: str | None = None
) -> LangchainLLMWrapper:
    """Build a RAGAS-compatible LLM wrapper for the judge's configured provider."""
    install_ragas_output_parser_compat_patch()
    judge_config = model_routing.ragas_judge
    provider = judge_config.provider
    model_kwargs = _build_openrouter_model_kwargs(judge_config)
    extra_body = _EXTRA_BODY_BUILDERS.get(provider, _no_extra_body)(judge_config)
    resolved_key = _resolve_api_key(provider, env, api_key)
    log.info(
        "ragas_judge_configured",
        model=judge_config.model_id,
        provider=provider,
        response_format=judge_config.response_format,
        include_reasoning=judge_config.reasoning,
    )
    llm = ChatOpenAI(
        model=judge_config.model_id,
        base_url=judge_config.base_url,
        api_key=resolved_key,
        temperature=judge_config.temperature,
        max_completion_tokens=judge_config.max_tokens,
        model_kwargs=model_kwargs,
        extra_body=extra_body,
        default_headers=_HEADER_BUILDERS.get(provider, _no_headers)(),
    )

    return LangchainLLMWrapper(llm, is_finished_parser=_ragas_generation_finished)


def build_ragas_embeddings(
    model_routing=ModelRouting, env=None, api_key: str | None = None
) -> OpenAIEmbeddings:
    """Build OpenAI-compatible embeddings for RAGAS metric calculation."""
    embedding_model = model_routing.ragas_embedding_model
    provider = embedding_model.provider
    resolved_key = _resolve_api_key(provider, env, api_key)
    return OpenAIEmbeddings(
        model=embedding_model.model_id,
        base_url=embedding_model.base_url,
        api_key=resolved_key,
        default_headers=_HEADER_BUILDERS.get(provider, _no_headers)(),
    )


def _build_openrouter_model_kwargs(judge_config) -> dict:
    """Extract model kwargs (e.g. response format) from judge config. This is
    plain OpenAI-spec JSON mode, so it applies unchanged across providers."""
    if judge_config.response_format == "json_object":
        return {"response_format": {"type": "json_object"}}
    return {}


def _build_openrouter_extra_body(judge_config) -> dict:
    """OpenRouter-specific request body options (e.g. reasoning exclusion)."""
    extra_body = {}
    if judge_config.reasoning is False:
        extra_body["reasoning"] = {"effort": "none", "exclude": True}
    return extra_body


def _no_extra_body(judge_config) -> dict:
    """Default extra_body for providers with no OpenRouter-style quirks."""
    return {}


def _no_headers() -> dict:
    """Default headers for providers that need no OpenRouter-style branding headers."""
    return {}


# Only OpenRouter needs special-cased headers/extra_body today (branding
# headers, its nested `reasoning` exclusion shape). Providers without an
# entry here — including future ones — get the plain OpenAI-spec defaults
# above; add an entry only when a provider actually needs different behavior.
_HEADER_BUILDERS: dict[str, Callable[[], dict]] = {
    "openrouter": build_openrouter_headers,
}
_EXTRA_BODY_BUILDERS: dict[str, Callable] = {
    "openrouter": _build_openrouter_extra_body,
}


def build_ragas_metrics(metric_names: list[str]):
    """Instantiate RAGAS metric objects from a list of metric names."""
    available_metrics = {
        "faithfulness": faithfulness,
        "answer_relevancy": answer_relevancy,
        "context_precision": context_precision,
        "context_recall": context_recall,
        "context_utilization": ContextUtilization(),
    }
    return [available_metrics[name] for name in metric_names if name in available_metrics]


def _ragas_generation_finished(response: LLMResult) -> bool:
    """Check if all LLM generations finished successfully or hit token limit."""
    finish_reasons = []
    for generation in response.flatten():
        item = generation.generations[0][0]
        reason = None
        if item.generation_info:
            reason = item.generation_info.get("finish_reason")
        message = getattr(item, "message", None)
        if reason is None and message is not None:
            reason = message.response_metadata.get("finish_reason")
        if reason is not None:
            finish_reasons.append(reason)

    if not finish_reasons:
        return True
    if any(reason == "length" for reason in finish_reasons):
        log.warning("ragas_judge_hit_token_limit", finish_reasons=finish_reasons)
    return all(reason in {"stop", "STOP", "MAX_TOKENS", "length"} for reason in finish_reasons)
