import json
import re
import random
import time
import uuid
from src.utils.langfuse_compat import observe
from src.utils.openrouter import call_openrouter
from src.utils.logger import get_logger
from src.scientist.prompt_builder import build_scientist_prompt, _build_history_lines
from src.scientist.proposal import (
    fallback_proposal, reranker_probe_proposal,
    structured_exploration_proposal, select_unused_candidate,
)

log = get_logger("scientist")


def _should_run_structured_exploration(state, settings) -> bool:
    limit = settings.explore_exploit.structured_exploration_experiments
    return state.get("experiments_completed", 0) < limit


def _should_force_reranker_probe(state, settings) -> bool:
    every_n = settings.explore_exploit.reranker_probe_every_n_experiments
    experiment_number = state.get("experiments_completed", 0) + 1
    return every_n > 0 and experiment_number % every_n == 0


@observe(name="scientist_node")
async def scientist_node(state, settings=None) -> dict:
    from src.utils.conversation_summary import sliding_window_compress

    history_lines = _build_history_lines(state)
    existing_summary = state.get("history_summary", "")
    recent_history, new_history_summary = await sliding_window_compress(
        history_lines,
        recent_k=10,
        existing_summary=existing_summary,
    )

    if _should_run_structured_exploration(state, settings):
        result = await structured_exploration_proposal(state, settings)
        return {**result, "history_summary": new_history_summary}

    if _should_force_reranker_probe(state, settings):
        result = await reranker_probe_proposal(state, settings)
        return {**result, "history_summary": new_history_summary}

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
        raw_response = await call_openrouter(
            model_id="deepseek/deepseek-v4-pro",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=8192,
            task="scientist",
            reasoning_effort="high",
            temperature=None,
            return_reasoning=True,
            fallback_model_id=None,
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
