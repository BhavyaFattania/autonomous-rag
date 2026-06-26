import json
import uuid
from datetime import datetime, timezone

import aiosqlite

from src.storage.database import Database
from src.storage.models import Experiment
from src.storage.repositories.experiment_repository import ExperimentRepository
from src.storage.repositories.config_hash_repository import ConfigHashRepository
from src.storage.cost_tracker import get_total
from src.utils.config_helpers import logical_config
from src.utils.hashing import get_config_hash

PIPELINE_FAILURE_STATUSES = {
    "FAILED_SMOKE",
    "FAILED_TIMEOUT",
    "FAILED_API_ERROR",
    "FAILED_VALIDATION",
}


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
    config_dict = logical_config(config_source)
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

    experiment = Experiment(
        experiment_uuid=experiment_uuid,
        run_id=state["run_id"],
        config_hash=config_hash,
        config_json=json.dumps(config_dict),
        hypothesis=state.get("hypothesis", ""),
        status=status,
        failure_reason=failure_reason,
        metrics_json=metrics_json,
        baseline_score=baseline_score,
        proposed_score=proposed_score,
        cost_usd=cost,
        started_at=started_at,
        finished_at=finished_at,
    )

    async with Database().connect() as db:
        exp_repo = ExperimentRepository(db)
        ch_repo = ConfigHashRepository(db)

        experiment_id = await exp_repo.insert(experiment)

        if config_hash and proposed_score is not None:
            await ch_repo.update_score(config_hash, proposed_score)
        await db.commit()

    completed = state.get("experiments_completed", 0) + 1
    accepted = state.get("experiments_accepted", 0)
    failures = state.get("consecutive_failures", 0)
    repeated = state.get("experiments_repeated", 0)
    experiments_competitive = state.get("experiments_competitive", 0)

    if status == "ACCEPTED":
        accepted += 1
    elif status == "REJECTED":
        failures += 1
    elif status == "COMPETITIVE":
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
        "failed_patterns": failed,
    }
