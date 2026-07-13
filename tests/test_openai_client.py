import pytest
from src.core.interfaces import ILLMClient
from src.storage.cost_tracker import get_total, initialize
from src.utils.openai_client import (
    OpenAIClient,
    OpenAINonRetryableError,
    _build_payload,
)


def test_openai_client_satisfies_illm_client_protocol():
    assert isinstance(OpenAIClient(api_key="sk-test"), ILLMClient)


class _FakeCostTracker:
    def __init__(self):
        self.reported = []

    def initialize(self, hard_ceiling, warning_threshold, start_cost=0.0):
        pass

    def add_cost(self, usd: float) -> float:
        self.reported.append(usd)
        return sum(self.reported)

    def get_total(self) -> float:
        return sum(self.reported)


def test_report_cost_uses_injected_tracker_not_module_singleton():
    tracker = _FakeCostTracker()
    client = OpenAIClient(api_key="sk-test", cost_tracker=tracker)

    client._report_cost(1.23)

    assert tracker.reported == [1.23]


def test_report_cost_falls_back_to_module_singleton_when_no_tracker_injected():
    initialize(hard_ceiling=100.0, warning_threshold=90.0)
    client = OpenAIClient(api_key="sk-test")

    client._report_cost(2.5)

    assert get_total() == 2.5


def test_compute_cost_uses_injected_pricing():
    """Injected pricing (used by callers with their own source) takes
    priority over config/openai_pricing.yaml and is fully isolated from it."""
    client = OpenAIClient(api_key="sk-test", pricing={"fake-model": (1.0, 2.0)})

    cost = client.compute_cost("fake-model", prompt_tokens=1_000_000, completion_tokens=1_000_000)

    assert cost == pytest.approx(1.0 + 2.0)


def test_compute_cost_unknown_model_is_zero_and_warns(caplog):
    client = OpenAIClient(api_key="sk-test", pricing={"gpt-4o-mini": (0.15, 0.60)})

    with caplog.at_level("WARNING"):
        cost = client.compute_cost(
            "some-future-model", prompt_tokens=1_000_000, completion_tokens=500
        )

    assert cost == 0.0
    assert "openai_pricing_missing" in caplog.text


def test_compute_cost_defaults_to_config_openai_pricing_yaml():
    """Smoke test: the real config/openai_pricing.yaml, loaded lazily when no
    pricing dict is injected, prices a model this project actually uses."""
    client = OpenAIClient(api_key="sk-test")

    cost = client.compute_cost("gpt-4o-mini", prompt_tokens=1_000_000, completion_tokens=1_000_000)

    assert cost > 0.0


def test_build_payload_reasoning_model_uses_reasoning_effort_field():
    payload = _build_payload(
        model_id="o3-mini",
        messages=[{"role": "user", "content": "hi"}],
        max_tokens=100,
        reasoning_effort="high",
        temperature=0.1,
    )

    assert payload["reasoning_effort"] == "high"
    assert "temperature" not in payload


def test_build_payload_non_reasoning_model_uses_temperature():
    payload = _build_payload(
        model_id="gpt-4o-mini",
        messages=[{"role": "user", "content": "hi"}],
        max_tokens=100,
        reasoning_effort=None,
        temperature=0.3,
    )

    assert payload["temperature"] == 0.3
    assert "reasoning_effort" not in payload


def test_build_payload_reasoning_model_ignores_reasoning_effort_when_unset():
    """A reasoning model with no reasoning_effort hint gets neither field —
    OpenAI's o-series rejects an explicit temperature override."""
    payload = _build_payload(
        model_id="o3-mini",
        messages=[{"role": "user", "content": "hi"}],
        max_tokens=100,
        reasoning_effort=None,
        temperature=0.1,
    )

    assert "reasoning_effort" not in payload
    assert "temperature" not in payload


def test_build_payload_json_response_format():
    payload = _build_payload(
        model_id="gpt-4o-mini",
        messages=[{"role": "user", "content": "hi"}],
        max_tokens=100,
        reasoning_effort=None,
        temperature=0.1,
        response_format="json_object",
    )

    assert payload["response_format"] == {"type": "json_object"}


@pytest.mark.asyncio
async def test_call_without_api_key_raises_non_retryable_before_any_request(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = OpenAIClient(api_key="")

    with pytest.raises(OpenAINonRetryableError):
        await client.call(
            model_id="gpt-4o-mini",
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=10,
            task="test",
        )


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
