# src/scientist/brain.py

import json
import uuid
from src.utils.openrouter import call_openrouter
from src.utils.logger import get_logger

log = get_logger("scientist")

async def scientist_node(state) -> dict:
    """
    Calls the scientist LLM (DeepSeek V4 Pro with reasoning) to propose the next config.
    Returns only the fields this node owns: proposed_config, hypothesis.
    On any failure, sets status=FAILED_API_ERROR or FAILED_VALIDATION.
    """
    import random
    from src.orchestrator.config_loader import load_run_settings
    settings = load_run_settings()

    exploit = random.random() < settings["explore_exploit"]["exploit_probability"]
    prompt = _build_scientist_prompt(state, exploit)

    try:
        # v2.1: reasoning_effort="high", temperature=None (must be None when reasoning is set)
        raw_response = await call_openrouter(
            model_id="deepseek/deepseek-v4-pro",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            task="scientist",
            reasoning_effort="high",
            temperature=None,       # MUST be None when reasoning_effort is set
            fallback_model_id=None, # No fallback for scientist — V4 Pro is required
        )
    except Exception as e:
        log.error("scientist_llm_failed", error=str(e))
        return {"status": "FAILED_API_ERROR", "failure_reason": f"Scientist API call failed: {e}"}

    # v2.1: raw_response IS already the final answer.
    # OpenRouter puts reasoning in reasoning_details; content field is clean.
    # Do NOT strip <think> tags.
    cleaned = raw_response.strip()

    # Remove markdown code fences if the model added them despite instructions
    import re
    cleaned = re.sub(r"```(?:json)?", "", cleaned).strip().rstrip("`").strip()

    try:
        config_dict = json.loads(cleaned)
    except json.JSONDecodeError as e:
        log.warning("scientist_json_parse_failed", raw=cleaned[:200], error=str(e))
        return {"status": "FAILED_VALIDATION", "failure_reason": f"Scientist returned invalid JSON: {e}"}

    hypothesis = config_dict.pop("hypothesis", "")
    if len(hypothesis) > 500:
        hypothesis = hypothesis[:500]

    log.info("scientist_proposed", hypothesis=hypothesis, config=config_dict)

    return {
        "experiment_uuid": str(uuid.uuid4()),
        "proposed_config": config_dict,
        "hypothesis": hypothesis,
        "status": "RUNNING",
    }


def _build_scientist_prompt(state, exploit: bool) -> str:
    from pathlib import Path
    system_prompt = Path("prompts/scientist_v1.txt").read_text()

    history_lines = []
    for i, pattern in enumerate(state.get("successful_patterns", [])):
        history_lines.append(f"ACCEPTED[{i+1}]: {pattern}")
    for i, pattern in enumerate(state.get("failed_patterns", [])):
        history_lines.append(f"REJECTED[{i+1}]: {pattern}")

    mode = "EXPLOIT (refine near current best)" if exploit else "EXPLORE (try something new)"

    user_message = f"""
System instructions:
{system_prompt}

Current best config:
{json.dumps(state.get("current_best_config", {}), indent=2)}

Current best weighted score: {state.get("current_best_weighted_score", 0.0):.4f}

Experiment history:
{chr(10).join(history_lines) if history_lines else "No experiments yet. Start from baseline."}

Reflection summary:
{state.get("reflection_summary", "No reflection yet.")}

Mode for this experiment: {mode}

Respond with ONLY the JSON object.
"""
    return user_message.strip()
