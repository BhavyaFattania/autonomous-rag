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

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

MODEL_PRICING = {
    "deepseek/deepseek-v4-pro": (0.435, 0.870),
    "deepseek/deepseek-v4-flash": (0.140, 0.280),
    "deepseek/deepseek-v4-flash:free": (0.000, 0.000),
    "qwen/qwen3-30b-a3b": (0.100, 0.300),
    "qwen/qwen3.5-flash-02-23": (0.065, 0.260),
    "openai/gpt-oss-20b": (0.050, 0.200),
}


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
