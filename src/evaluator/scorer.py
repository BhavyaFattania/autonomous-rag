"""Scoring and acceptance logic for RAG configuration experiments.

Evaluates proposed configurations against baseline using weighted median scores,
variance thresholds, and metric regression guards.
"""

from src.models.metrics import AggregatedMetrics, SingleRunMetrics
from src.utils.config_helpers import logical_config
from src.utils.function_trace import trace_call
from src.utils.logger import get_logger

log = get_logger("scorer")


@trace_call
def acceptance_node(state, settings) -> dict:
    """
    Determines if the proposed config should be accepted as the new best.
    Uses median across runs and guards against variance/recall regressions.
    """
    thresholds = settings.acceptance

    metrics = AggregatedMetrics(**state["aggregated_metrics"])
    baseline_score = state["current_best_weighted_score"]
    proposed_score = metrics.median_weighted_score
    relative_improvement = (proposed_score - baseline_score) / max(baseline_score, 1e-6)

    if proposed_score > baseline_score and thresholds.accept_any_score_gain:
        return _accept_best_config(
            state,
            metrics,
            proposed_score,
            baseline_score,
            relative_improvement,
        )

    if relative_improvement < thresholds.min_weighted_score_improvement:
        if proposed_score >= baseline_score - thresholds.competitive_score_tolerance:
            reason = (
                f"Competitive result: {relative_improvement:.4f} < "
                f"{thresholds.min_weighted_score_improvement} required. "
                f"Proposed={proposed_score:.4f}, Baseline={baseline_score:.4f}"
            )
            log.info("experiment_competitive", reason=reason)
            return {"status": "COMPETITIVE", "failure_reason": reason}
        reason = (
            f"Insufficient improvement: {relative_improvement:.4f} < "
            f"{thresholds.min_weighted_score_improvement} required. "
            f"Proposed={proposed_score:.4f}, Baseline={baseline_score:.4f}"
        )
        log.info("experiment_rejected", reason=reason)
        return {"status": "REJECTED", "failure_reason": reason}

    if metrics.std_dev_weighted_score > thresholds.max_variance_between_runs:
        reason = (
            f"High variance: std_dev={metrics.std_dev_weighted_score:.4f} > "
            f"{thresholds.max_variance_between_runs} threshold"
        )
        log.info("experiment_rejected", reason=reason)
        return {"status": "REJECTED", "failure_reason": reason}

    best_metrics_dict = state.get("current_best_metrics", {})
    if best_metrics_dict:
        current_best_metrics = SingleRunMetrics(**best_metrics_dict)
        max_regression = thresholds.max_metric_regression

        # Guard all three primary IR metrics — not just recall
        metric_regressions = {
            "recall_at_k": current_best_metrics.recall_at_k - metrics.median_recall_at_k,
            "ndcg_at_k": current_best_metrics.ndcg_at_k - metrics.median_ndcg_at_k,
            "mrr": current_best_metrics.mrr - metrics.median_mrr,
        }
        for metric_name, regression in metric_regressions.items():
            if regression > max_regression:
                reason = (
                    f"Metric regression on {metric_name}: dropped by {regression:.4f} "
                    f"(max allowed: {max_regression})"
                )
                log.info("experiment_rejected", reason=reason)
                return {"status": "REJECTED", "failure_reason": reason}

    return _accept_best_config(
        state,
        metrics,
        proposed_score,
        baseline_score,
        relative_improvement,
    )


def _accept_best_config(
    state: dict,
    metrics: AggregatedMetrics,
    proposed_score: float,
    baseline_score: float,
    relative_improvement: float,
) -> dict:
    """Log acceptance and return updated state with new best config and metrics."""
    log.info(
        "experiment_accepted",
        proposed_score=proposed_score,
        previous_best=baseline_score,
        relative_gain=relative_improvement,
    )
    return {
        "status": "ACCEPTED",
        "current_best_config": logical_config(state["validated_config"]),
        "current_best_weighted_score": proposed_score,
        "current_best_metrics": {
            "faithfulness": metrics.median_faithfulness,
            "answer_relevancy": metrics.median_answer_relevancy,
            "context_recall": metrics.median_context_recall,
            "context_precision": metrics.median_context_precision,
            "context_utilization": metrics.median_context_utilization,
            "recall_at_k": metrics.median_recall_at_k,
            "precision_at_k": metrics.median_precision_at_k,
            "ndcg_at_k": metrics.median_ndcg_at_k,
            "mrr": metrics.median_mrr,
        },
        "failure_reason": "",
    }
