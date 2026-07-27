import pytest
from src.utils.openai_client import OpenAIClient


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload
        self.text = str(payload)

    def json(self):
        return self._payload


class _FakeAsyncClient:
    """Stands in for httpx.AsyncClient — no mocking library is installed in
    this project, so this fakes just the `async with ... as client: await
    client.get(...)` shape fetch_available_models relies on."""

    def __init__(self, response: _FakeResponse, *args, **kwargs):
        self._response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False

    async def get(self, *_args, **_kwargs):
        return self._response


@pytest.mark.asyncio
async def test_fetch_available_models_returns_ids_from_catalog(monkeypatch):
    import src.utils.openai_client as openai_client_module

    fake_response = _FakeResponse(
        200, {"data": [{"id": "gpt-4o-mini"}, {"id": "gpt-4o"}, {"id": "o3-mini"}]}
    )
    monkeypatch.setattr(
        openai_client_module.httpx,
        "AsyncClient",
        lambda *a, **kw: _FakeAsyncClient(fake_response),
    )

    client = OpenAIClient(api_key="sk-test")
    models = await client.fetch_available_models()

    assert models == {"gpt-4o-mini", "gpt-4o", "o3-mini"}


@pytest.mark.asyncio
async def test_validate_models_reports_only_missing_ones(monkeypatch, caplog):
    import src.utils.openai_client as openai_client_module

    fake_response = _FakeResponse(200, {"data": [{"id": "gpt-4o-mini"}]})
    monkeypatch.setattr(
        openai_client_module.httpx,
        "AsyncClient",
        lambda *a, **kw: _FakeAsyncClient(fake_response),
    )

    client = OpenAIClient(api_key="sk-test")
    with caplog.at_level("WARNING"):
        missing = await client.validate_models(["gpt-4o-mini", "gpt-4o-retired"])

    assert missing == ["gpt-4o-retired"]
    assert "openai_models_unavailable" in caplog.text


@pytest.mark.asyncio
async def test_validate_models_empty_when_all_present(monkeypatch):
    import src.utils.openai_client as openai_client_module

    fake_response = _FakeResponse(200, {"data": [{"id": "gpt-4o-mini"}, {"id": "gpt-4o"}]})
    monkeypatch.setattr(
        openai_client_module.httpx,
        "AsyncClient",
        lambda *a, **kw: _FakeAsyncClient(fake_response),
    )

    client = OpenAIClient(api_key="sk-test")
    missing = await client.validate_models(["gpt-4o-mini"])

    assert missing == []


@pytest.mark.asyncio
async def test_fetch_available_models_raises_on_http_error(monkeypatch):
    import src.utils.openai_client as openai_client_module

    fake_response = _FakeResponse(401, {"error": "unauthorized"})
    monkeypatch.setattr(
        openai_client_module.httpx,
        "AsyncClient",
        lambda *a, **kw: _FakeAsyncClient(fake_response),
    )

    client = OpenAIClient(api_key="sk-bad")
    with pytest.raises(Exception, match="Failed to list models"):
        await client.fetch_available_models()
