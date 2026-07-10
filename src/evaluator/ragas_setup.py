"""Setup and configuration for RAGAS evaluation framework.

Provides utilities for building RAGAS-compatible LLM wrappers, embeddings, metrics,
and response validation against OpenRouter API.
"""

import os

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

from src.utils.json_repair import install_ragas_output_parser_compat_patch
from src.utils.logger import get_logger
from src.utils.openrouter import build_openrouter_headers

log = get_logger("evaluator")


def build_ragas_llm(
    model_routing=ModelRouting, env=None, api_key: str | None = None
) -> LangchainLLMWrapper:
    """Build a RAGAS-compatible LLM wrapper configured for OpenRouter judging."""
    install_ragas_output_parser_compat_patch()
    judge_config = model_routing.ragas_judge
    model_kwargs = _build_openrouter_model_kwargs(judge_config)
    extra_body = _build_openrouter_extra_body(judge_config)
    model_id = judge_config.model_id
    resolved_key = api_key or (
        env.get("OPENROUTER_API_KEY") if env else os.environ["OPENROUTER_API_KEY"]
    )
    log.info(
        "ragas_judge_configured",
        model=model_id,
        response_format=judge_config.response_format,
        include_reasoning=judge_config.reasoning,
    )
    llm = ChatOpenAI(
        model=model_id,
        base_url="https://openrouter.ai/api/v1",
        api_key=resolved_key,
        temperature=judge_config.temperature,
        max_completion_tokens=judge_config.max_tokens,
        model_kwargs=model_kwargs,
        extra_body=extra_body,
        default_headers=build_openrouter_headers(),
    )

    return LangchainLLMWrapper(llm, is_finished_parser=_ragas_generation_finished)


def build_ragas_embeddings(
    model_name: str, env=None, api_key: str | None = None
) -> OpenAIEmbeddings:
    """Build OpenAI-compatible embeddings for RAGAS metric calculation."""
    resolved_key = api_key or (
        env.get("OPENROUTER_API_KEY") if env else os.environ["OPENROUTER_API_KEY"]
    )
    return OpenAIEmbeddings(
        model=model_name,
        base_url="https://openrouter.ai/api/v1",
        api_key=resolved_key,
    )


def _build_openrouter_model_kwargs(judge_config) -> dict:
    """Extract model kwargs (e.g. response format) from judge config."""
    if judge_config.response_format == "json_object":
        return {"response_format": {"type": "json_object"}}
    return {}


def _build_openrouter_extra_body(judge_config) -> dict:
    """Build OpenRouter-specific request body options (e.g. reasoning exclusion)."""
    extra_body = {}
    if judge_config.reasoning is False:
        extra_body["reasoning"] = {"effort": "none", "exclude": True}
    return extra_body


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
