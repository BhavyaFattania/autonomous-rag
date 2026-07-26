from src.core.langchain_llm_client import build_chat_model


def _payload(**kw):
    chat = build_chat_model(
        provider=kw.pop("provider", "openrouter"),
        model_id=kw.pop("model_id", "deepseek/deepseek-v4-pro"),
        api_key="k",
        base_url="https://openrouter.ai/api/v1",
        default_headers={},
        max_tokens=256,
        reasoning_effort=kw.pop("reasoning_effort", None),
        temperature=kw.pop("temperature", 0.1),
        response_format=kw.pop("response_format", None),
        callbacks=[],
    )
    return chat._get_request_payload([{"role": "user", "content": "hi"}])


def test_openrouter_reasoning_effort_goes_to_extra_body_and_omits_temperature():
    p = _payload(reasoning_effort="high", temperature=0.1)
    assert p["extra_body"]["reasoning"] == {"effort": "high"}
    assert "temperature" not in p  # reasoning => no temperature (current behavior)


def test_plain_call_sends_temperature_no_reasoning():
    p = _payload(reasoning_effort=None, temperature=0.1)
    assert p.get("temperature") == 0.1
    assert "reasoning" not in p.get("extra_body", {})


def test_json_object_sets_response_format():
    p = _payload(response_format="json_object")
    assert p["response_format"] == {"type": "json_object"}


def test_openai_o_series_uses_top_level_reasoning_effort():
    p = _payload(provider="openai", model_id="o3-mini", reasoning_effort="high", temperature=0.1)
    assert p.get("reasoning_effort") == "high"
    assert "temperature" not in p
