# src/scientist/brain.py

import json
import re
import random
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
    from src.orchestrator.config_loader import load_run_settings
    from src.utils.conversation_summary import sliding_window_compress
    settings = load_run_settings()

    # ── Sliding-window history compression ──────────────────────────────────
    # Run unconditionally so history_summary is always up-to-date in state.
    # When len(history) <= 10 the function returns immediately with no LLM call.
    history_lines = _build_history_lines(state)
    existing_summary = state.get("history_summary", "")
    recent_history, new_history_summary = await sliding_window_compress(
        history_lines,
        recent_k=10,
        existing_summary=existing_summary,
    )
    # ────────────────────────────────────────────────────────────────────────

    if _should_run_structured_exploration(state, settings):
        result = await _structured_exploration_proposal(state)
        return {**result, "history_summary": new_history_summary}

    if _should_force_reranker_probe(state, settings):
        result = await _reranker_probe_proposal(state)
        return {**result, "history_summary": new_history_summary}

    exploit = random.random() < settings["explore_exploit"]["exploit_probability"]
    prompt = _build_scientist_prompt(
        state,
        exploit,
        recent_history=recent_history,
        history_summary=new_history_summary,
    )

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
        fallback = await _fallback_proposal(state, f"Scientist API call failed: {e}")
        return {**fallback, "history_summary": new_history_summary}

    reasoning_text = ""
    if isinstance(raw_response, dict):
        reasoning_text = str(raw_response.get("reasoning") or "").strip()
        raw_response = raw_response.get("content", "")

    # v2.1: raw_response IS already the final answer.
    # OpenRouter puts reasoning in reasoning_details; content field is clean.
    # Do NOT strip <think> tags.
    if not isinstance(raw_response, str) or not raw_response.strip():
        log.warning("scientist_empty_response")
        fallback = await _fallback_proposal(state, "Scientist returned empty content")
        return {**fallback, "history_summary": new_history_summary}

    cleaned = raw_response.strip()

    # Remove markdown code fences if the model added them despite instructions
    cleaned = re.sub(r"```(?:json)?", "", cleaned).strip().rstrip("`").strip()

    try:
        config_dict = json.loads(cleaned)
    except json.JSONDecodeError as e:
        log.warning("scientist_json_parse_failed", raw=cleaned[-500:], error=str(e))
        fallback = await _fallback_proposal(state, f"Scientist returned invalid JSON: {e}")
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


def _build_history_lines(state) -> list[str]:
    """Build the combined ACCEPTED/REJECTED history line list from state patterns."""
    lines = []
    for i, pattern in enumerate(state.get("successful_patterns", [])):
        lines.append(f"ACCEPTED[{i+1}]: {pattern}")
    for i, pattern in enumerate(state.get("failed_patterns", [])):
        lines.append(f"REJECTED[{i+1}]: {pattern}")
    return lines


def _build_scientist_prompt(
    state,
    exploit: bool,
    *,
    recent_history: list[str] | None = None,
    history_summary: str = "",
) -> str:
    """Build the scientist prompt.

    Args:
        state: Current WorkflowState.
        exploit: True = exploit mode, False = explore mode.
        recent_history: Pre-compressed recent history lines from sliding-window
            middleware. If None, falls back to building history from state directly
            (backward-compatible for direct test calls).
        history_summary: LLM-compressed summary of older history entries.
    """
    from pathlib import Path
    from src.orchestrator.config_loader import load_run_settings

    settings = load_run_settings()  # cached — no disk I/O after first call
    system_prompt = Path("prompts/scientist_v1.txt").read_text()

    search_space = settings.get("search_space") or {}
    allowed_node_parsers = search_space.get("allowed_node_parsers")
    allowed_chunk_sizes = search_space.get("allowed_chunk_sizes")
    allowed_chunk_overlaps = search_space.get("allowed_chunk_overlaps")

    indexed_configs_text = "Any valid chunk_size/chunk_overlap pair."
    if not settings["evaluation"].get("allow_new_index_builds", True):
        from src.indexer.collection_manager import list_available_index_configs
        indexed_configs = list_available_index_configs()

        # Filter available index configs according to search space constraints
        filtered_configs = []
        for iconfig in indexed_configs:
            if allowed_node_parsers is not None and iconfig.get("node_parser") not in allowed_node_parsers:
                continue
            if allowed_chunk_sizes is not None and iconfig.get("chunk_size") not in allowed_chunk_sizes:
                continue
            if allowed_chunk_overlaps is not None and iconfig.get("chunk_overlap") not in allowed_chunk_overlaps:
                continue
            filtered_configs.append(iconfig)
        indexed_configs = filtered_configs

        indexed_configs_text = json.dumps(indexed_configs, indent=2)

    # ── History block (sliding-window aware) ─────────────────────────────────
    if recent_history is not None:
        # Pre-compressed path: show summary of old entries + recent verbatim.
        parts = []
        if history_summary:
            parts.append(f"[Compressed summary of older experiments]\n{history_summary}")
        if recent_history:
            parts.append("[Recent experiments (verbatim)]\n" + "\n".join(recent_history))
        history_text = "\n\n".join(parts) if parts else ""
    else:
        # Fallback path (e.g. direct test calls): truncate from full history in state.
        history_lines = _build_history_lines(state)
        history_text = _truncate_history(
            history_lines,
            max_chars=settings["reflection"]["max_history_tokens"] * 4,
        )
    # ─────────────────────────────────────────────────────────────────────────

    mode = "EXPLOIT (refine near current best)" if exploit else "EXPLORE (try something new)"

    # Build developer constraints prompt text
    constraints_lines = []
    for key, label in [
        ("allowed_node_parsers", "node_parser"),
        ("allowed_retrievers", "retriever"),
        ("allowed_chunk_sizes", "chunk_size"),
        ("allowed_chunk_overlaps", "chunk_overlap"),
        ("allowed_generator_models", "generator_model"),
        ("allowed_rerankers", "reranker"),
    ]:
        allowed = search_space.get(key)
        if allowed is not None:
            constraints_lines.append(f"- {label}: must be one of {allowed}")
            
    constraints_text = ""
    if constraints_lines:
        constraints_text = "\nCRITICAL DEVELOPER CONSTRAINTS (You must strictly follow these rules):\n" + "\n".join(constraints_lines) + "\n"

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
{constraints_text}
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
