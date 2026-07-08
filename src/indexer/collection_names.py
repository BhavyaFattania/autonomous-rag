"""Collection and cache path management.

Generates deterministic collection names from configs and paths for persistent caching.
"""
from pathlib import Path

import chromadb

from src.indexer.parser_registry import parser_slug
from src.models.rag_config import RAGConfig

CHROMA_PATH = Path("data/chroma")
BM25_PATH = Path("data/bm25")

CHROMA_PATH.mkdir(parents=True, exist_ok=True)
BM25_PATH.mkdir(parents=True, exist_ok=True)


def collection_name(config: RAGConfig) -> str:
    """Generate deterministic Chroma collection name from embedding model and parser config."""
    slug = config.embedding_model.replace("/", "_").replace("-", "_").replace(".", "_")
    if config.node_parser == "sentence":
        return f"rag_{slug}_{config.chunk_size}_{config.chunk_overlap}"
    return f"rag_{slug}_{parser_slug(config)}"


def bm25_cache_path(name: str) -> Path:
    """Return Path to pickled BM25 node cache for collection."""
    return BM25_PATH / f"{name}_nodes.pkl"


def bm25_engine_path(name: str) -> Path:
    """Return Path to pickled BM25 engine (corpus) for collection."""
    return BM25_PATH / f"{name}_engine.pkl"


def get_chroma_client(path: str | Path | None = None) -> chromadb.PersistentClient:
    """Get or create persistent Chroma client at optional path (defaults to data/chroma)."""
    resolved = str(path) if path else str(CHROMA_PATH)
    return chromadb.PersistentClient(path=resolved)
