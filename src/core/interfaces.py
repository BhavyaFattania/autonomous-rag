"""
Interface definitions for all external dependencies.
Enables DI: module → interface → implementation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable

# ─── Cost Tracking ────────────────────────────────────────────────────────────


@runtime_checkable
class ICostTracker(Protocol):
    def initialize(
        self, hard_ceiling: float, warning_threshold: float, start_cost: float = 0.0
    ) -> None: ...
    def add_cost(self, usd: float) -> float: ...
    def get_total(self) -> float: ...


# ─── LLM Client ───────────────────────────────────────────────────────────────


@runtime_checkable
class ILLMClient(Protocol):
    async def call(
        self,
        model_id: str,
        messages: list[dict],
        max_tokens: int,
        task: str,
        reasoning_effort: str | None = None,
        temperature: float | None = 0.1,
        fallback_model_id: str | None = None,
        return_reasoning: bool = False,
        response_format: str | None = None,
    ) -> str | dict:
        """Send a chat-completion-style request and return the response.

        `reasoning_effort` and `fallback_model_id` are optional provider hints,
        not universal semantics: they originate from OpenRouter/OpenAI-o-series
        capabilities (reasoning-effort tiers, routed fallback models). An
        implementation for a provider without an equivalent capability MUST
        accept these parameters and silently ignore them rather than raising —
        callers are not expected to know which providers support which hints.
        """
        ...


# ─── Embedding Service ────────────────────────────────────────────────────────


@runtime_checkable
class IEmbeddingService(Protocol):
    """Provider-agnostic text embedding. Deliberately excludes any single
    consuming framework's adapter shape (e.g. LlamaIndex) — see
    `ILlamaIndexEmbeddingAdapter` for that concern."""

    async def embed_texts(self, texts: list[str]) -> list[list[float]]: ...
    async def embed_query(self, query: str) -> list[float]: ...


@runtime_checkable
class ILlamaIndexEmbeddingAdapter(Protocol):
    """Optional capability: expose this embedding service as a LlamaIndex
    `BaseEmbedding`-compatible object, for code that must hand embeddings to
    LlamaIndex APIs (indexers, retrievers). Not every `IEmbeddingService`
    implementation needs to satisfy this — only ones consumed by LlamaIndex
    pipeline code."""

    def get_llama_index_embedding(self, model_name: str) -> Any: ...


# ─── Reranker ─────────────────────────────────────────────────────────────────


@runtime_checkable
class IReranker(Protocol):
    """Provider-agnostic reranking. Returns `(original_index, relevance_score)`
    pairs for the top `top_n` documents, sorted by descending relevance.
    Framework-specific adapters (e.g. LlamaIndex `BaseNodePostprocessor`) wrap
    this contract rather than replacing it."""

    async def rerank(
        self, query: str, documents: list[str], top_n: int
    ) -> list[tuple[int, float]]: ...


# ─── Database ─────────────────────────────────────────────────────────────────


@runtime_checkable
class IDatabase(Protocol):
    path: str

    async def init(self) -> None: ...
    def connect(self) -> Any: ...


# ─── Chroma Client Factory ────────────────────────────────────────────────────


@runtime_checkable
class IChromaClientFactory(Protocol):
    def get_client(self) -> Any: ...
    def path(self) -> Path: ...


# ─── RAGAS Factory ─────────────────────────────────────────────────────────────


@runtime_checkable
class IRagasFactory(Protocol):
    def build_llm(self, model_routing: Any, env: dict | None = None) -> Any: ...
    def build_embeddings(self, model_name: str, env: dict | None = None) -> Any: ...
    def build_metrics(self, metric_names: list[str]) -> list: ...


# ─── Model Routing Provider ───────────────────────────────────────────────────


class IModelRoutingProvider(Protocol):
    def get_model_id(self, role: str) -> str: ...
    def get_config(self, role: str) -> Any: ...
