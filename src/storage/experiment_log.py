import json
import uuid
import aiosqlite
from datetime import datetime, timezone
from src.storage.db import DB_PATH
from src.storage.cost_tracker import get_total
from src.utils.hashing import get_config_hash

async def recorder_node(state) -> dict:
    experiment_uuid = state.get("experiment_uuid") or str(uuid.uuid4())
    config_dict = state.get("validated_config", state.get("proposed_config", {}))
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
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
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
        await db.commit()
        
    completed = state.get("experiments_completed", 0) + 1
    accepted = state.get("experiments_accepted", 0)
    failures = state.get("consecutive_failures", 0)
    
    if status == "ACCEPTED":
        accepted += 1
        failures = 0
    elif status != "RUNNING":
        failures += 1
        
    successful = state.get("successful_patterns", [])
    failed = state.get("failed_patterns", [])
    
    if status == "ACCEPTED":
        successful.append(f"Score {proposed_score:.4f}: {state.get('hypothesis', '')}")
    elif status.startswith("FAILED_") or status == "REJECTED":
        failed.append(f"{status}: {state.get('hypothesis', '')}")
        
    return {
        "experiments_completed": completed,
        "experiments_accepted": accepted,
        "consecutive_failures": failures,
        "total_cost_usd": get_total(),
        "successful_patterns": successful,
        "failed_patterns": failed
    }
