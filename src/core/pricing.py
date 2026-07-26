"""Unified per-(provider, model) pricing lookup shared by the cost callback."""

from __future__ import annotations

from src.utils.logger import get_logger

log = get_logger("pricing")


def _pricing_for(provider: str) -> dict[str, tuple[float, float]]:
    if provider == "openrouter":
        from src.utils.openrouter import MODEL_PRICING

        return MODEL_PRICING
    if provider == "openai":
        from config.loader import load_openai_pricing

        return load_openai_pricing()
    return {}


def compute_cost(provider: str, model_id: str, prompt_tokens: int, completion_tokens: int) -> float:
    """USD cost for a call; 0.0 (with a warning) when the model has no price."""
    pricing = _pricing_for(provider)
    if model_id not in pricing:
        log.warning(
            "pricing_missing",
            provider=provider,
            model=model_id,
            hint="cost recorded as $0 until added to the pricing table",
        )
        return 0.0
    price_in, price_out = pricing[model_id]
    return (prompt_tokens / 1_000_000) * price_in + (completion_tokens / 1_000_000) * price_out
