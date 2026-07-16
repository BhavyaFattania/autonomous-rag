import pytest
from src.models.metrics import AggregatedMetrics


def test_aggregated_metrics_from_runs_rejects_empty_runs():
    with pytest.raises(ValueError, match="At least 1 run required"):
        AggregatedMetrics.from_runs([])
