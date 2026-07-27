from src.utils.openrouter import _extract_reasoning_text, build_openrouter_headers


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
