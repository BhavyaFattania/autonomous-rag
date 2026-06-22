import aiosqlite
import json
import src.storage.db as storage_db
from src.utils.logger import get_logger

log = get_logger("deduplicator")

# Stale proposed-hash TTL: rows older than this with no completed experiment are orphans.
_STALE_HASH_TTL_DAYS = 7


def _logical_config(config: dict) -> dict:
    return {k: v for k, v in config.items() if not k.startswith("_")}


async def _fetch_best_historical_record(db, config_hash: str) -> dict:
    """Fetch the best-scoring historical experiment for this config hash.

    Returns a dict with keys: score, metrics, status, hypothesis.
    All values default to None / empty if no record is found.
    """
    cursor = await db.execute(
        """
        SELECT proposed_score, metrics_json, status, hypothesis
        FROM experiments
        WHERE config_hash = ?
          AND status NOT IN ('FAILED_VALIDATION')
        ORDER BY proposed_score DESC NULLS LAST
        LIMIT 1
        """,
        (config_hash,),
    )
    row = await cursor.fetchone()
    if not row:
        return {"score": None, "metrics": {}, "status": "unknown", "hypothesis": ""}

    proposed_score, metrics_json, status, hypothesis = row
    metrics = {}
    if metrics_json:
        try:
            metrics = json.loads(metrics_json)
        except (json.JSONDecodeError, TypeError):
            metrics = {}

    return {
        "score": proposed_score,
        "metrics": metrics,
        "status": status,
        "hypothesis": hypothesis or "",
    }


async def deduplicator_node(state) -> dict:
    from src.utils.hashing import get_config_hash
    from datetime import datetime, timezone, timedelta

    config_hash = get_config_hash(_logical_config(state["validated_config"]))

    async with aiosqlite.connect(storage_db.DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT experiment_id FROM experiments
            WHERE config_hash=?
              AND status NOT IN ('FAILED_VALIDATION')
            LIMIT 1
            """,
            (config_hash,),
        )
        row = await cursor.fetchone()

        if row:
            # Fetch the previous result so the scientist gets real performance context,
            # not just "was already run". This lets it understand what that config achieved.
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
            await db.execute(
                """
                INSERT INTO config_hashes (config_hash, first_seen, score)
                VALUES (?, ?, NULL)
                """,
                (config_hash, datetime.now(timezone.utc).isoformat()),
            )
            await db.commit()
        except aiosqlite.IntegrityError:
            # Hash already in config_hashes (proposed but not yet completed).
            # Still try to fetch historical data if a completed experiment exists.
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

        # Clean up orphaned proposed-hash rows: older than TTL with no completed experiment.
        # This prevents stale entries from crashed runs blocking future valid proposals.
        cutoff = (datetime.now(timezone.utc) - timedelta(days=_STALE_HASH_TTL_DAYS)).isoformat()
        result = await db.execute(
            """
            DELETE FROM config_hashes
            WHERE first_seen < ?
              AND score IS NULL
              AND config_hash NOT IN (
                  SELECT config_hash FROM experiments
                  WHERE status NOT IN ('FAILED_VALIDATION')
              )
            """,
            (cutoff,),
        )
        if result.rowcount:
            log.info("deduplicator_stale_hashes_cleaned", removed=result.rowcount, ttl_days=_STALE_HASH_TTL_DAYS)
        await db.commit()

    return {"status": "RUNNING"}

