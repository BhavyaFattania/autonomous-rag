"""RAG evaluation metrics models for single runs and aggregated results."""

from pydantic import BaseModel


class SingleRunMetrics(BaseModel):
    """Metrics from a single RAG generation run."""

    faithfulness: float = 0.0
    answer_relevancy: float = 0.0
    context_recall: float = 0.0
    context_precision: float = 0.0
    context_utilization: float = 0.0
    recall_at_k: float = 0.0
    precision_at_k: float = 0.0
    ndcg_at_k: float = 0.0
    mrr: float = 0.0

    @property
    def weighted_score(self) -> float:
        """Composite score: 35% recall_at_k + 25% ndcg + 20% mrr + 10% precision + 10% context_recall."""
        return (
            0.35 * self.recall_at_k
            + 0.25 * self.ndcg_at_k
            + 0.20 * self.mrr
            + 0.10 * self.precision_at_k
            + 0.10 * self.context_recall
        )


class AggregatedMetrics(BaseModel):
    """Aggregated metrics across multiple runs (up to 3) with median values and variance."""

    run_1: SingleRunMetrics
    run_2: SingleRunMetrics | None = None
    run_3: SingleRunMetrics | None = None
    median_faithfulness: float
    median_answer_relevancy: float
    median_context_recall: float
    median_context_precision: float
    median_context_utilization: float = 0.0
    median_recall_at_k: float = 0.0
    median_precision_at_k: float = 0.0
    median_ndcg_at_k: float = 0.0
    median_mrr: float = 0.0
    median_weighted_score: float
    std_dev_weighted_score: float  # Standard deviation across 3 runs (not variance)

    @classmethod
    def from_runs(cls, runs: list[SingleRunMetrics]) -> "AggregatedMetrics":
        """Aggregate metrics from multiple runs by computing medians and std dev of weighted scores."""
        import statistics

        if not runs:
            raise ValueError("At least 1 run required")

        def _median(key):
            return statistics.median([getattr(r, key) for r in runs])

        scores = [r.weighted_score for r in runs]
        return cls(
            run_1=runs[0],
            run_2=runs[1] if len(runs) > 1 else None,
            run_3=runs[2] if len(runs) > 2 else None,
            median_faithfulness=_median("faithfulness"),
            median_answer_relevancy=_median("answer_relevancy"),
            median_context_recall=_median("context_recall"),
            median_context_precision=_median("context_precision"),
            median_context_utilization=_median("context_utilization"),
            median_recall_at_k=_median("recall_at_k"),
            median_precision_at_k=_median("precision_at_k"),
            median_ndcg_at_k=_median("ndcg_at_k"),
            median_mrr=_median("mrr"),
            median_weighted_score=statistics.median(scores),
            std_dev_weighted_score=statistics.stdev(scores) if len(scores) > 1 else 0.0,
        )
