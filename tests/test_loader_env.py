"""Boundary validation for load_env().

An empty/blank OPENROUTER_API_KEY previously passed through silently and
surfaced far downstream as `Illegal header value b'Bearer '` and a vague
`APIConnectionError` from the ragas judge (every judge call swallowed to a
NaN -> 0.0 score). load_env() must reject a missing OR blank key loudly at
the system boundary with an actionable message.
"""

import pytest
from config.loader import load_env


def test_load_env_returns_key_when_present(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-valid")
    assert load_env()["OPENROUTER_API_KEY"] == "sk-or-valid"


def test_load_env_rejects_missing_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        load_env()


def test_load_env_rejects_empty_key(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        load_env()


def test_load_env_rejects_blank_key(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "   ")
    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        load_env()
