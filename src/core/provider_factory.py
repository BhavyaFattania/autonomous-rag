"""Resolves `settings.run.llm_provider` to a fully-wired Provider.

Single seam for provider selection: adding a new provider means writing one
`_build_*_provider(settings, env)` function and registering it in
`_PROVIDER_BUILDERS`, without touching call sites of `build_provider`.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.core.provider import Provider
from src.storage.cost_tracker import CostTracker


def _build_openrouter_provider(settings: Any, env: dict | None) -> Provider:
    from src.utils.openrouter import OpenRouterClient

    return Provider(
        cost_tracker=CostTracker(
            hard_ceiling=settings.run.cost_hard_ceiling_usd,
            warning_threshold=settings.run.cost_warning_threshold_usd,
        ),
        llm_client=OpenRouterClient(api_key=env.get("OPENROUTER_API_KEY") if env else None),
        env=env,
        settings=settings,
    )


def _build_openai_provider(settings: Any, env: dict | None) -> Provider:
    from src.utils.openai_client import OpenAIClient

    return Provider(
        cost_tracker=CostTracker(
            hard_ceiling=settings.run.cost_hard_ceiling_usd,
            warning_threshold=settings.run.cost_warning_threshold_usd,
        ),
        llm_client=OpenAIClient(api_key=env.get("OPENAI_API_KEY") if env else None),
        env=env,
        settings=settings,
    )


_PROVIDER_BUILDERS: dict[str, Callable[[Any, dict | None], Provider]] = {
    "openrouter": _build_openrouter_provider,
    "openai": _build_openai_provider,
}

# Which env var each provider's builder reads its API key from. Kept next to
# _PROVIDER_BUILDERS so the two registries can't drift — callers that need to
# validate "is this provider's key present" (e.g. run_overnight.py's
# --dry-run) go through required_env_var() instead of hardcoding a second
# provider-name list.
_PROVIDER_REQUIRED_ENV_VAR: dict[str, str] = {
    "openrouter": "OPENROUTER_API_KEY",
    "openai": "OPENAI_API_KEY",
}


def _unknown_provider_error(provider_name: str) -> ValueError:
    supported = ", ".join(sorted(_PROVIDER_BUILDERS))
    return ValueError(f"Unknown llm_provider {provider_name!r}. Supported providers: {supported}.")


def build_provider(settings: Any, env: dict | None = None) -> Provider:
    """Construct the `Provider` for `settings.run.llm_provider`.

    Raises `ValueError` for an unregistered provider name, listing the
    providers that are actually available, rather than letting an unknown
    name silently fall through to whatever the default happened to be.
    """
    provider_name = settings.run.llm_provider
    try:
        builder = _PROVIDER_BUILDERS[provider_name]
    except KeyError:
        raise _unknown_provider_error(provider_name) from None
    return builder(settings, env)


def required_env_var(provider_name: str) -> str:
    """Return the environment variable name `provider_name`'s builder reads.

    Raises `ValueError` for an unregistered provider name, same as
    `build_provider`.
    """
    if provider_name not in _PROVIDER_BUILDERS:
        raise _unknown_provider_error(provider_name)
    return _PROVIDER_REQUIRED_ENV_VAR[provider_name]
