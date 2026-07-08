"""Tests for extracting model reasoning text from OpenRouter response payloads."""

from src.utils.openrouter import _extract_reasoning_text


def test_extract_reasoning_text_from_reasoning_field():
    """A plain "reasoning" string field is returned as-is."""
    assert _extract_reasoning_text({"reasoning": "because retrieval improved"}) == (
        "because retrieval improved"
    )


def test_extract_reasoning_text_from_reasoning_details():
    """Multiple reasoning_details entries (mixed "text"/"content" keys) are joined with newlines."""
    message = {
        "reasoning_details": [
            {"type": "reasoning", "text": "first"},
            {"type": "reasoning", "content": "second"},
        ]
    }

    assert _extract_reasoning_text(message) == "first\nsecond"
