"""Tests for provider selection via src.core.provider_factory.build_provider."""

import pytest
from src.core.interfaces import ICostTracker, ILLMClient
from src.core.provider_factory import build_provider


class _Settings:
    class run:
        cost_hard_ceiling_usd = 10.0
        cost_warning_threshold_usd = 7.0
        llm_provider = "openrouter"


def test_build_provider_wires_openrouter_by_default():
    provider = build_provider(_Settings, env={"OPENROUTER_API_KEY": "sk-test"})

    assert isinstance(provider.llm_client, ILLMClient)
    assert isinstance(provider.cost_tracker, ICostTracker)
    assert provider.env == {"OPENROUTER_API_KEY": "sk-test"}
    assert provider.settings is _Settings


def test_build_provider_rejects_unknown_provider_name():
    class Settings:
        class run:
            cost_hard_ceiling_usd = 10.0
            cost_warning_threshold_usd = 7.0
            llm_provider = "does-not-exist"

    with pytest.raises(ValueError, match="does-not-exist"):
        build_provider(Settings, env={})


def test_build_provider_error_lists_supported_providers():
    class Settings:
        class run:
            cost_hard_ceiling_usd = 10.0
            cost_warning_threshold_usd = 7.0
            llm_provider = "bogus"

    with pytest.raises(ValueError, match="openrouter"):
        build_provider(Settings, env={})


def test_build_provider_tolerates_missing_env():
    provider = build_provider(_Settings, env=None)

    assert isinstance(provider.llm_client, ILLMClient)
    assert provider.env is None


def test_build_provider_wires_openai():
    from src.utils.openai_client import OpenAIClient

    class Settings:
        class run:
            cost_hard_ceiling_usd = 10.0
            cost_warning_threshold_usd = 7.0
            llm_provider = "openai"

    provider = build_provider(Settings, env={"OPENAI_API_KEY": "sk-test"})

    assert isinstance(provider.llm_client, OpenAIClient)
    assert isinstance(provider.llm_client, ILLMClient)
    assert isinstance(provider.cost_tracker, ICostTracker)


def test_build_provider_openrouter_client_shares_provider_cost_tracker():
    """The bug the audit flagged: without this, the client could silently
    report cost to a different tracker than the one Provider.cost_tracker
    exposes (e.g. a stray module-level singleton), decoupling the ceiling
    check from what real calls actually report."""
    provider = build_provider(_Settings, env={"OPENROUTER_API_KEY": "sk-test"})

    assert provider.llm_client._cost_tracker is provider.cost_tracker  # type: ignore[attr-defined]


def test_build_provider_openai_client_shares_provider_cost_tracker():
    class Settings:
        class run:
            cost_hard_ceiling_usd = 10.0
            cost_warning_threshold_usd = 7.0
            llm_provider = "openai"

    provider = build_provider(Settings, env={"OPENAI_API_KEY": "sk-test"})

    assert provider.llm_client._cost_tracker is provider.cost_tracker  # type: ignore[attr-defined]
