"""
Experiment deduplication and config hash tracking.

Detects repeated configurations to prevent redundant trials and maintains
a rolling cleanup of stale hash records.
"""

import aiosqlite

from src.storage.repositories.config_hash_repository import ConfigHashRepository
from src.storage.repositories.experiment_repository import ExperimentRepository
from src.storage.write_coordinator import write_transaction
from src.utils.config_helpers import logical_config
from src.utils.function_trace import trace_call
from src.utils.logger import get_logger

log = get_logger("deduplicator")

_STALE_HASH_TTL_DAYS = 7


@trace_call
async def _fetch_best_historical_record(db, config_hash: str) -> dict:
    """Retrieve best experiment result for a config hash."""
    repo = ExperimentRepository(db)
    record = await repo.find_best_historical(config_hash)
    return {
        "score": record.score,
        "experiment_id": record.experiment_id,
        "metrics": record.metrics,
        "status": record.status,
        "hypothesis": record.hypothesis,
    }


def _reuse_historical_result(state: dict, historical: dict) -> dict | None:
    """Turn a completed duplicate into a zero-cost observation for acceptance."""
    score = historical["score"]
    metrics = historical["metrics"]
    if score is None or not metrics or "median_weighted_score" not in metrics:
        return None

    source_id = historical["experiment_id"]
    message = (
        f"Reused duplicate result from experiment {source_id}: "
        f"score={score:.4f}, status={historical['status']}."
    )
    return {
        "status": "RUNNING",
        "reused_duplicate": True,
        "duplicate_historical_experiment_id": source_id,
        "duplicate_historical_score": score,
        "duplicate_historical_metrics": metrics,
        "duplicate_historical_status": historical["status"],
        "duplicate_historical_hypothesis": historical["hypothesis"],
        "aggregated_metrics": metrics,
        "proposed_weighted_score": score,
        "evaluation_warnings": metrics.get("evaluation_warnings", []),
        "run_warnings": [*state.get("run_warnings", []), message],
    }


@trace_call
async def deduplicator_node(state, writer=None) -> dict:
    """Check if config was already tried; block duplicate or mark success; clean stale records."""
    from src.utils.hashing import get_config_hash

    config_hash = get_config_hash(logical_config(state["validated_config"]))

    async with write_transaction(writer) as db:
        exp_repo = ExperimentRepository(db)
        ch_repo = ConfigHashRepository(db)

        existing_id = await exp_repo.find_by_config_hash(config_hash)

        if existing_id:
            historical = await _fetch_best_historical_record(db, config_hash)
            reused = _reuse_historical_result(state, historical)
            if reused is not None:
                log.info(
                    "deduplicator_duplicate_reused",
                    config_hash=config_hash,
                    previous_score=historical["score"],
                    previous_experiment_id=historical["experiment_id"],
                )
                return reused
            score_str = (
                f"{historical['score']:.4f}" if historical["score"] is not None else "unknown"
            )
            log.info(
                "deduplicator_duplicate_found",
                config_hash=config_hash,
                previous_score=historical["score"],
                previous_status=historical["status"],
            )
            return {
                "status": "FAILED_DUPLICATE",
                "reused_duplicate": False,
                "duplicate_historical_experiment_id": None,
                "failure_reason": (
                    f"Config was already run. "
                    f"Previous result: status={historical['status']}, "
                    f"score={score_str}"
                ),
                "duplicate_historical_score": historical["score"],
                "duplicate_historical_metrics": historical["metrics"],
                "duplicate_historical_status": historical["status"],
                "duplicate_historical_hypothesis": historical["hypothesis"],
            }

        try:
            await ch_repo.insert(config_hash)
            await db.commit()
        except aiosqlite.IntegrityError:
            historical = await _fetch_best_historical_record(db, config_hash)
            reused = _reuse_historical_result(state, historical)
            if reused is not None:
                return reused
            score_str = (
                f"{historical['score']:.4f}" if historical["score"] is not None else "unknown"
            )
            return {
                "status": "FAILED_DUPLICATE",
                "reused_duplicate": False,
                "duplicate_historical_experiment_id": None,
                "failure_reason": (
                    f"Config was already proposed this run. "
                    f"Previous result: status={historical['status']}, "
                    f"score={score_str}"
                ),
                "duplicate_historical_score": historical["score"],
                "duplicate_historical_metrics": historical["metrics"],
                "duplicate_historical_status": historical["status"],
                "duplicate_historical_hypothesis": historical["hypothesis"],
            }

        removed = await ch_repo.delete_stale(ttl_days=_STALE_HASH_TTL_DAYS)
        if removed:
            log.info(
                "deduplicator_stale_hashes_cleaned", removed=removed, ttl_days=_STALE_HASH_TTL_DAYS
            )
        await db.commit()

    return {
        "status": "RUNNING",
        "reused_duplicate": False,
        "duplicate_historical_experiment_id": None,
    }
