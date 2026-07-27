"""Resolves `settings.run.llm_provider` to a fully-wired Provider.

Single seam for provider selection: adding a new provider means adding one
`ProviderSpec` entry to `_PROVIDER_SPECS`, without touching call sites of
`build_provider`. Every provider's `llm_client` is a `LangChainLLMClient`
(langchain-openai's `ChatOpenAI` under the hood); the spec only supplies the
per-provider base URL, headers, and required env var.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from src.core.langchain_llm_client import LangChainLLMClient
from src.core.provider import Provider
from src.storage.cost_tracker import CostTracker
from src.utils.openrouter import OPENROUTER_BASE_URL, build_openrouter_headers


class ModelRoutingProvider:
    """Adapter exposing YAML role routing through the Provider DI boundary."""

    def __init__(self, model_routing: Any):
        self._model_routing = model_routing

    def get_model_id(self, role: str) -> str:
        return self.get_config(role).model_id

    def get_config(self, role: str) -> Any:
        try:
            config = getattr(self._model_routing, role)
        except AttributeError as exc:
            raise ValueError(f"Unknown model role {role!r}.") from exc
        if config is None:
            raise ValueError(f"Model role {role!r} is not configured.")
        return config


def _provider_kwargs(model_routing: Any | None) -> dict[str, Any]:
    return {
        "model_routing_provider": ModelRoutingProvider(model_routing) if model_routing else None,
    }


@dataclass(frozen=True)
class ProviderSpec:
    """Everything `build_provider` needs to wire one provider's
    `LangChainLLMClient` — the base URL `ChatOpenAI` talks to, a header
    builder (OpenRouter needs `HTTP-Referer`/`X-Title`; OpenAI needs none
    beyond what `ChatOpenAI`'s own `api_key` already sets), and the env var
    the API key is read from.
    """

    base_url: str
    headers: Callable[[str], dict]
    env_var: str


def _openrouter_default_headers(api_key: str) -> dict:
    """OpenRouter branding headers only. ChatOpenAI derives Authorization from
    the resolved api_key, so we must NOT include an Authorization header here:
    build_openrouter_headers() falls back to the module-level singleton (which
    reads os.environ) when api_key is empty, which would leak a real key past
    the injected-env boundary and desync it from the client's own api_key.
    """
    headers = build_openrouter_headers(api_key)
    headers.pop("Authorization", None)
    return headers


# Single seam for provider selection: adding a new provider means adding one
# entry here, without touching call sites of `build_provider` or
# `required_env_var`.
_PROVIDER_SPECS: dict[str, ProviderSpec] = {
    "openrouter": ProviderSpec(
        base_url=OPENROUTER_BASE_URL,
        headers=_openrouter_default_headers,
        env_var="OPENROUTER_API_KEY",
    ),
    "openai": ProviderSpec(
        base_url="https://api.openai.com/v1",
        headers=lambda _api_key: {},
        env_var="OPENAI_API_KEY",
    ),
}


def _unknown_provider_error(provider_name: str) -> ValueError:
    supported = ", ".join(sorted(_PROVIDER_SPECS))
    return ValueError(f"Unknown llm_provider {provider_name!r}. Supported providers: {supported}.")


def _resolve_pricing_map(provider_name: str) -> dict[str, tuple[float, float]] | None:
    """Resolve the pricing map to inject into cost tracking, fetched once here at
    startup (never in the per-call hot path).

    For OpenRouter, fetch live rates from the Models API and layer them over the
    static table (static covers any id the live list omits, e.g. `:free` aliases).
    Returns None on fetch failure — the cost path then falls back to the static
    per-provider registry, so a network blip never breaks the budget ceiling.
    Non-OpenRouter providers return None (their static registry is authoritative).
    """
    if provider_name != "openrouter":
        return None
    from src.utils.openrouter import MODEL_PRICING, fetch_openrouter_pricing

    live = fetch_openrouter_pricing()
    if live is None:
        return None
    return {**MODEL_PRICING, **live}


def build_provider(
    settings: Any, env: dict | None = None, model_routing: Any | None = None
) -> Provider:
    """Construct the `Provider` for `settings.run.llm_provider`.

    Raises `ValueError` for an unregistered provider name, listing the
    providers that are actually available, rather than letting an unknown
    name silently fall through to whatever the default happened to be.
    """
    provider_name = settings.run.llm_provider
    try:
        spec = _PROVIDER_SPECS[provider_name]
    except KeyError:
        raise _unknown_provider_error(provider_name) from None

    api_key = (env.get(spec.env_var) if env else None) or ""
    # Built once and handed to both Provider and the client, so the tracker
    # that enforces the cost ceiling and the tracker that real calls report
    # to are provably the same object — not two trackers that happen to
    # agree only because of a module-level singleton elsewhere.
    cost_tracker = CostTracker(
        hard_ceiling=settings.run.cost_hard_ceiling_usd,
        warning_threshold=settings.run.cost_warning_threshold_usd,
    )
    pricing = _resolve_pricing_map(provider_name)
    llm_client = LangChainLLMClient(
        provider=provider_name,
        api_key=api_key,
        base_url=spec.base_url,
        default_headers=spec.headers(api_key),
        cost_tracker=cost_tracker,
        pricing=pricing,
    )
    return Provider(
        cost_tracker=cost_tracker,
        llm_client=llm_client,
        env=env,
        settings=settings,
        pricing=pricing,
        **_provider_kwargs(model_routing),
    )


def required_env_var(provider_name: str) -> str:
    """Return the environment variable name `provider_name`'s client reads.

    Raises `ValueError` for an unregistered provider name, same as
    `build_provider`.
    """
    try:
        return _PROVIDER_SPECS[provider_name].env_var
    except KeyError:
        raise _unknown_provider_error(provider_name) from None
