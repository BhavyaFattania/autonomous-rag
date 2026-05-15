import statistics
from src.models.metrics import AggregatedMetrics, SingleRunMetrics
from src.utils.logger import get_logger
from src.orchestrator.config_loader import load_run_settings

log = get_logger("scorer")

def acceptance_node(state) -> dict:
    """
    Determines if the proposed config should be accepted as the new best.
    Uses median across 3 runs (robust to outliers).
    Three checks: minimum improvement, variance, per-metric regression.
    """
    settings = load_run_settings()
    thresholds = settings["acceptance"]

    metrics = AggregatedMetrics(**state["aggregated_metrics"])
    baseline_score = state["current_best_weighted_score"]
    proposed_score = metrics.median_weighted_score

    # Check 1: Minimum relative improvement
    relative_improvement = (proposed_score - baseline_score) / max(baseline_score, 1e-6)
    if relative_improvement < thresholds["min_weighted_score_improvement"]:
        reason = (
            f"Insufficient improvement: {relative_improvement:.4f} < "
            f"{thresholds['min_weighted_score_improvement']} required. "
            f"Proposed={proposed_score:.4f}, Baseline={baseline_score:.4f}"
        )
        log.info("experiment_rejected", reason=reason)
        return {"status": "REJECTED", "failure_reason": reason}

    # Check 2: Variance across 3 runs
    if metrics.std_dev_weighted_score > thresholds["max_variance_between_runs"]:
        reason = (
            f"High variance: std_dev={metrics.std_dev_weighted_score:.4f} > "
            f"{thresholds['max_variance_between_runs']} threshold"
        )
        log.info("experiment_rejected", reason=reason)
        return {"status": "REJECTED", "failure_reason": reason}

    # Check 3: No single metric may regress by more than max_metric_regression
    best_metrics_dict = state.get("current_best_metrics", {})
    if best_metrics_dict:
        current_best_metrics = SingleRunMetrics(**best_metrics_dict)
        for metric_name in ("faithfulness", "answer_relevancy", "context_recall", "context_precision"):
            proposed_val = getattr(metrics, f"median_{metric_name}")
            best_val = getattr(current_best_metrics, metric_name)
            regression = best_val - proposed_val
            if regression > thresholds["max_metric_regression"]:
                reason = (
                    f"Metric regression on {metric_name}: dropped by {regression:.4f} "
                    f"(max allowed: {thresholds['max_metric_regression']})"
                )
                log.info("experiment_rejected", reason=reason)
                return {"status": "REJECTED", "failure_reason": reason}

    # All checks passed — accept
    log.info(
        "experiment_accepted",
        proposed_score=proposed_score,
        previous_best=baseline_score,
        relative_gain=relative_improvement,
    )
    return {
        "status": "ACCEPTED",
        "current_best_config": state["validated_config"].copy(),
        "current_best_weighted_score": proposed_score,
        "current_best_metrics": {
            "faithfulness": metrics.median_faithfulness,
            "answer_relevancy": metrics.median_answer_relevancy,
            "context_recall": metrics.median_context_recall,
            "context_precision": metrics.median_context_precision,
        },
        "failure_reason": "",
    }
