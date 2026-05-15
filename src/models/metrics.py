from pydantic import BaseModel

class SingleRunMetrics(BaseModel):
    faithfulness: float
    answer_relevancy: float
    context_recall: float
    context_precision: float

    @property
    def weighted_score(self) -> float:
        return (
            self.answer_relevancy * 0.35
            + self.faithfulness * 0.30
            + self.context_recall * 0.20
            + self.context_precision * 0.15
        )

class AggregatedMetrics(BaseModel):
    run_1: SingleRunMetrics
    run_2: SingleRunMetrics
    run_3: SingleRunMetrics
    median_faithfulness: float
    median_answer_relevancy: float
    median_context_recall: float
    median_context_precision: float
    median_weighted_score: float
    std_dev_weighted_score: float   # Standard deviation across 3 runs (not variance)

    @classmethod
    def from_runs(cls, runs: list[SingleRunMetrics]) -> "AggregatedMetrics":
        import statistics
        assert len(runs) == 3, "Exactly 3 runs required"

        def _median(key):
            return statistics.median([getattr(r, key) for r in runs])

        scores = [r.weighted_score for r in runs]
        return cls(
            run_1=runs[0], run_2=runs[1], run_3=runs[2],
            median_faithfulness=_median("faithfulness"),
            median_answer_relevancy=_median("answer_relevancy"),
            median_context_recall=_median("context_recall"),
            median_context_precision=_median("context_precision"),
            median_weighted_score=statistics.median(scores),
            std_dev_weighted_score=statistics.stdev(scores),
        )
