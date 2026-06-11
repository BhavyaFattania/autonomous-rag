import os
import httpx
from pydantic import Field
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import NodeWithScore, QueryBundle
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
from src.utils.logger import get_logger

log = get_logger("openrouter_reranker")


def is_openrouter_rate_limit_error(exception: Exception) -> bool:
    msg = str(exception).lower()
    return "429" in msg or "too_many_requests" in msg or "rate limit" in msg


class OpenRouterRerank(BaseNodePostprocessor):
    model: str = Field(default="cohere/rerank-v3.5")
    top_n: int = Field(default=5)

    @classmethod
    def class_name(cls) -> str:
        return "OpenRouterRerank"

    def _postprocess_nodes(
        self,
        nodes: list[NodeWithScore],
        query_bundle: QueryBundle | None = None,
    ) -> list[NodeWithScore]:
        if not nodes or query_bundle is None:
            return nodes

        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is not set.")

        url = "https://openrouter.ai/api/v1/rerank"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/autonomous-rag-optimizer",
            "X-Title": "RAG Optimizer",
        }
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
                    raise httpx.HTTPStatusError("Rate limit hit 429", request=response.request, response=response)
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
        if not nodes or query_bundle is None:
            return nodes

        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is not set.")

        url = "https://openrouter.ai/api/v1/rerank"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/autonomous-rag-optimizer",
            "X-Title": "RAG Optimizer",
        }
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
                    raise httpx.HTTPStatusError("Rate limit hit 429", request=response.request, response=response)
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
        results = data.get("results", [])
        reranked_nodes = []
        for r in results:
            idx = r.get("index")
            score = r.get("relevance_score")
            if idx is not None and 0 <= idx < len(nodes):
                node = nodes[idx]
                reranked_nodes.append(NodeWithScore(node=node.node, score=float(score or 0.0)))
        return reranked_nodes[:top_n]
