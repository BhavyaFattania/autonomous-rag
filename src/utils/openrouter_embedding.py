"""
Custom LlamaIndex BaseEmbedding that calls /embeddings on OpenRouter.
Refactored for DI: accepts explicit api_key and api_base.
"""

import os

import nest_asyncio
from llama_index.core.bridge.pydantic import Field
from llama_index.core.embeddings import BaseEmbedding
from openai import AsyncOpenAI

nest_asyncio.apply()


class OpenRouterEmbedding(BaseEmbedding):
    """LlamaIndex embedding provider wrapping OpenRouter /embeddings endpoint."""

    model_name: str = Field(description="OpenRouter model ID")
    api_key: str = Field(description="OpenRouter API key")
    api_base: str = Field(default="https://openrouter.ai/api/v1")
    embed_batch_size: int = Field(default=1024)

    def __init__(
        self, model_name: str, api_key: str | None = None, api_base: str | None = None, **kwargs
    ):
        """Initialize with model_name and optional API credentials (fallback to env vars)."""
        api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        api_base = api_base or "https://openrouter.ai/api/v1"
        super().__init__(
            model_name=model_name,
            api_key=api_key,
            api_base=api_base,
            **kwargs,
        )

    def _client(self) -> AsyncOpenAI:
        """Create AsyncOpenAI client with OpenRouter base URL."""
        return AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.api_base,
        )

    async def _aget_query_embedding(self, query: str) -> list[float]:
        """Async: embed a single query string."""
        return (await self._embed_async([query]))[0]

    async def _aget_text_embedding(self, text: str) -> list[float]:
        """Async: embed a single text string."""
        return (await self._embed_async([text]))[0]

    async def _aget_text_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Async: embed multiple texts in batches."""
        import asyncio

        batches = [
            texts[i : i + self.embed_batch_size]
            for i in range(0, len(texts), self.embed_batch_size)
        ]
        results_nested = await asyncio.gather(*[self._embed_async(b) for b in batches])
        return [emb for batch_result in results_nested for emb in batch_result]

    async def _embed_async(self, texts: list[str]) -> list[list[float]]:
        """Call OpenRouter embeddings API; binary-split retries on partial failures."""
        if not texts:
            return []
        client = self._client()
        try:
            response = await client.embeddings.create(
                model=self.model_name,
                input=texts,
            )
        except Exception as e:
            raise RuntimeError(f"OpenRouter embedding API error: {e}") from e

        if not response.data:
            if len(texts) == 1:
                raise RuntimeError(
                    f"No embedding data received for model '{self.model_name}' "
                    f"even for a single text. Check model availability on OpenRouter."
                )
            mid = len(texts) // 2
            left = await self._embed_async(texts[:mid])
            right = await self._embed_async(texts[mid:])
            return left + right

        return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]

    def _get_query_embedding(self, query: str) -> list[float]:
        """Sync wrapper: embed a single query (creates event loop if needed)."""
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self._embed_async([query]))[0]

    def _get_text_embedding(self, text: str) -> list[float]:
        """Sync wrapper: embed a single text (creates event loop if needed)."""
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self._embed_async([text]))[0]

    def _get_text_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Sync wrapper: embed multiple texts (creates event loop if needed)."""
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self._aget_text_embeddings(texts))
