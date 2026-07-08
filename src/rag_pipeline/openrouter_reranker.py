"""
Cohere reranking via OpenRouter API.

Wraps Cohere's rerank-v3.5 model with retry logic for rate limits and async support.
BaseNodePostprocessor interface integrates seamlessly with llama_index retrievers.
"""

import os

import httpx
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import NodeWithScore, QueryBundle
from pydantic import Field
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from src.utils.logger import get_logger
from src.utils.openrouter import build_openrouter_headers

log = get_logger("openrouter_reranker")


def is_openrouter_rate_limit_error(exception: Exception) -> bool:
    """Check if exception indicates a 429 rate limit from OpenRouter."""
    msg = str(exception).lower()
    return "429" in msg or "too_many_requests" in msg or "rate limit" in msg


class OpenRouterRerank(BaseNodePostprocessor):
    """
    Rerank nodes using Cohere's rerank model via OpenRouter.

    Configurable model (default: cohere/rerank-v3.5), top_n results, and API key.
    Supports both sync and async reranking with exponential backoff on rate limits.
    """

    model: str = Field(default="cohere/rerank-v3.5")
    top_n: int = Field(default=5)
    api_key: str | None = Field(default=None)

    @classmethod
    def class_name(cls) -> str:
        return "OpenRouterRerank"

    def _postprocess_nodes(
        self,
        nodes: list[NodeWithScore],
        query_bundle: QueryBundle | None = None,
    ) -> list[NodeWithScore]:
        """Synchronous reranking. Calls OpenRouter API with retry on rate limits."""
        if not nodes or query_bundle is None:
            return nodes

        api_key = self.api_key or os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is not set.")

        url = "https://openrouter.ai/api/v1/rerank"
        headers = build_openrouter_headers(api_key)
        payload = {
            "model": self.model,
            "query": query_bundle.query_str,
            "documents": [node.node.get_content() for node in nodes],
            "top_n": self.top_n,
        }

        @retry(
            retry=retry_if_exception(is_openrouter_rate_limit_error),
            stop=stop_after_attempt(5),
            wait=wait_exponential(multiplier=2, min=5, max=60),
            reraise=True,
        )
        def _call():
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, headers=headers, json=payload)
                if response.status_code == 429:
                    raise httpx.HTTPStatusError(
                        "Rate limit hit 429", request=response.request, response=response
                    )
                response.raise_for_status()
                return response.json()

        try:
            data = _call()
        except Exception as e:
            log.error("openrouter_rerank_sync_failed", error=str(e))
            raise e

        return self._build_reranked_nodes(nodes, data, self.top_n)

    async def _apostprocess_nodes(
        self,
        nodes: list[NodeWithScore],
        query_bundle: QueryBundle | None = None,
    ) -> list[NodeWithScore]:
        """Asynchronous reranking. Calls OpenRouter API with async client and retry on rate limits."""
        if not nodes or query_bundle is None:
            return nodes

        api_key = self.api_key or os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is not set.")

        url = "https://openrouter.ai/api/v1/rerank"
        headers = build_openrouter_headers(api_key)
        payload = {
            "model": self.model,
            "query": query_bundle.query_str,
            "documents": [node.node.get_content() for node in nodes],
            "top_n": self.top_n,
        }

        @retry(
            retry=retry_if_exception(is_openrouter_rate_limit_error),
            stop=stop_after_attempt(5),
            wait=wait_exponential(multiplier=2, min=5, max=60),
            reraise=True,
        )
        async def _call_async():
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code == 429:
                    raise httpx.HTTPStatusError(
                        "Rate limit hit 429", request=response.request, response=response
                    )
                response.raise_for_status()
                return response.json()

        try:
            data = await _call_async()
        except Exception as e:
            log.error("openrouter_rerank_async_failed", error=str(e))
            raise e

        return self._build_reranked_nodes(nodes, data, self.top_n)

    def _build_reranked_nodes(
        self, nodes: list[NodeWithScore], data: dict, top_n: int
    ) -> list[NodeWithScore]:
        """Extract reranked results from API response and rebuild NodeWithScore objects with relevance scores."""
        results = data.get("results", [])
        reranked_nodes = []
        for r in results:
            idx = r.get("index")
            score = r.get("relevance_score")
            if idx is not None and 0 <= idx < len(nodes):
                node = nodes[idx]
                reranked_nodes.append(NodeWithScore(node=node.node, score=float(score or 0.0)))
        return reranked_nodes[:top_n]
