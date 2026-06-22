import json
import uuid
import aiosqlite
from datetime import datetime, timezone
import src.storage.db as storage_db
from src.storage.cost_tracker import get_total
from src.utils.hashing import get_config_hash

PIPELINE_FAILURE_STATUSES = {
    "FAILED_SMOKE",
    "FAILED_TIMEOUT",
    "FAILED_API_ERROR",
    "FAILED_VALIDATION",
}

def _logical_config(config: dict) -> dict:
    return {k: v for k, v in config.items() if not k.startswith("_")}


def _config_summary(config: dict) -> str:
    if not config:
        return "config=<none>"
    reranker = config.get("reranker") or "None"
    return (
        f"parser={config.get('node_parser', 'sentence')} "
        f"retriever={config.get('retriever', 'weighted_hybrid_rrf')} "
        f"chunk={config.get('chunk_size')}/{config.get('chunk_overlap')} "
        f"top_k={config.get('top_k')} "
        f"alpha={config.get('hybrid_alpha')} "
        f"reranker={reranker}"
    )

async def recorder_node(state) -> dict:
    experiment_uuid = state.get("experiment_uuid") or str(uuid.uuid4())
    config_source = state.get("validated_config") or state.get("proposed_config", {})
    config_dict = _logical_config(config_source)
    config_hash = get_config_hash(config_dict) if config_dict else ""

    status = state.get("status", "FAILED_UNKNOWN")
    failure_reason = state.get("failure_reason", "")

    metrics = state.get("aggregated_metrics", {})
    metrics_json = json.dumps(metrics) if metrics else None

    proposed_score = state.get("proposed_weighted_score", 0.0)
    baseline_score = state.get("current_best_weighted_score", 0.0)
    cost = state.get("experiment_cost_usd", 0.0)

    started_at = state.get("experiment_started_at", datetime.now(timezone.utc).isoformat())
    finished_at = datetime.now(timezone.utc).isoformat()

    async with aiosqlite.connect(storage_db.DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO experiments
            (experiment_uuid, run_id, config_hash, config_json, hypothesis, status, failure_reason,
             metrics_json, baseline_score, proposed_score, cost_usd, started_at, finished_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            experiment_uuid,
            state["run_id"],
            config_hash,
            json.dumps(config_dict),
            state.get("hypothesis", ""),
            status,
            failure_reason,
            metrics_json,
            baseline_score,
            proposed_score,
            cost,
            started_at,
            finished_at
        ))
        # Update the config_hashes row with the best score achieved
        if config_hash and proposed_score is not None:
            await db.execute("""
                UPDATE config_hashes
                SET score = MAX(COALESCE(score, 0.0), ?)
                WHERE config_hash = ?
            """, (proposed_score, config_hash))
        await db.commit()
        experiment_id = cursor.lastrowid

    completed = state.get("experiments_completed", 0) + 1
    accepted = state.get("experiments_accepted", 0)
    failures = state.get("consecutive_failures", 0)
    repeated = state.get("experiments_repeated", 0)
    experiments_competitive = state.get("experiments_competitive", 0)
    
    if status == "ACCEPTED":
        accepted += 1
        # Do NOT reset failures — never reinitialise counters to zero during a run.
    elif status == "REJECTED":
        # Failed to meet improvement requirements — counts as a failure.
        failures += 1
    elif status == "COMPETITIVE":
        # Near-best but not promoted. Increment both the dedicated competitive counter
        # and the failure counter so a long COMPETITIVE streak triggers the stop limit.
        experiments_competitive += 1
        failures += 1
    elif status == "FAILED_DUPLICATE":
        repeated += 1
    elif status in PIPELINE_FAILURE_STATUSES:
        failures += 1

    successful = state.get("successful_patterns", [])
    failed = state.get("failed_patterns", [])
    summary = _config_summary(config_dict)

    if status == "ACCEPTED":
        gain = proposed_score - baseline_score
        successful.append(
            f"{summary} score={proposed_score:.4f} gain={gain:+.4f}: {state.get('hypothesis', '')}"
        )
    elif status == "COMPETITIVE":
        successful.append(
            f"COMPETITIVE {summary} score={proposed_score:.4f} best={baseline_score:.4f}: {state.get('hypothesis', '')}"
        )
    elif (status.startswith("FAILED_") and status != "FAILED_DUPLICATE") or status == "REJECTED":
        failed.append(
            f"{status} {summary} score={proposed_score:.4f} best={baseline_score:.4f}: {state.get('hypothesis', '')}"
        )

    return {
        "experiment_id": experiment_id,
        "status": status,
        "experiments_completed": completed,
        "experiments_accepted": accepted,
        "consecutive_failures": failures,
        "experiments_repeated": repeated,
        "experiments_competitive": experiments_competitive,
        "total_cost_usd": get_total(),
        "successful_patterns": successful,
        "failed_patterns": failed
    }
