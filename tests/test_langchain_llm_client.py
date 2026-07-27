import pytest
from langchain_core.messages import AIMessage
from src.core.langchain_llm_client import LangChainLLMClient, LLMClientError


class _FakeChat:
    def __init__(self, message):
        self._message = message
        self.seen = []

    async def ainvoke(self, messages, **kwargs):
        self.seen.append(messages)
        return self._message


@pytest.fixture
def client(monkeypatch):
    c = LangChainLLMClient(
        provider="openrouter",
        api_key="k",
        base_url="https://openrouter.ai/api/v1",
        default_headers={},
        cost_tracker=None,
    )
    return c


@pytest.mark.asyncio
async def test_call_returns_plain_string_content(client, monkeypatch):
    fake = _FakeChat(AIMessage(content="the answer"))
    monkeypatch.setattr("src.core.langchain_llm_client.build_chat_model", lambda **kw: fake)
    out = await client.call(
        model_id="m", messages=[{"role": "user", "content": "q"}], max_tokens=64, task="t"
    )
    assert out == "the answer"


@pytest.mark.asyncio
async def test_call_return_reasoning_yields_dict(client, monkeypatch):
    msg = AIMessage(content="ans", additional_kwargs={"reasoning": "because"})
    monkeypatch.setattr(
        "src.core.langchain_llm_client.build_chat_model", lambda **kw: _FakeChat(msg)
    )
    out = await client.call(
        model_id="m",
        messages=[{"role": "user", "content": "q"}],
        max_tokens=64,
        task="t",
        return_reasoning=True,
    )
    assert out == {"content": "ans", "reasoning": "because"}


@pytest.mark.asyncio
async def test_empty_content_raises(client, monkeypatch):
    monkeypatch.setattr(
        "src.core.langchain_llm_client.build_chat_model",
        lambda **kw: _FakeChat(AIMessage(content="")),
    )
    with pytest.raises(LLMClientError):
        await client.call(
            model_id="m", messages=[{"role": "user", "content": "q"}], max_tokens=64, task="t"
        )


@pytest.mark.asyncio
async def test_rate_limit_triggers_single_fallback(monkeypatch):
    class RateLimitError(Exception):
        pass

    calls = {"models": []}

    class _FailThenOK:
        def __init__(self, fail):
            self.fail = fail

        async def ainvoke(self, messages, **kw):
            if self.fail:
                raise RateLimitError("429 rate limited")
            return AIMessage(content="fallback answer")

    def fake_build(**kw):
        calls["models"].append(kw["model_id"])
        return _FailThenOK(fail=len(calls["models"]) == 1)

    monkeypatch.setattr("src.core.langchain_llm_client.build_chat_model", fake_build)
    client = LangChainLLMClient(
        provider="openrouter",
        api_key="k",
        base_url="https://openrouter.ai/api/v1",
        default_headers={},
        cost_tracker=None,
    )
    out = await client.call(
        model_id="primary",
        messages=[{"role": "user", "content": "q"}],
        max_tokens=64,
        task="t",
        fallback_model_id="backup",
    )
    assert out == "fallback answer"
    assert calls["models"] == ["primary", "backup"]


@pytest.mark.asyncio
async def test_cost_tracker_attaches_cost_callback(monkeypatch):
    from src.core.cost_callback import CostTrackingCallback

    captured = {}

    class _FakeChat:
        async def ainvoke(self, messages, **kw):
            return AIMessage(content="ok")

    def fake_build(**kw):
        captured["callbacks"] = kw["callbacks"]
        return _FakeChat()

    monkeypatch.setattr("src.core.langchain_llm_client.build_chat_model", fake_build)

    class _Tracker:
        def add_cost(self, usd):
            return usd

    client = LangChainLLMClient(
        provider="openrouter",
        api_key="k",
        base_url="https://openrouter.ai/api/v1",
        default_headers={},
        cost_tracker=_Tracker(),
    )
    await client.call(
        model_id="m",
        messages=[{"role": "user", "content": "q"}],
        max_tokens=64,
        task="t",
    )
    assert any(isinstance(cb, CostTrackingCallback) for cb in captured["callbacks"])
