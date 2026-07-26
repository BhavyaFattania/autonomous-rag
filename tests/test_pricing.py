from src.core.pricing import compute_cost


def test_openrouter_cost_uses_model_pricing_table():
    # deepseek/deepseek-v4-pro = (0.435, 0.870) USD per million
    cost = compute_cost("openrouter", "deepseek/deepseek-v4-pro", 1_000_000, 1_000_000)
    assert round(cost, 4) == round(0.435 + 0.870, 4)


def test_unknown_model_is_zero_cost(caplog):
    cost = compute_cost("openrouter", "made-up/model", 1000, 1000)
    assert cost == 0.0
