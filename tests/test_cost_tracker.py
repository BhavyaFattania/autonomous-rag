import pytest
from src.storage.cost_tracker import initialize, add_cost, get_total, BudgetExceededError

@pytest.fixture(autouse=True)
def setup_tracker():
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
    add_cost(9.5)
    with pytest.raises(BudgetExceededError):
        add_cost(1.0)

def test_warning_at_threshold(caplog):
    # structlog combined with standard logging
    import logging
    with caplog.at_level(logging.WARNING):
        add_cost(7.5)

    assert get_total() == 7.5
    # Since we use structlog to standard logging, it might appear in caplog
    assert any("budget_warning" in rec.message for rec in caplog.records)
