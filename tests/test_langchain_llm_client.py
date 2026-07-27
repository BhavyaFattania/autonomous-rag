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
