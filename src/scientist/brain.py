# src/scientist/brain.py

import json
import time
import uuid
try:
    from langfuse.decorators import observe
except ImportError:
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

from src.utils.openrouter import call_openrouter
from src.utils.logger import get_logger

log = get_logger("scientist")

@observe(name="scientist_node")
async def scientist_node(state) -> dict:
    """
    Calls the scientist LLM (DeepSeek V4 Pro with reasoning) to propose the next config.
    Returns only the fields this node owns: proposed_config, hypothesis.
    On any failure, sets status=FAILED_API_ERROR or FAILED_VALIDATION.
    """
    import random
    from src.orchestrator.config_loader import load_run_settings
    settings = load_run_settings()

    if _should_run_structured_exploration(state, settings):
        return await _structured_exploration_proposal(state)

    if _should_force_reranker_probe(state, settings):
        return await _reranker_probe_proposal(state)

    exploit = random.random() < settings["explore_exploit"]["exploit_probability"]
    prompt = _build_scientist_prompt(state, exploit)

    try:
        # v2.1: reasoning_effort="high", temperature=None (must be None when reasoning is set)
        started = time.perf_counter()
        log.info("scientist_llm_start", exploit=exploit)
        raw_response = await call_openrouter(
            model_id="deepseek/deepseek-v4-pro",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=8192,
            task="scientist",
            reasoning_effort="high",
            temperature=None,       # MUST be None when reasoning_effort is set
            return_reasoning=True,
            fallback_model_id=None, # No fallback for scientist — V4 Pro is required
        )
        log.info("scientist_llm_complete", elapsed_sec=round(time.perf_counter() - started, 2))
    except Exception as e:
        log.error("scientist_llm_failed", error=str(e))
        return await _fallback_proposal(state, f"Scientist API call failed: {e}")

    reasoning_text = ""
    if isinstance(raw_response, dict):
        reasoning_text = str(raw_response.get("reasoning") or "").strip()
        raw_response = raw_response.get("content", "")

    # v2.1: raw_response IS already the final answer.
    # OpenRouter puts reasoning in reasoning_details; content field is clean.
    # Do NOT strip <think> tags.
    if not isinstance(raw_response, str) or not raw_response.strip():
        log.warning("scientist_empty_response")
        return await _fallback_proposal(state, "Scientist returned empty content")

    cleaned = raw_response.strip()

    # Remove markdown code fences if the model added them despite instructions
    import re
    cleaned = re.sub(r"```(?:json)?", "", cleaned).strip().rstrip("`").strip()

    try:
        config_dict = json.loads(cleaned)
    except json.JSONDecodeError as e:
        log.warning("scientist_json_parse_failed", raw=cleaned[-500:], error=str(e))
        return await _fallback_proposal(state, f"Scientist returned invalid JSON: {e}")

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
    }


async def _fallback_proposal(state, reason: str) -> dict:
    from src.scientist.candidates import get_fallback_candidates
    candidates = get_fallback_candidates(state)
    selected = await _select_unused_candidate(candidates, state)

    hypothesis = "Fallback local proposal after scientist LLM returned no usable config."
    log.warning("scientist_fallback_proposed", reason=reason, config=selected)
    return {
        "experiment_uuid": str(uuid.uuid4()),
        "proposed_config": selected,
        "hypothesis": hypothesis,
        "status": "RUNNING",
        "failure_reason": "",
    }


async def _reranker_probe_proposal(state) -> dict:
    from src.scientist.candidates import get_reranker_probe_candidates
    candidates = get_reranker_probe_candidates(state)
    selected = await _select_unused_candidate(candidates, state)

    hypothesis = "Periodic reranker probe tests whether Cohere preserves recall evidence."
    log.info("scientist_forced_reranker_probe", config=selected)
    return {
        "experiment_uuid": str(uuid.uuid4()),
        "proposed_config": selected,
        "hypothesis": hypothesis,
        "status": "RUNNING",
        "failure_reason": "",
    }


async def _structured_exploration_proposal(state) -> dict:
    from src.scientist.candidates import get_structured_exploration_candidates
    candidates = get_structured_exploration_candidates(state)
    selected = await _select_unused_candidate(candidates, state)

    hypothesis = "Structured exploration covers chunking and retrieval modes before exploitation."
    log.info("scientist_structured_exploration", config=selected)
    return {
        "experiment_uuid": str(uuid.uuid4()),
        "proposed_config": selected,
        "hypothesis": hypothesis,
        "status": "RUNNING",
        "failure_reason": "",
    }


async def _select_unused_candidate(candidates: list[dict], state) -> dict:
    from src.models.rag_config import RAGConfig
    from src.utils.hashing import get_config_hash
    import src.storage.db as storage_db
    import aiosqlite

    used_hashes = set()
    try:
        async with aiosqlite.connect(storage_db.DB_PATH) as db:
            cursor = await db.execute(
                """
                SELECT config_hash FROM experiments
                WHERE config_hash IS NOT NULL AND config_hash != ''
                  AND status NOT IN ('FAILED_VALIDATION')
                UNION
                SELECT config_hash FROM config_hashes
                """
            )
            used_hashes = {row[0] for row in await cursor.fetchall()}
    except Exception as e:
        log.warning("scientist_fallback_dedup_unavailable", error=str(e))

    selected = None
    for candidate in candidates:
        try:
            config = RAGConfig(**candidate).model_dump()
        except ValueError:
            continue
        if get_config_hash(config) not in used_hashes:
            selected = config
            break
    if selected is None:
        for candidate in candidates:
            try:
                selected = RAGConfig(**candidate).model_dump()
                break
            except ValueError:
                continue
    if selected is None:
        raise ValueError("No valid candidate configs available for scientist proposal")
    return selected


def _should_run_structured_exploration(state, settings: dict) -> bool:
    limit = settings["explore_exploit"].get("structured_exploration_experiments", 0)
    return state.get("experiments_completed", 0) < limit


def _should_force_reranker_probe(state, settings: dict) -> bool:
    every_n = settings["explore_exploit"].get("reranker_probe_every_n_experiments", 0)
    experiment_number = state.get("experiments_completed", 0) + 1
    return every_n > 0 and experiment_number % every_n == 0




def _build_scientist_prompt(state, exploit: bool) -> str:
    from pathlib import Path
    from src.orchestrator.config_loader import load_run_settings

    settings = load_run_settings()
    system_prompt = Path("prompts/scientist_v1.txt").read_text()
    indexed_configs_text = "Any valid chunk_size/chunk_overlap pair."
    if not settings["evaluation"].get("allow_new_index_builds", True):
        from src.indexer.collection_manager import list_available_index_configs
        indexed_configs = list_available_index_configs()
        indexed_configs_text = json.dumps(indexed_configs, indent=2)

    history_lines = []
    for i, pattern in enumerate(state.get("successful_patterns", [])):
        history_lines.append(f"ACCEPTED[{i+1}]: {pattern}")
    for i, pattern in enumerate(state.get("failed_patterns", [])):
        history_lines.append(f"REJECTED[{i+1}]: {pattern}")
    history_text = _truncate_history(
        history_lines,
        max_chars=settings["reflection"]["max_history_tokens"] * 4,
    )

    mode = "EXPLOIT (refine near current best)" if exploit else "EXPLORE (try something new)"

    user_message = f"""
System instructions:
{system_prompt}

Current best config:
{json.dumps(state.get("current_best_config", {}), indent=2)}

Current best composite retrieval score: {state.get("current_best_weighted_score", 0.0):.4f}

Active scoring metric:
Composite retrieval score from Recall@K, Precision@K, nDCG@K, MRR, and periodic
RAGAS context metrics. Prioritize parser, retriever, top_k, hybrid_alpha, and
reranker only when it is likely to improve the retrieval evidence.

Experiment history:
{history_text if history_text else "No experiments yet. Start from baseline."}

Reflection summary:
{state.get("reflection_summary", "No reflection yet.")}

Allowed indexed configurations:
{indexed_configs_text}

If allowed indexed configurations are listed, choose only one of those
embedding_model/node_parser/chunk_size/chunk_overlap/parser-param combinations.
Other retrieval parameters may vary.

Mode for this experiment: {mode}

Respond with ONLY the JSON object.
"""
    return user_message.strip()


def _truncate_history(history_lines: list[str], max_chars: int) -> str:
    selected = []
    total = 0
    for line in reversed(history_lines):
        line_len = len(line) + 1
        if selected and total + line_len > max_chars:
            break
        selected.append(line)
        total += line_len
    return "\n".join(reversed(selected))
