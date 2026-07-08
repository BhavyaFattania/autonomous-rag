from src.utils.openrouter import _extract_reasoning_text


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
