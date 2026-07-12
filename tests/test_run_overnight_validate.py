"""Tests for scripts/run_overnight.py's provider-aware --dry-run validation."""

import pytest
from scripts.run_overnight import _validate_environment


class _Settings:
    class run:
        llm_provider = "openrouter"


def _settings_for(provider_name: str):
    class Settings:
        class run:
            llm_provider = provider_name

    return Settings


@pytest.mark.asyncio
async def test_openrouter_missing_key_exits(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with pytest.raises(SystemExit):
        await _validate_environment(_settings_for("openrouter"))


@pytest.mark.asyncio
async def test_openrouter_present_key_passes(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")

    await _validate_environment(_settings_for("openrouter"))


@pytest.mark.asyncio
async def test_unknown_provider_exits():
    with pytest.raises(SystemExit):
        await _validate_environment(_settings_for("bogus-provider"))


@pytest.mark.asyncio
async def test_openai_missing_key_exits(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(SystemExit):
        await _validate_environment(_settings_for("openai"))


@pytest.mark.asyncio
async def test_openai_missing_models_exits(monkeypatch):
    from src.utils.openai_client import OpenAIClient

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(
        OpenAIClient, "validate_models", lambda self, required: _fake_missing(["gpt-4o-retired"])
    )

    with pytest.raises(SystemExit):
        await _validate_environment(_settings_for("openai"))


@pytest.mark.asyncio
async def test_openai_all_models_present_passes(monkeypatch):
    from src.utils.openai_client import OpenAIClient

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(OpenAIClient, "validate_models", lambda self, required: _fake_missing([]))

    await _validate_environment(_settings_for("openai"))


@pytest.mark.asyncio
async def test_openai_model_check_network_failure_exits(monkeypatch):
    from src.utils.openai_client import OpenAIClient

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    async def _raise(self, _required):
        raise ConnectionError("no route to host")

    monkeypatch.setattr(OpenAIClient, "validate_models", _raise)

    with pytest.raises(SystemExit):
        await _validate_environment(_settings_for("openai"))


async def _fake_missing(missing: list[str]) -> list[str]:
    return missing
