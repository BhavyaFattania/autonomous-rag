import json

from src.storage.experiment_log import _serialize_metrics


def test_serialize_metrics_persists_non_fatal_evaluation_warnings():
    warning = "RAGAS judge warning across 2 question(s): no usable scores for faithfulness."

    payload = json.loads(_serialize_metrics({"median_weighted_score": 0.8}, [warning], 12))

    assert payload["median_weighted_score"] == 0.8
    assert payload["evaluation_warnings"] == [warning]
    assert payload["reused_from_experiment_id"] == 12
