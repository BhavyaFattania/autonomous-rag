"""Resolves `settings.run.llm_provider` to a fully-wired Provider.

Single seam for provider selection: adding a new provider means writing one
`_build_*_provider(settings, env)` function and registering it in
`_PROVIDER_BUILDERS`, without touching call sites of `build_provider`.
"""

from __future__ import annotations

from typing import Any, Callable

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


_PROVIDER_BUILDERS: dict[str, Callable[[Any, dict | None], Provider]] = {
    "openrouter": _build_openrouter_provider,
}


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
        supported = ", ".join(sorted(_PROVIDER_BUILDERS))
        raise ValueError(
            f"Unknown llm_provider {provider_name!r}. Supported providers: {supported}."
        ) from None
    return builder(settings, env)
