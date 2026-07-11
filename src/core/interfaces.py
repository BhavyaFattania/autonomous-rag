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
    ) -> str | dict: ...


# ─── Embedding Service ────────────────────────────────────────────────────────


@runtime_checkable
class IEmbeddingService(Protocol):
    async def embed_texts(self, texts: list[str]) -> list[list[float]]: ...
    async def embed_query(self, query: str) -> list[float]: ...
    def get_llama_index_embedding(self, model_name: str) -> Any: ...


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
