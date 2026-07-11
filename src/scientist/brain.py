import json
import random
import re
import time
import uuid

from config.loader import load_model_routing

from src.core.provider import Provider
from src.scientist.prompt_builder import build_history_lines, build_scientist_prompt
from src.scientist.proposal import (
    fallback_proposal,
    reranker_probe_proposal,
    structured_exploration_proposal,
)
from src.utils.function_trace import trace_call
from src.utils.langfuse_compat import observe
from src.utils.logger import get_logger
from src.utils.openrouter import call_openrouter

log = get_logger("scientist")
model_routing = load_model_routing()
scientist_llm = model_routing.scientist


@trace_call
def _should_run_structured_exploration(state, settings) -> bool:
    limit = settings.explore_exploit.structured_exploration_experiments
    return state.get("experiments_completed", 0) < limit


@trace_call
def _should_force_reranker_probe(state, settings) -> bool:
    every_n = settings.explore_exploit.reranker_probe_every_n_experiments
    experiment_number = state.get("experiments_completed", 0) + 1
    return every_n > 0 and experiment_number % every_n == 0


@observe(name="scientist_node")
@trace_call(log_return=False)
async def scientist_node(state, settings, provider: Provider | None = None) -> dict:
    from src.utils.conversation_summary import sliding_window_compress

    history_lines = build_history_lines(state)
    existing_summary = state.get("history_summary", "")
    recent_history, new_history_summary = await sliding_window_compress(
        history_lines,
        recent_k=10,
        existing_summary=existing_summary,
    )

    if _should_run_structured_exploration(state, settings):
        result = await structured_exploration_proposal(state, settings)
        if result is not None:
            return {**result, "history_summary": new_history_summary}
        log.info("structured_exploration_exhausted_falling_through_to_llm")

    if _should_force_reranker_probe(state, settings):
        result = await reranker_probe_proposal(state, settings)
        if result is not None:
            return {**result, "history_summary": new_history_summary}
        log.info("reranker_probe_exhausted_falling_through_to_llm")

    exploit = random.random() < settings.explore_exploit.exploit_probability
    prompt = build_scientist_prompt(
        state,
        exploit,
        recent_history=recent_history,
        history_summary=new_history_summary,
        settings=settings,
    )

    try:
        started = time.perf_counter()
        log.info("scientist_llm_start", exploit=exploit)
        llm = provider.llm_client if provider else None
        if llm:
            raw_response = await llm.call(
                model_id=scientist_llm.model_id,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=scientist_llm.max_tokens,
                task=scientist_llm.task,
                reasoning_effort=scientist_llm.reasoning_effort,
                temperature=scientist_llm.temperature,
                return_reasoning=True,
                response_format=scientist_llm.response_format,
            )
        else:
            raw_response = await call_openrouter(
                model_id="deepseek/deepseek-v4-pro",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=8192,
                task="scientist",
                reasoning_effort="high",
                temperature=None,
                return_reasoning=True,
                fallback_model_id=None,
                response_format="json_object",
            )
        log.info("scientist_llm_complete", elapsed_sec=round(time.perf_counter() - started, 2))
    except Exception as e:
        log.error("scientist_llm_failed", error=str(e))
        fallback = await fallback_proposal(state, f"Scientist API call failed: {e}", settings)
        return {**fallback, "history_summary": new_history_summary}

    reasoning_text = ""
    if isinstance(raw_response, dict):
        reasoning_text = str(raw_response.get("reasoning") or "").strip()
        raw_response = raw_response.get("content", "")

    if not isinstance(raw_response, str) or not raw_response.strip():
        log.warning("scientist_empty_response")
        fallback = await fallback_proposal(state, "Scientist returned empty content", settings)
        return {**fallback, "history_summary": new_history_summary}

    cleaned = raw_response.strip()
    cleaned = re.sub(r"```(?:json)?", "", cleaned).strip().rstrip("`").strip()

    try:
        config_dict = json.loads(cleaned)
    except json.JSONDecodeError as e:
        log.warning("scientist_json_parse_failed", raw=cleaned[-500:], error=str(e))
        fallback = await fallback_proposal(state, f"Scientist returned invalid JSON: {e}", settings)
        return {**fallback, "history_summary": new_history_summary}

    hypothesis = config_dict.pop("hypothesis", "")
    if len(hypothesis) > 500:
        hypothesis = hypothesis[:500]

    log.info("scientist_proposed", hypothesis=hypothesis, config=config_dict)

    return {
        "experiment_uuid": str(uuid.uuid4()),
        "proposed_config": config_dict,
        "hypothesis": hypothesis,
        "scientist_reasoning": reasoning_text,
        "status": "RUNNING",
        "history_summary": new_history_summary,
    }
