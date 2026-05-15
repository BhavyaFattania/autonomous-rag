"""
src/utils/openrouter_embedding.py

A custom LlamaIndex BaseEmbedding that calls the OpenAI-compatible
/embeddings endpoint on OpenRouter — accepts ANY model string without
the hardcoded OpenAIEmbeddingModelType enum validation.
"""

import os
from typing import List

from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.bridge.pydantic import Field
from openai import AsyncOpenAI


class OpenRouterEmbedding(BaseEmbedding):
    """
    Drop-in LlamaIndex embedding class for any model available on OpenRouter.
    Uses the OpenAI-compatible /embeddings endpoint at https://openrouter.ai/api/v1.
    """

    model_name: str = Field(description="OpenRouter model ID, e.g. 'qwen/qwen3-embedding-8b'")
    api_key: str    = Field(description="OpenRouter API key")
    api_base: str   = Field(default="https://openrouter.ai/api/v1")
    # embed_batch_size: texts sent per _aget_text_embeddings call.
    # 1024 is high throughput; auto-halving handles models with smaller limits.
    embed_batch_size: int = Field(default=1024)

    def __init__(self, model_name: str, api_key: str | None = None, **kwargs):
        api_key = api_key or os.environ["OPENROUTER_API_KEY"]
        super().__init__(
            model_name=model_name,
            api_key=api_key,
            **kwargs,
        )

    def _client(self) -> AsyncOpenAI:
        return AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.api_base,
        )

    # ── async (primary) ───────────────────────────────────────────────────────

    async def _aget_query_embedding(self, query: str) -> List[float]:
        return await self._embed([query])[0] if False else (await self._embed_async([query]))[0]

    async def _aget_text_embedding(self, text: str) -> List[float]:
        return (await self._embed_async([text]))[0]

    async def _aget_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        import asyncio
        batches = [
            texts[i : i + self.embed_batch_size]
            for i in range(0, len(texts), self.embed_batch_size)
        ]
        # Fire all batches concurrently — much faster than awaiting sequentially
        results_nested = await asyncio.gather(*[self._embed_async(b) for b in batches])
        # Flatten: [[emb, emb, ...], [emb, emb, ...], ...] → [emb, emb, ...]
        return [emb for batch_result in results_nested for emb in batch_result]

    async def _embed_async(self, texts: List[str]) -> List[List[float]]:
        """Call OpenRouter /embeddings. Auto-halves batch on empty response."""
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
            # Model rejected the batch size — split and retry recursively
            if len(texts) == 1:
                raise RuntimeError(
                    f"No embedding data received for model '{self.model_name}' "
                    f"even for a single text. Check model availability on OpenRouter."
                )
            mid = len(texts) // 2
            left  = await self._embed_async(texts[:mid])
            right = await self._embed_async(texts[mid:])
            return left + right

        return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]

    # ── sync fallbacks (required by BaseEmbedding ABC) ────────────────────────

    def _get_query_embedding(self, query: str) -> List[float]:
        import asyncio
        return asyncio.get_event_loop().run_until_complete(
            self._embed_async([query])
        )[0]

    def _get_text_embedding(self, text: str) -> List[float]:
        import asyncio
        return asyncio.get_event_loop().run_until_complete(
            self._embed_async([text])
        )[0]

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        import asyncio
        return asyncio.get_event_loop().run_until_complete(
            self._aget_text_embeddings(texts)
        )
