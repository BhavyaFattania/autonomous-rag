import os
import yaml
import asyncio
from ragas.llms import LangchainLLMWrapper
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.outputs import LLMResult
from ragas.metrics import (
    ContextUtilization,
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)
from src.utils.logger import get_logger
from src.utils.openrouter import build_openrouter_headers
from src.utils.json_repair import install_ragas_output_parser_compat_patch

log = get_logger("evaluator")


def build_ragas_llm() -> LangchainLLMWrapper:
    install_ragas_output_parser_compat_patch()
    judge_config = _load_ragas_judge_config()
    model_kwargs = _build_openrouter_model_kwargs(judge_config)
    extra_body = _build_openrouter_extra_body(judge_config)
    model_id = judge_config.get("model_id", "qwen/qwen3.5-flash-02-23")
    log.info(
        "ragas_judge_configured",
        model=model_id,
        response_format=judge_config.get("response_format"),
        exclude_reasoning=judge_config.get("exclude_reasoning"),
    )
    llm = ChatOpenAI(
        model=model_id,
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        temperature=judge_config.get("temperature", 0.0),
        max_tokens=judge_config.get("max_tokens", 4096),
        model_kwargs=model_kwargs,
        extra_body=extra_body,
        default_headers=build_openrouter_headers(),
    )
    return LangchainLLMWrapper(llm, is_finished_parser=_ragas_generation_finished)


def build_ragas_embeddings(model_name: str) -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=model_name,
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
    )


def _build_openrouter_model_kwargs(judge_config: dict) -> dict:
    if judge_config.get("response_format") == "json_object":
        return {"response_format": {"type": "json_object"}}
    return {}


def _build_openrouter_extra_body(judge_config: dict) -> dict:
    extra_body = {}
    if judge_config.get("exclude_reasoning", True):
        extra_body["reasoning"] = {"effort": "none", "exclude": True}
    return extra_body


def _load_ragas_judge_config() -> dict:
    try:
        with open("config/model_routing.yaml") as f:
            routing = yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}
    return routing.get("models", {}).get("ragas_judge", {})


def build_ragas_metrics(metric_names: list[str]):
    available_metrics = {
        "faithfulness": faithfulness,
        "answer_relevancy": answer_relevancy,
        "context_precision": context_precision,
        "context_recall": context_recall,
        "context_utilization": ContextUtilization(),
    }
    return [
        available_metrics[name]
        for name in metric_names
        if name in available_metrics
    ]


def _ragas_generation_finished(response: LLMResult) -> bool:
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
