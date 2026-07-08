"""Tests for the global cost tracker: accumulation, hard ceiling, and warning threshold."""

import pytest
from src.storage.cost_tracker import BudgetExceededError, add_cost, get_total, initialize


@pytest.fixture(autouse=True)
def setup_tracker():
    """Reset the module-level tracker state before and after every test."""
    initialize(hard_ceiling=10.0, warning_threshold=7.0)
    yield
    initialize(hard_ceiling=10.0, warning_threshold=7.0)


def test_add_cost_accumulates():
    assert get_total() == 0.0
    add_cost(1.0)
    add_cost(1.0)
    add_cost(1.0)
    assert get_total() == 3.0


def test_hard_ceiling_raises():
    """Exceeding hard_ceiling raises instead of silently continuing to spend."""
    add_cost(9.5)
    with pytest.raises(BudgetExceededError):
        add_cost(1.0)


def test_warning_at_threshold(caplog):
    """Crossing warning_threshold (but not the ceiling) logs a "budget_warning", not an exception."""
    # structlog combined with standard logging
    import logging

    with caplog.at_level(logging.WARNING):
        add_cost(7.5)

    assert get_total() == 7.5
    # Since we use structlog to standard logging, it might appear in caplog
    assert any("budget_warning" in rec.message for rec in caplog.records)


def test_initialize_with_start_cost():
    """initialize() can seed a non-zero starting spend (e.g. resuming a run)."""
    initialize(hard_ceiling=10.0, warning_threshold=7.0, start_cost=5.0)
    assert get_total() == 5.0
    add_cost(1.0)
    assert get_total() == 6.0
