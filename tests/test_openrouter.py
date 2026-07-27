from src.utils.openrouter import (
    _extract_reasoning_text,
    build_openrouter_headers,
    fetch_openrouter_pricing,
)


class _FakeResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def raise_for_status(self):
        if self.status_code != 200:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


def test_fetch_openrouter_pricing_converts_per_token_to_per_million(monkeypatch):
    payload = {
        "data": [
            {
                "id": "deepseek/deepseek-v4-pro",
                "pricing": {"prompt": "0.000000435", "completion": "0.00000087"},
            },
            {"id": "some/free-model", "pricing": {"prompt": "0", "completion": "0"}},
        ]
    }
    monkeypatch.setattr("src.utils.openrouter.httpx.get", lambda *a, **k: _FakeResponse(payload))

    pricing = fetch_openrouter_pricing()

    assert pricing is not None
    assert round(pricing["deepseek/deepseek-v4-pro"][0], 4) == 0.435
    assert round(pricing["deepseek/deepseek-v4-pro"][1], 4) == 0.870
    assert pricing["some/free-model"] == (0.0, 0.0)


def test_fetch_openrouter_pricing_returns_none_on_failure(monkeypatch):
    def _boom(*a, **k):
        raise RuntimeError("network down")

    monkeypatch.setattr("src.utils.openrouter.httpx.get", _boom)

    assert fetch_openrouter_pricing() is None


def test_extract_reasoning_text_from_reasoning_field():
    assert _extract_reasoning_text({"reasoning": "because retrieval improved"}) == (
        "because retrieval improved"
    )


def test_extract_reasoning_text_from_reasoning_details():
    message = {
        "reasoning_details": [
            {"type": "reasoning", "text": "first"},
            {"type": "reasoning", "content": "second"},
        ]
    }

    assert _extract_reasoning_text(message) == "first\nsecond"


def test_build_openrouter_headers_uses_passed_api_key():
    headers = build_openrouter_headers("real-key")

    assert headers["Authorization"] == "Bearer real-key"


def test_build_openrouter_headers_falls_back_to_env_when_no_key(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "env-key")

    assert build_openrouter_headers()["Authorization"] == "Bearer env-key"
