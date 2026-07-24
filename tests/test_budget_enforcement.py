"""Regression tests for the cost-tracker split-brain bug: budget_guard_node
(and every other node that reports/reads cost) must read the same
provider.cost_tracker instance real LLM calls report to, not the deprecated
src.storage.cost_tracker module-level singleton that nothing updates. Also
covers the BUDGET_EXCEEDED routing/propagation path end to end so a real
BudgetExceededError halts the run instead of being absorbed into a generic
fallback/failure that lets the loop keep spending."""

from unittest.mock import MagicMock

import pytest
from src.core.provider import Provider
from src.orchestrator.budget_guard import budget_guard_node
from src.orchestrator.graph import _after_evaluator, _after_indexer, _after_validator
from src.orchestrator.validator import validator_node
from src.storage.cost_tracker import BudgetExceededError, CostTracker
from src.storage.cost_tracker import add_cost as singleton_add_cost
from src.storage.cost_tracker import initialize as singleton_initialize


class _Settings:
    class run:
        cost_hard_ceiling_usd = 10.0


@pytest.fixture(autouse=True)
def _reset_singleton_tracker():
    """The deprecated module singleton is intentionally left untouched by
    the fix (still used as _report_cost()'s fallback in openrouter.py/
    openai_client.py when no tracker is injected) -- reset it around each
    test so a stray value can't accidentally make a real-tracker assertion
    pass for the wrong reason."""
    singleton_initialize(hard_ceiling=10.0, warning_threshold=7.0)
    yield
    singleton_initialize(hard_ceiling=10.0, warning_threshold=7.0)


def test_budget_guard_reads_providers_tracker_not_the_singleton():
    """budget_guard_node must halt based on the tracker real API calls
    report to (provider.cost_tracker), never the module singleton -- even
    when the singleton disagrees."""
    singleton_add_cost(0.0)  # singleton stays at 0.0, unlike provider's tracker below

    real_tracker = CostTracker(hard_ceiling=10.0, warning_threshold=7.0)
    real_tracker.add_cost(9.99)  # under ceiling, but real spend the singleton doesn't see
    provider = Provider(cost_tracker=real_tracker)

    result = budget_guard_node({}, _Settings, provider)
    assert result["status"] == "RUNNING"

    real_tracker.initialize(hard_ceiling=10.0, warning_threshold=7.0, start_cost=0.0)
    with pytest.raises(BudgetExceededError):
        real_tracker.add_cost(10.5)  # crosses the ceiling on the real tracker

    result = budget_guard_node({}, _Settings, provider)
    assert result["status"] == "BUDGET_EXCEEDED"


def test_after_validator_routes_budget_exceeded_to_recorder():
    assert _after_validator({"status": "BUDGET_EXCEEDED"}) == "recorder"


def test_after_indexer_routes_budget_exceeded_to_recorder():
    assert _after_indexer({"status": "BUDGET_EXCEEDED"}) == "recorder"


def test_after_evaluator_routes_budget_exceeded_to_recorder():
    assert _after_evaluator({"status": "BUDGET_EXCEEDED"}) == "recorder"


def test_validator_node_passes_through_budget_exceeded_without_revalidating():
    """scientist_node's BUDGET_EXCEEDED tick still carries the PREVIOUS
    tick's proposed_config (LangGraph state merge, not an empty dict) since
    the scientist node didn't return one. validator_node must not
    re-validate that stale config and silently overwrite the halt with
    RUNNING/FAILED_VALIDATION."""
    state = {
        "status": "BUDGET_EXCEEDED",
        "failure_reason": "Cost $10.50 exceeds ceiling $10.00. Stopping.",
        "proposed_config": {"node_parser": "sentence"},  # stale, intentionally incomplete
    }

    result = validator_node(state, settings=MagicMock())

    assert result["status"] == "BUDGET_EXCEEDED"
    assert result["failure_reason"] == state["failure_reason"]


@pytest.mark.asyncio
async def test_scientist_node_reports_budget_exceeded_not_a_fallback_proposal():
    """A BudgetExceededError from the real LLM call must produce
    status=BUDGET_EXCEEDED, not be swallowed into fallback_proposal() like a
    generic API failure -- a fallback would let the autonomous loop keep
    running (and spending) past the hard ceiling."""
    from src.scientist.brain import scientist_node

    class _BudgetExceededLLMClient:
        async def call(self, **kwargs):
            raise BudgetExceededError("Cost $10.50 exceeds ceiling $10.00. Stopping.")

    provider = Provider(
        cost_tracker=CostTracker(hard_ceiling=10.0, warning_threshold=7.0),
        llm_client=_BudgetExceededLLMClient(),
    )

    state = {
        "experiments_completed": 5,
        "history_summary": "",
        "baseline_config": {},
        "current_best_config": {},
        "current_best_weighted_score": 0.5,
        "successful_patterns": [],
        "failed_patterns": [],
    }

    mock_settings = MagicMock()
    mock_settings.explore_exploit.structured_exploration_experiments = 0
    mock_settings.explore_exploit.reranker_probe_every_n_experiments = 0
    mock_settings.explore_exploit.exploit_probability = 0.0

    result = await scientist_node(state, mock_settings, provider=provider)

    assert result["status"] == "BUDGET_EXCEEDED"
    assert "proposed_config" not in result  # unlike fallback_proposal()'s return shape
