import random
import uuid

from src.storage.database import Database
from src.storage.repositories.experiment_repository import ExperimentRepository
from src.models.rag_config import RAGConfig
from src.utils.hashing import get_config_hash
from src.utils.logger import get_logger
from src.utils.function_trace import trace_call

log = get_logger("scientist")


@trace_call
async def fallback_proposal(state, reason: str, settings) -> dict:
    from src.scientist.candidates import get_fallback_candidates
    candidates = get_fallback_candidates(state, settings)
    selected = await select_unused_candidate(candidates, state)

    hypothesis = "Fallback local proposal after scientist LLM returned no usable config."
    log.warning("scientist_fallback_proposed", reason=reason, config=selected)
    return {
        "experiment_uuid": str(uuid.uuid4()),
        "proposed_config": selected,
        "hypothesis": hypothesis,
        "status": "RUNNING",
        "failure_reason": "",
    }


@trace_call
async def reranker_probe_proposal(state, settings) -> dict:
    from src.scientist.candidates import get_reranker_probe_candidates
    candidates = get_reranker_probe_candidates(state, settings)
    selected = await select_unused_candidate(candidates, state)

    hypothesis = "Periodic reranker probe tests whether Cohere preserves recall evidence."
    log.info("scientist_forced_reranker_probe", config=selected)
    return {
        "experiment_uuid": str(uuid.uuid4()),
        "proposed_config": selected,
        "hypothesis": hypothesis,
        "status": "RUNNING",
        "failure_reason": "",
    }


@trace_call
async def structured_exploration_proposal(state, settings) -> dict:
    from src.scientist.candidates import get_structured_exploration_candidates
    candidates = get_structured_exploration_candidates(state, settings)
    selected = await select_unused_candidate(candidates, state)

    hypothesis = "Structured exploration covers chunking and retrieval modes before exploitation."
    log.info("scientist_structured_exploration", config=selected)
    return {
        "experiment_uuid": str(uuid.uuid4()),
        "proposed_config": selected,
        "hypothesis": hypothesis,
        "status": "RUNNING",
        "failure_reason": "",
    }


@trace_call
async def select_unused_candidate(candidates: list[dict], state) -> dict:
    used_hashes: set[str] = set()
    try:
        async with Database().connect() as db:
            repo = ExperimentRepository(db)
            used_hashes = await repo.find_used_hashes()
    except Exception as e:
        log.warning("scientist_fallback_dedup_unavailable", error=str(e))

    # Shuffle to avoid always picking the same candidate[0] across runs
    shuffled = list(candidates)
    random.shuffle(shuffled)

    selected = None
    for candidate in shuffled:
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
