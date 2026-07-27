"""
OpenAI catalog-validation client.

The hand-rolled chat-completions call machinery (`call`/`_call_once`/
`_build_payload`/`compute_cost`) has been replaced by
src.core.langchain_llm_client.LangChainLLMClient (langchain-openai's
ChatOpenAI) via src.core.provider_factory.build_provider. This module now
only keeps `fetch_available_models`/`validate_models` — the live-catalog
check scripts/run_overnight.py's `--dry-run` path uses to confirm the
OpenAI models this project is configured for still exist, since that has
no LangChain equivalent.
"""

from __future__ import annotations

import os

import httpx

from src.utils.logger import get_logger

log = get_logger("openai_client")

OPENAI_BASE_URL = "https://api.openai.com/v1"


class OpenAIError(Exception):
    pass


class OpenAIClient:
    """Thin client used only to validate configured OpenAI models against
    OpenAI's live catalog (GET /v1/models) — see
    scripts/run_overnight.py's `_validate_environment`."""

    def __init__(self, api_key: str | None = None, base_url: str = OPENAI_BASE_URL):
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self._base_url = base_url

    def build_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    async def fetch_available_models(self) -> set[str]:
        """Live model IDs from OpenAI's catalog (GET /v1/models). Used to
        validate configured models still exist — OpenAI's API has no pricing
        endpoint, so this checks availability only, not price."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self._base_url}/models", headers=self.build_headers())

        if response.status_code != 200:
            raise OpenAIError(
                f"Failed to list models: HTTP {response.status_code}: {response.text[:300]}"
            )

        data = response.json()
        return {item["id"] for item in data.get("data", [])}

    async def validate_models(self, required_model_ids: list[str]) -> list[str]:
        """Check only the models this project actually references (not
        OpenAI's full catalog) against the live model list. Returns the
        subset of `required_model_ids` that OpenAI no longer serves, logging
        a warning if any are missing."""
        available = await self.fetch_available_models()
        missing = [m for m in required_model_ids if m not in available]
        if missing:
            log.warning("openai_models_unavailable", missing=missing)
        return missing
