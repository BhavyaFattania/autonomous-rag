"""Tests for compute_config_diff(), which powers the hero panel's
'Live Configuration Diff' (chunk_size 768, up from 512, etc)."""

from src.tui.formatting import compute_config_diff


def test_same_value_is_marked_same():
    rows = compute_config_diff({"retriever": "hybrid"}, {"retriever": "hybrid"})
    assert rows == [("retriever", "hybrid", "same")]


def test_numeric_increase_shows_up_arrow_with_previous_value():
    rows = compute_config_diff({"chunk_size": 768}, {"chunk_size": 512})
    assert rows == [("chunk_size", 768, "↑ from 512")]


def test_numeric_decrease_shows_down_arrow_with_previous_value():
    rows = compute_config_diff({"top_k": 5}, {"top_k": 10})
    assert rows == [("top_k", 5, "↓ from 10")]


def test_non_numeric_change_is_marked_changed():
    rows = compute_config_diff({"reranker": "cohere"}, {"reranker": None})
    assert rows == [("reranker", "cohere", "changed")]


def test_field_missing_from_best_is_marked_changed():
    rows = compute_config_diff({"new_field": "x"}, {})
    assert rows == [("new_field", "x", "changed")]


def test_preserves_current_field_order():
    current = {"b": 1, "a": 2}
    rows = compute_config_diff(current, {"b": 1, "a": 2})
    assert [r[0] for r in rows] == ["b", "a"]
