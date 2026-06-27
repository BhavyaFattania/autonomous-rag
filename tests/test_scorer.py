from src.evaluator.scorer import acceptance_node
from src.models.metrics import AggregatedMetrics, SingleRunMetrics
from config.settings import Settings, AcceptanceSettings


def test_acceptance_promotes_any_positive_gain_when_enabled():
    settings = Settings(acceptance=AcceptanceSettings(
        accept_any_score_gain=True,
        min_weighted_score_improvement=0.03,
        competitive_score_tolerance=0.02,
        max_variance_between_runs=0.035,
        max_metric_regression=0.02,
    ))
    run = SingleRunMetrics(
        context_recall=0.5,
        recall_at_k=1.0,
        precision_at_k=0.2,
        ndcg_at_k=1.0,
        mrr=1.0,
    )
    metrics = AggregatedMetrics.from_runs([run])

    result = acceptance_node({
        "aggregated_metrics": metrics.model_dump(),
        "current_best_weighted_score": run.weighted_score - 0.001,
        "current_best_metrics": {"recall_at_k": 1.0},
        "validated_config": {"chunk_size": 512, "_collection_name": "internal"},
    }, settings=settings)

    assert result["status"] == "ACCEPTED"
    assert result["current_best_config"] == {"chunk_size": 512}
