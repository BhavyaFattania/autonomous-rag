import uuid
import aiosqlite
import src.storage.db as storage_db
from src.models.rag_config import RAGConfig
from src.utils.hashing import get_config_hash
from src.utils.logger import get_logger

log = get_logger("scientist")


async def fallback_proposal(state, reason: str) -> dict:
    from src.scientist.candidates import get_fallback_candidates
    candidates = get_fallback_candidates(state)
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


async def reranker_probe_proposal(state) -> dict:
    from src.scientist.candidates import get_reranker_probe_candidates
    candidates = get_reranker_probe_candidates(state)
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


async def structured_exploration_proposal(state) -> dict:
    from src.scientist.candidates import get_structured_exploration_candidates
    candidates = get_structured_exploration_candidates(state)
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


async def select_unused_candidate(candidates: list[dict], state) -> dict:
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
