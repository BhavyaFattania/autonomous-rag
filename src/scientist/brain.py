# src/scientist/brain.py

import json
import time
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
    candidates = _fallback_candidates(state)
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
    candidates = _reranker_probe_candidates(state)
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
    candidates = _structured_exploration_candidates(state)
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


def _structured_exploration_candidates(state) -> list[dict]:
    index_configs = _available_index_configs(state)
    variants = [
        {"retriever": "dense", "top_k": 3, "hybrid_alpha": 1.0, "reranker": None, "reranker_top_n": None},
        {"retriever": "dense", "top_k": 5, "hybrid_alpha": 1.0, "reranker": None, "reranker_top_n": None},
        {"retriever": "dense", "top_k": 7, "hybrid_alpha": 1.0, "reranker": None, "reranker_top_n": None},
        {"retriever": "bm25", "top_k": 5, "hybrid_alpha": 0.0, "reranker": None, "reranker_top_n": None},
        {"retriever": "weighted_hybrid_rrf", "top_k": 5, "hybrid_alpha": 0.7, "reranker": None, "reranker_top_n": None},
        {"retriever": "weighted_hybrid_rrf", "top_k": 7, "hybrid_alpha": 0.3, "reranker": None, "reranker_top_n": None},
        {"retriever": "query_fusion_simple", "top_k": 5, "hybrid_alpha": 0.5, "fusion_num_queries": 1, "reranker": None, "reranker_top_n": None},
        {"retriever": "query_fusion_rrf", "top_k": 5, "hybrid_alpha": 0.7, "fusion_num_queries": 1, "reranker": None, "reranker_top_n": None},
        {"retriever": "sentence_window_dense", "top_k": 5, "hybrid_alpha": 1.0, "reranker": None, "reranker_top_n": None},
        {"retriever": "auto_merging", "top_k": 5, "hybrid_alpha": 1.0, "reranker": None, "reranker_top_n": None},
        {"retriever": "recursive", "top_k": 5, "hybrid_alpha": 1.0, "reranker": None, "reranker_top_n": None},
        {"retriever": "dense", "top_k": 5, "hybrid_alpha": 1.0, "reranker": "CohereRerank", "reranker_top_n": 5},
    ]
    return _combine_candidates(index_configs, variants, variants_first=True)


def _reranker_probe_candidates(state) -> list[dict]:
    index_configs = _available_index_configs(state)
    current_best = state.get("current_best_config", {})
    preferred_chunk = {
        "embedding_model": current_best.get("embedding_model"),
        "chunk_size": current_best.get("chunk_size"),
        "chunk_overlap": current_best.get("chunk_overlap"),
    }
    ordered_index_configs = sorted(
        index_configs,
        key=lambda item: 0 if all(item.get(k) == v for k, v in preferred_chunk.items()) else 1,
    )
    variants = [
        {"retriever": "dense", "top_k": 10, "hybrid_alpha": 1.0, "reranker": "CohereRerank", "reranker_top_n": 10},
        {"retriever": "weighted_hybrid_rrf", "top_k": 10, "hybrid_alpha": 0.7, "reranker": "CohereRerank", "reranker_top_n": 10},
        {"retriever": "query_fusion_rrf", "top_k": 10, "hybrid_alpha": 0.7, "fusion_num_queries": 1, "reranker": "CohereRerank", "reranker_top_n": 10},
    ]
    return _combine_candidates(ordered_index_configs, variants, variants_first=False)


def _fallback_candidates(state) -> list[dict]:
    indexed_configs = _available_index_configs(state)

    retrieval_variants = [
        {"retriever": "dense", "top_k": 10, "hybrid_alpha": 1.0, "reranker": None, "reranker_top_n": None},
        {"retriever": "weighted_hybrid_rrf", "top_k": 12, "hybrid_alpha": 0.7, "reranker": None, "reranker_top_n": None},
        {"retriever": "query_fusion_rrf", "top_k": 10, "hybrid_alpha": 0.7, "fusion_num_queries": 1, "reranker": None, "reranker_top_n": None},
        {"retriever": "bm25", "top_k": 10, "hybrid_alpha": 0.0, "reranker": None, "reranker_top_n": None},
        {"retriever": "dense", "top_k": 10, "hybrid_alpha": 1.0, "reranker": "CohereRerank", "reranker_top_n": 10},
    ]

    return _combine_candidates(indexed_configs, retrieval_variants, variants_first=False)


def _combine_candidates(index_configs: list[dict], variants: list[dict], variants_first: bool) -> list[dict]:
    candidates = []
    if variants_first:
        for variant in variants:
            for index_config in index_configs:
                candidates.append({
                    **index_config,
                    **variant,
                    "generator_model": "deepseek/deepseek-v4-flash",
                })
        return candidates

    for index_config in index_configs:
        for variant in variants:
            candidates.append({
                **index_config,
                **variant,
                "generator_model": "deepseek/deepseek-v4-flash",
            })
    return candidates


def _available_index_configs(state) -> list[dict]:
    from src.orchestrator.config_loader import load_run_settings

    settings = load_run_settings()
    indexed_configs = []
    from src.indexer.collection_manager import collection_is_cached, list_available_index_configs

    if not settings["evaluation"].get("allow_new_index_builds", True):
        indexed_configs = list_available_index_configs()
    if indexed_configs:
        return indexed_configs

    baseline = state.get("baseline_config") or state.get("current_best_config") or {}
    embedding_model = baseline.get("embedding_model", "openai/text-embedding-3-small")
    candidates = [
        {"embedding_model": embedding_model, "node_parser": "sentence", "chunk_size": 512, "chunk_overlap": 128},
        {"embedding_model": embedding_model, "node_parser": "sentence", "chunk_size": 768, "chunk_overlap": 128},
        {"embedding_model": embedding_model, "node_parser": "sentence", "chunk_size": 1024, "chunk_overlap": 200},
        {"embedding_model": embedding_model, "node_parser": "token", "chunk_size": 768, "chunk_overlap": 128},
        {"embedding_model": embedding_model, "node_parser": "sentence_window", "chunk_size": 512, "chunk_overlap": 64, "window_size": 3},
        {"embedding_model": embedding_model, "node_parser": "hierarchical", "chunk_size": 512, "chunk_overlap": 64},
    ]
    semantic_candidates = [
        {"embedding_model": embedding_model, "node_parser": "semantic", "chunk_size": 768, "chunk_overlap": 128, "semantic_threshold": 95, "semantic_buffer_size": 1},
        {"embedding_model": embedding_model, "node_parser": "semantic_double", "chunk_size": 768, "chunk_overlap": 128, "semantic_threshold": 90, "semantic_buffer_size": 1},
    ]
    if settings["evaluation"].get("allow_expensive_parser_builds", False):
        candidates.extend(semantic_candidates)
    else:
        from src.models.rag_config import RAGConfig

        for candidate in semantic_candidates:
            try:
                config = RAGConfig(
                    **candidate,
                    top_k=5,
                    hybrid_alpha=1.0,
                    retriever="dense",
                    reranker=None,
                    reranker_top_n=None,
                    generator_model="deepseek/deepseek-v4-flash",
                )
                if collection_is_cached(config):
                    candidates.append(candidate)
            except ValueError:
                continue
    return candidates


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
