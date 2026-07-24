from config.settings import AcceptanceSettings, Settings
from src.evaluator.scorer import acceptance_node
from src.models.metrics import AggregatedMetrics, SingleRunMetrics

# Shared thresholds for every test below that needs accept_any_score_gain=False
# to reach the deeper branches (competitive/variance/regression) instead of
# short-circuiting on the first `if proposed_score > baseline_score` check.
_THRESHOLDS = AcceptanceSettings(
    accept_any_score_gain=False,
    min_weighted_score_improvement=0.03,
    competitive_score_tolerance=0.02,
    max_variance_between_runs=0.035,
    max_metric_regression=0.02,
)


def test_acceptance_promotes_any_positive_gain_when_enabled():
    settings = Settings(
        acceptance=AcceptanceSettings(
            accept_any_score_gain=True,
            min_weighted_score_improvement=0.03,
            competitive_score_tolerance=0.02,
            max_variance_between_runs=0.035,
            max_metric_regression=0.02,
        )
    )
    run = SingleRunMetrics(
        context_recall=0.5,
        recall_at_k=1.0,
        precision_at_k=0.2,
        ndcg_at_k=1.0,
        mrr=1.0,
    )
    metrics = AggregatedMetrics.from_runs([run])

    result = acceptance_node(
        {
            "aggregated_metrics": metrics.model_dump(),
            "current_best_weighted_score": run.weighted_score - 0.001,
            "current_best_metrics": {"recall_at_k": 1.0},
            "validated_config": {"chunk_size": 512, "_collection_name": "internal"},
        },
        settings=settings,
    )

    assert result["status"] == "ACCEPTED"
    assert result["current_best_config"] == {"chunk_size": 512}


def test_acceptance_rejects_insufficient_improvement():
    """relative_improvement below the threshold, and too far below baseline
    to count as competitive -> REJECTED."""
    settings = Settings(acceptance=_THRESHOLDS)
    run = SingleRunMetrics(
        context_recall=0.1, recall_at_k=0.1, precision_at_k=0.1, ndcg_at_k=0.1, mrr=0.1
    )
    metrics = AggregatedMetrics.from_runs([run])  # weighted_score == 0.1

    result = acceptance_node(
        {
            "aggregated_metrics": metrics.model_dump(),
            "current_best_weighted_score": 0.5,
            "current_best_metrics": {},
            "validated_config": {"chunk_size": 512},
        },
        settings=settings,
    )

    assert result["status"] == "REJECTED"
    assert "Insufficient improvement" in result["failure_reason"]


def test_acceptance_marks_competitive_near_miss():
    """Below the improvement threshold but within competitive_score_tolerance
    of baseline -> COMPETITIVE, not REJECTED."""
    settings = Settings(acceptance=_THRESHOLDS)
    # weighted_score = 0.49, baseline = 0.5: within the 0.02 tolerance band.
    run = SingleRunMetrics(
        context_recall=0.49, recall_at_k=0.49, precision_at_k=0.49, ndcg_at_k=0.49, mrr=0.49
    )
    metrics = AggregatedMetrics.from_runs([run])

    result = acceptance_node(
        {
            "aggregated_metrics": metrics.model_dump(),
            "current_best_weighted_score": 0.5,
            "current_best_metrics": {},
            "validated_config": {"chunk_size": 512},
        },
        settings=settings,
    )

    assert result["status"] == "COMPETITIVE"
    assert "Competitive result" in result["failure_reason"]


def test_acceptance_rejects_high_variance_between_runs():
    """Improvement clears the threshold, but std_dev across runs exceeds
    max_variance_between_runs -> REJECTED as unstable, before ever reaching
    the metric-regression guard."""
    settings = Settings(acceptance=_THRESHOLDS)
    high = SingleRunMetrics(
        context_recall=1.0, recall_at_k=1.0, precision_at_k=1.0, ndcg_at_k=1.0, mrr=1.0
    )
    low = SingleRunMetrics(
        context_recall=0.1, recall_at_k=0.1, precision_at_k=0.1, ndcg_at_k=0.1, mrr=0.1
    )
    metrics = AggregatedMetrics.from_runs([high, low])  # median 0.55, huge std_dev

    result = acceptance_node(
        {
            "aggregated_metrics": metrics.model_dump(),
            "current_best_weighted_score": 0.5,
            "current_best_metrics": {},
            "validated_config": {"chunk_size": 512},
        },
        settings=settings,
    )

    assert result["status"] == "REJECTED"
    assert "High variance" in result["failure_reason"]


def test_acceptance_rejects_recall_regression():
    """recall_at_k regressing past max_metric_regression rejects even though
    ndcg/mrr improve and the overall weighted score clears the improvement
    threshold -- the per-metric guard is independent of the composite score."""
    settings = Settings(acceptance=_THRESHOLDS)
    run = SingleRunMetrics(
        context_recall=1.0, recall_at_k=0.5, precision_at_k=1.0, ndcg_at_k=0.9, mrr=0.9
    )
    metrics = AggregatedMetrics.from_runs([run])

    result = acceptance_node(
        {
            "aggregated_metrics": metrics.model_dump(),
            "current_best_weighted_score": 0.5,
            "current_best_metrics": {"recall_at_k": 1.0, "ndcg_at_k": 0.1, "mrr": 0.1},
            "validated_config": {"chunk_size": 512},
        },
        settings=settings,
    )

    assert result["status"] == "REJECTED"
    assert "recall_at_k" in result["failure_reason"]


def test_acceptance_rejects_ndcg_regression():
    settings = Settings(acceptance=_THRESHOLDS)
    run = SingleRunMetrics(
        context_recall=1.0, recall_at_k=0.9, precision_at_k=1.0, ndcg_at_k=0.5, mrr=0.9
    )
    metrics = AggregatedMetrics.from_runs([run])

    result = acceptance_node(
        {
            "aggregated_metrics": metrics.model_dump(),
            "current_best_weighted_score": 0.5,
            "current_best_metrics": {"recall_at_k": 0.1, "ndcg_at_k": 1.0, "mrr": 0.1},
            "validated_config": {"chunk_size": 512},
        },
        settings=settings,
    )

    assert result["status"] == "REJECTED"
    assert "ndcg_at_k" in result["failure_reason"]


def test_acceptance_rejects_mrr_regression():
    settings = Settings(acceptance=_THRESHOLDS)
    run = SingleRunMetrics(
        context_recall=1.0, recall_at_k=0.9, precision_at_k=1.0, ndcg_at_k=0.9, mrr=0.5
    )
    metrics = AggregatedMetrics.from_runs([run])

    result = acceptance_node(
        {
            "aggregated_metrics": metrics.model_dump(),
            "current_best_weighted_score": 0.5,
            "current_best_metrics": {"recall_at_k": 0.1, "ndcg_at_k": 0.1, "mrr": 1.0},
            "validated_config": {"chunk_size": 512},
        },
        settings=settings,
    )

    assert result["status"] == "REJECTED"
    assert "mrr" in result["failure_reason"]


def test_acceptance_bootstraps_without_prior_best_metrics():
    """No current_best_metrics yet (first-ever acceptance) must skip the
    per-metric regression guard entirely rather than crashing or rejecting,
    and fall through to ACCEPTED once improvement/variance checks pass."""
    settings = Settings(acceptance=_THRESHOLDS)
    run = SingleRunMetrics(
        context_recall=1.0, recall_at_k=1.0, precision_at_k=1.0, ndcg_at_k=1.0, mrr=1.0
    )
    metrics = AggregatedMetrics.from_runs([run])

    result = acceptance_node(
        {
            "aggregated_metrics": metrics.model_dump(),
            "current_best_weighted_score": 0.5,
            "validated_config": {"chunk_size": 512},
            # current_best_metrics intentionally absent
        },
        settings=settings,
    )

    assert result["status"] == "ACCEPTED"
