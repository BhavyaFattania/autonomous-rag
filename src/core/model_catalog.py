"""Registry mapping RAGConfig model identifiers to the provider that serves them.

Mirrors `src/core/provider_factory.py`'s `_PROVIDER_BUILDERS` seam: adding a new
embedding/reranker provider means adding one catalog entry and one `_build_*`
function, without touching call sites of `build_embedding_model`/`build_reranker`.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

EMBEDDING_CATALOG: dict[str, dict[str, Any]] = {
    "openai/text-embedding-3-small": {"provider": "openrouter", "dimensions": 1536},
    "qwen/qwen3-embedding-8b": {"provider": "openrouter", "dimensions": 4096},
    "qwen/qwen3-embedding-4b": {"provider": "openrouter", "dimensions": 2560},
    "baai/bge-m3": {"provider": "openrouter", "dimensions": 1024},
}

RERANKER_CATALOG: dict[str, dict[str, Any]] = {
    "CohereRerank": {"provider": "openrouter", "model_id": "cohere/rerank-v3.5"},
}


def _build_openrouter_embedding(model_id: str, env: dict | None):
    from src.utils.openrouter_embedding import OpenRouterEmbedding

    api_key = env.get("OPENROUTER_API_KEY") if env else None
    return OpenRouterEmbedding(model_name=model_id, api_key=api_key)


def _build_openrouter_reranker(model_id: str, top_n: int, env: dict | None):
    from src.rag_pipeline.openrouter_reranker import OpenRouterRerank

    spec = RERANKER_CATALOG[model_id]
    api_key = env.get("OPENROUTER_API_KEY") if env else None
    return OpenRouterRerank(model=spec["model_id"], top_n=top_n, api_key=api_key)


_EMBEDDING_BUILDERS: dict[str, Callable[[str, dict | None], Any]] = {
    "openrouter": _build_openrouter_embedding,
}

_RERANKER_BUILDERS: dict[str, Callable[[str, int, dict | None], Any]] = {
    "openrouter": _build_openrouter_reranker,
}


def _unknown_embedding_model_error(model_id: str) -> ValueError:
    supported = ", ".join(sorted(EMBEDDING_CATALOG))
    return ValueError(f"Unknown embedding_model {model_id!r}. Supported models: {supported}.")


def _unknown_reranker_error(reranker_name: str) -> ValueError:
    supported = ", ".join(sorted(RERANKER_CATALOG))
    return ValueError(f"Unknown reranker {reranker_name!r}. Supported rerankers: {supported}.")


def build_embedding_model(model_id: str, env: dict | None = None):
    """Instantiate the concrete embedding model for `model_id` via its catalog provider."""
    try:
        spec = EMBEDDING_CATALOG[model_id]
    except KeyError:
        raise _unknown_embedding_model_error(model_id) from None
    return _EMBEDDING_BUILDERS[spec["provider"]](model_id, env)


def build_reranker(reranker_name: str, top_n: int, env: dict | None = None):
    """Instantiate the concrete reranker for `reranker_name` via its catalog provider."""
    try:
        spec = RERANKER_CATALOG[reranker_name]
    except KeyError:
        raise _unknown_reranker_error(reranker_name) from None
    return _RERANKER_BUILDERS[spec["provider"]](reranker_name, top_n, env)


def embedding_dimensions(model_id: str) -> int:
    """Return the vector dimensionality for `model_id`."""
    try:
        return EMBEDDING_CATALOG[model_id]["dimensions"]
    except KeyError:
        raise _unknown_embedding_model_error(model_id) from None
