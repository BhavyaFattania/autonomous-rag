import json
from datetime import datetime, timezone, timedelta

import aiosqlite

from src.storage.database import Database
from src.storage.repositories.experiment_repository import ExperimentRepository
from src.storage.repositories.config_hash_repository import ConfigHashRepository
from src.utils.config_helpers import logical_config
from src.utils.logger import get_logger
from src.utils.function_trace import trace_call

log = get_logger("deduplicator")

_STALE_HASH_TTL_DAYS = 7


@trace_call
async def _fetch_best_historical_record(db, config_hash: str) -> dict:
    repo = ExperimentRepository(db)
    record = await repo.find_best_historical(config_hash)
    return {
        "score": record.score,
        "metrics": record.metrics,
        "status": record.status,
        "hypothesis": record.hypothesis,
    }


@trace_call
async def deduplicator_node(state) -> dict:
    from src.utils.hashing import get_config_hash

    config_hash = get_config_hash(logical_config(state["validated_config"]))

    async with Database().connect() as db:
        exp_repo = ExperimentRepository(db)
        ch_repo = ConfigHashRepository(db)

        existing_id = await exp_repo.find_by_config_hash(config_hash)

        if existing_id:
            historical = await _fetch_best_historical_record(db, config_hash)
            score_str = f"{historical['score']:.4f}" if historical["score"] is not None else "unknown"
            log.info(
                "deduplicator_duplicate_found",
                config_hash=config_hash,
                previous_score=historical["score"],
                previous_status=historical["status"],
            )
            return {
                "status": "FAILED_DUPLICATE",
                "failure_reason": (
                    f"Config was already run. "
                    f"Previous result: status={historical['status']}, "
                    f"score={score_str}"
                ),
                "duplicate_historical_score":   historical["score"],
                "duplicate_historical_metrics": historical["metrics"],
                "duplicate_historical_status":  historical["status"],
                "duplicate_historical_hypothesis": historical["hypothesis"],
            }

        try:
            await ch_repo.insert(config_hash)
            await db.commit()
        except aiosqlite.IntegrityError:
            historical = await _fetch_best_historical_record(db, config_hash)
            score_str = f"{historical['score']:.4f}" if historical["score"] is not None else "unknown"
            return {
                "status": "FAILED_DUPLICATE",
                "failure_reason": (
                    f"Config was already proposed this run. "
                    f"Previous result: status={historical['status']}, "
                    f"score={score_str}"
                ),
                "duplicate_historical_score":   historical["score"],
                "duplicate_historical_metrics": historical["metrics"],
                "duplicate_historical_status":  historical["status"],
                "duplicate_historical_hypothesis": historical["hypothesis"],
            }

        removed = await ch_repo.delete_stale(ttl_days=_STALE_HASH_TTL_DAYS)
        if removed:
            log.info("deduplicator_stale_hashes_cleaned", removed=removed, ttl_days=_STALE_HASH_TTL_DAYS)
        await db.commit()

    return {"status": "RUNNING"}
