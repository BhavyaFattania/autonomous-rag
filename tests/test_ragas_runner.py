import pandas as pd
from src.evaluator.ragas_runner import _all_rows_failed, _metric_availability_warning, _safe_mean


def test_safe_mean_returns_zero_for_real_zero_score():
    df = pd.DataFrame({"faithfulness": [0.0, 0.0, 0.0]})

    assert _safe_mean(df, "faithfulness") == 0.0


def test_safe_mean_returns_zero_when_all_nan():
    df = pd.DataFrame({"faithfulness": [float("nan"), float("nan")]})

    assert _safe_mean(df, "faithfulness") == 0.0


def test_all_rows_failed_distinguishes_real_zero_from_all_nan():
    """The bug: _safe_mean alone makes a genuine 0.0000 score indistinguishable
    from every judge call failing. _all_rows_failed is what tells them apart."""
    real_zero = pd.DataFrame({"faithfulness": [0.0, 0.0, 0.0]})
    all_failed = pd.DataFrame({"faithfulness": [float("nan"), float("nan"), float("nan")]})

    assert _all_rows_failed(real_zero, "faithfulness") is False
    assert _all_rows_failed(all_failed, "faithfulness") is True


def test_all_rows_failed_false_when_only_some_rows_nan():
    partial = pd.DataFrame({"faithfulness": [0.8, float("nan"), 0.6]})

    assert _all_rows_failed(partial, "faithfulness") is False


def test_all_rows_failed_false_when_column_missing():
    df = pd.DataFrame({"other_metric": [0.5]})

    assert _all_rows_failed(df, "faithfulness") is False


def test_metric_availability_warning_marks_all_nan_scores_as_unavailable():
    df = pd.DataFrame(
        {
            "faithfulness": [float("nan"), float("nan")],
            "context_recall": [0.6, 0.7],
        }
    )

    warning = _metric_availability_warning(df, ["faithfulness", "context_recall"], questions=2)

    assert warning is not None
    assert "faithfulness" in warning
    assert "0.0" in warning
