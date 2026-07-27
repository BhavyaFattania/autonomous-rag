import logging

from src.core.pricing import compute_cost


def test_openrouter_cost_uses_model_pricing_table():
    # deepseek/deepseek-v4-pro = (0.435, 0.870) USD per million
    cost = compute_cost("openrouter", "deepseek/deepseek-v4-pro", 1_000_000, 1_000_000)
    assert round(cost, 4) == round(0.435 + 0.870, 4)


def test_unknown_model_is_zero_cost(caplog):
    with caplog.at_level(logging.WARNING):
        cost = compute_cost("openrouter", "made-up/model", 1000, 1000)
    assert cost == 0.0
    # Verify the warning was logged
    assert any(
        "pricing_missing" in record.getMessage() or "pricing_missing" in str(record.msg)
        for record in caplog.records
    ), "Expected warning with 'pricing_missing' was not logged"


def test_compute_cost_prefers_injected_pricing_over_registry():
    # injected map overrides the static registry for the same model
    injected = {"deepseek/deepseek-v4-pro": (1.0, 2.0)}
    cost = compute_cost(
        "openrouter", "deepseek/deepseek-v4-pro", 1_000_000, 1_000_000, pricing=injected
    )
    assert round(cost, 4) == round(1.0 + 2.0, 4)
