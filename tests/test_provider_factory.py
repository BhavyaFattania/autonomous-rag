"""Tests for provider selection via src.core.provider_factory.build_provider."""

import pytest
from config.models import ModelConfig
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
    from src.core.langchain_llm_client import LangChainLLMClient

    class Settings:
        class run:
            cost_hard_ceiling_usd = 10.0
            cost_warning_threshold_usd = 7.0
            llm_provider = "openai"

    provider = build_provider(Settings, env={"OPENAI_API_KEY": "sk-test"})

    assert isinstance(provider.llm_client, LangChainLLMClient)
    assert isinstance(provider.llm_client, ILLMClient)
    assert isinstance(provider.cost_tracker, ICostTracker)


def test_build_provider_uses_langchain_llm_client():
    from src.core.langchain_llm_client import LangChainLLMClient

    provider = build_provider(_Settings, env={"OPENROUTER_API_KEY": "sk-test"})
    assert isinstance(provider.llm_client, LangChainLLMClient)
    assert provider.llm_client._cost_tracker is provider.cost_tracker  # type: ignore[attr-defined]


def test_build_provider_openrouter_client_shares_provider_cost_tracker():
    """The bug the audit flagged: without this, the client could silently
    report cost to a different tracker than the one Provider.cost_tracker
    exposes (e.g. a stray module-level singleton), decoupling the ceiling
    check from what real calls actually report."""
    provider = build_provider(_Settings, env={"OPENROUTER_API_KEY": "sk-test"})

    assert provider.llm_client._cost_tracker is provider.cost_tracker  # type: ignore[attr-defined]


def test_build_provider_exposes_configured_model_roles():
    class Routing:
        scientist = ModelConfig(model_id="openrouter/scientist", task="scientist")

    provider = build_provider(
        _Settings,
        env={"OPENROUTER_API_KEY": "sk-test"},
        model_routing=Routing(),
    )

    assert provider.get_model_config("scientist").model_id == "openrouter/scientist"


def test_openrouter_headers_do_not_leak_os_environ_key(monkeypatch):
    """The bug the audit flagged: build_openrouter_headers("") falls back to
    the module-level _default_client singleton, whose key is read from the
    real os.environ — leaking a real key into default_headers even when the
    injected env has none, and desyncing it from the client's own api_key
    (which correctly stays ""). ChatOpenAI merges default_headers OVER its
    own api_key-derived Authorization, so a leaked Authorization header here
    would actually be used on the wire."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "REAL-OS-ENV-KEY")

    # injected env deliberately has NO key
    provider = build_provider(_Settings, env={})
    client = provider.llm_client

    assert client._api_key == ""  # type: ignore[attr-defined]
    assert "Authorization" not in client._default_headers  # type: ignore[attr-defined]
    assert client._default_headers.get("X-Title")  # type: ignore[attr-defined]  # branding header still present


def test_build_provider_openai_client_shares_provider_cost_tracker():
    class Settings:
        class run:
            cost_hard_ceiling_usd = 10.0
            cost_warning_threshold_usd = 7.0
            llm_provider = "openai"

    provider = build_provider(Settings, env={"OPENAI_API_KEY": "sk-test"})

    assert provider.llm_client._cost_tracker is provider.cost_tracker  # type: ignore[attr-defined]
