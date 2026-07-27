"""
OpenRouter helpers.

The hand-rolled OpenRouterClient HTTP call machinery has been replaced by
src.core.langchain_llm_client.LangChainLLMClient (langchain-openai's
ChatOpenAI). This module now only keeps what's still reused: the pricing
table (src.core.pricing), the base URL and header builder
(src.core.provider_factory), and the reasoning-text parser
(src.core.langchain_llm_client).
"""

from __future__ import annotations

import os

import httpx

from src.utils.logger import get_logger

log = get_logger("openrouter")

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Static fallback prices (USD per million tokens). Only used when the live
# Models API is unreachable, so a network blip can never silently zero out cost
# tracking (and the hard budget ceiling that reads it). Live pricing from
# fetch_openrouter_pricing() is authoritative and always current.
MODEL_PRICING = {
    "deepseek/deepseek-v4-pro": (0.435, 0.870),
    "deepseek/deepseek-v4-flash": (0.140, 0.280),
    "deepseek/deepseek-v4-flash:free": (0.000, 0.000),
    "qwen/qwen3-30b-a3b": (0.100, 0.300),
    "qwen/qwen3.5-flash-02-23": (0.065, 0.260),
    "openai/gpt-oss-20b": (0.050, 0.200),
}


def fetch_openrouter_pricing(timeout: float = 10.0) -> dict[str, tuple[float, float]] | None:
    """Fetch live (prompt, completion) USD-per-million pricing for every OpenRouter
    model from the public Models API (no API key required).

    Returns a ``{model_id: (prompt_per_M, completion_per_M)}`` map, or ``None`` on
    any failure so callers fall back to the static ``MODEL_PRICING`` table. The
    API reports per-token prices, converted here to the per-million convention the
    cost path uses. Conditional ``pricing.overrides`` (long-context / time-window
    tiers) are intentionally ignored — only the base rate is read.
    """
    try:
        resp = httpx.get(f"{OPENROUTER_BASE_URL}/models", timeout=timeout)
        resp.raise_for_status()
        data = resp.json().get("data", [])
    except Exception as exc:  # network error, non-200, malformed JSON
        log.warning("openrouter_pricing_fetch_failed", error=str(exc))
        return None

    pricing: dict[str, tuple[float, float]] = {}
    for model in data:
        model_id = model.get("id")
        rates = model.get("pricing") or {}
        try:
            prompt = float(rates.get("prompt", 0.0)) * 1_000_000
            completion = float(rates.get("completion", 0.0)) * 1_000_000
        except (TypeError, ValueError):
            continue
        if model_id:
            pricing[model_id] = (prompt, completion)
    return pricing or None


def build_openrouter_headers(api_key: str | None = None) -> dict:
    key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/autonomous-rag-optimizer",
        "X-Title": "RAG Optimizer",
    }


def _extract_reasoning_text(message: dict) -> str:
    reasoning = message.get("reasoning")
    if isinstance(reasoning, str):
        return reasoning.strip()
    details = message.get("reasoning_details")
    if not isinstance(details, list):
        return ""
    parts = []
    for item in details:
        if not isinstance(item, dict):
            continue
        for key in ("text", "content", "reasoning"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                parts.append(value.strip())
                break
    return "\n".join(parts)
