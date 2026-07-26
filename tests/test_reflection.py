# tests/test_reflection.py
"""Unit tests for src/scientist/reflection.py."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from config.settings import (
    EvalSettings,
    ExploreExploitSettings,
    ReflectionSettings,
    SearchSpaceSettings,
    Settings,
)
from src.core.provider import Provider
from src.scientist.reflection import _MAX_REFLECTION_TOKENS, reflection_node
from src.utils.context_budget import count_tokens

# ─── Setup & Fixtures ────────────────────────────────────────────────────────


def _make_settings(overrides: dict | None = None) -> Settings:
    """Build a Settings object for test use, mirroring test_brain.py style."""
    overrides = overrides or {}
    search_space_raw = overrides.pop("search_space", {})
    return Settings(
        evaluation=EvalSettings(**overrides.get("evaluation", {})),
        reflection=ReflectionSettings(
            **overrides.get("reflection", {"update_every_n_experiments": 5})
        ),
        explore_exploit=ExploreExploitSettings(**overrides.get("explore_exploit", {})),
        search_space=SearchSpaceSettings(**search_space_raw),
    )


BASE_STATE = {
    "current_best_config": {},
    "current_best_weighted_score": 0.0,
    "successful_patterns": [],
    "failed_patterns": [],
}


@pytest.fixture
def settings():
    """Create default test settings."""
    return _make_settings()


@pytest.fixture
def mock_provider():
    """Mock the Provider and its LLM client."""
    provider = MagicMock(spec=Provider)
    provider.llm_client = MagicMock()
    provider.llm_client.call = AsyncMock()
    return provider


# ─── Tests ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_reflection_node_zero_experiments(settings, mock_provider):
    """Returns {} when experiments_completed == 0."""
    state = {**BASE_STATE, "experiments_completed": 0}

    result = await reflection_node(state, settings, mock_provider)

    assert result == {}
    mock_provider.llm_client.call.assert_not_awaited()


@pytest.mark.asyncio
async def test_reflection_node_not_nth_experiment(settings, mock_provider):
    """Returns {} when experiments_completed % update_every_n != 0."""
    state = {**BASE_STATE, "experiments_completed": 3}

    result = await reflection_node(state, settings, mock_provider)

    assert result == {}
    mock_provider.llm_client.call.assert_not_awaited()


@pytest.mark.asyncio
async def test_reflection_node_success(settings, mock_provider):
    """Calls LLM and truncates the result to the configured token budget on success."""
    state = {**BASE_STATE, "experiments_completed": 5}

    # We pass a very long string to test the truncation boundary
    long_response = "word " * 5000
    mock_provider.llm_client.call.return_value = long_response

    result = await reflection_node(state, settings, mock_provider)

    assert "reflection_summary" in result
    summary = result["reflection_summary"]

    assert count_tokens(summary) <= _MAX_REFLECTION_TOKENS
    mock_provider.llm_client.call.assert_awaited_once()

    # Check that it actually passed the prompt in messages
    call_kwargs = mock_provider.llm_client.call.call_args.kwargs
    assert "messages" in call_kwargs
    assert len(call_kwargs["messages"]) == 1
    assert "content" in call_kwargs["messages"][0]
    assert isinstance(call_kwargs["messages"][0]["content"], str)


@pytest.mark.asyncio
async def test_reflection_node_llm_exception(settings, mock_provider):
    """Returns {} on LLM failure (exception handling)."""
    state = {**BASE_STATE, "experiments_completed": 5}
    mock_provider.llm_client.call.side_effect = Exception("LLM is down")

    result = await reflection_node(state, settings, mock_provider)

    assert result == {}
    mock_provider.llm_client.call.assert_awaited_once()


@pytest.mark.asyncio
async def test_reflection_node_non_string_response(settings, mock_provider):
    """Returns {} when LLM returns a non-string response."""
    state = {**BASE_STATE, "experiments_completed": 5}
    mock_provider.llm_client.call.return_value = {"error": "not a string"}

    result = await reflection_node(state, settings, mock_provider)

    assert result == {}
    mock_provider.llm_client.call.assert_awaited_once()
