"""Caching and loading utilities for BM25 nodes, embedding models, and corpus data.

Manages cache validation, document loading limits, and model instantiation.
"""

import json
import pickle
from pathlib import Path

from llama_index.core import Document

from src.indexer.collection_names import bm25_cache_path, bm25_engine_path
from src.models.rag_config import RAGConfig
from src.utils.logger import get_logger

log = get_logger("indexer")

MAX_CORPUS_DOCS = 15_000


def bm25_node_count(collection_name: str) -> int | None:
    """Load BM25 node cache and return count, or None if not found."""
    cache_path = bm25_cache_path(collection_name)
    if not cache_path.exists():
        return None
    with open(cache_path, "rb") as f:
        return len(pickle.load(f))


def cache_is_complete(collection_name: str, vector_count: int) -> bool:
    """Check if both BM25 cache and vector store are fully built and synchronized."""
    node_count = bm25_node_count(collection_name)
    if node_count is None or not bm25_engine_path(collection_name).exists():
        return False
    return vector_count == node_count


def new_index_builds_allowed(settings) -> bool:
    """Check if creating new indices is allowed by settings."""
    return settings.evaluation.allow_new_index_builds


def expensive_parser_builds_allowed(settings) -> bool:
    """Check if expensive parsers (semantic, semantic_double) can be used."""
    return settings.evaluation.allow_expensive_parser_builds


def effective_corpus_limit(config: RAGConfig, settings) -> int:
    """Get document limit based on parser type; expensive parsers get a lower limit."""
    if config.node_parser in {"semantic", "semantic_double"}:
        return settings.evaluation.max_docs_for_expensive_parsers
    return MAX_CORPUS_DOCS


def load_corpus_as_documents(corpus_path: Path, limit: int = MAX_CORPUS_DOCS):
    """Load JSONL corpus into Document objects up to the specified limit."""
    docs = []
    for line in corpus_path.read_text(encoding="utf-8").strip().splitlines():
        item = json.loads(line)
        docs.append(Document(text=item["text"], metadata={"title": item["title"]}))
        if len(docs) >= limit:
            break
    log.info("corpus_loaded", docs=len(docs), capped=(len(docs) == limit), limit=limit)
    return docs


def build_embed_model(config: RAGConfig, env=None):
    """Instantiate embedding model from config via the model catalog factory."""
    from src.core.model_catalog import build_embedding_model

    return build_embedding_model(config.embedding_model, env)


def load_bm25_nodes(collection_name: str) -> list:
    """Load pickled BM25 nodes from cache; raise if not found."""
    cache_path = bm25_cache_path(collection_name)
    if not cache_path.exists():
        raise FileNotFoundError(
            f"BM25 node cache not found at {cache_path}. "
            f"Delete the ChromaDB collection and re-index."
        )
    with open(cache_path, "rb") as f:
        nodes = pickle.load(f)
    return nodes


def load_bm25_engine(collection_name: str):
    engine_path = bm25_engine_path(collection_name)
    if not engine_path.exists():
        raise FileNotFoundError(f"BM25 engine cache not found at {engine_path}")
    with open(engine_path, "rb") as f:
        return pickle.load(f)
