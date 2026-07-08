"""Indexing subpackage: collection management, caching, and node parsing."""

from src.indexer.collection_cache import (
    bm25_node_count,
    build_embed_model,
    cache_is_complete,
    effective_corpus_limit,
    expensive_parser_builds_allowed,
    load_bm25_engine,
    load_bm25_nodes,
    load_corpus_as_documents,
    new_index_builds_allowed,
)
from src.indexer.collection_manager import (
    collection_is_cached,
    get_or_build_collection,
    indexer_node,
    list_available_index_configs,
)
from src.indexer.collection_names import (
    bm25_cache_path,
    bm25_engine_path,
    collection_name,
    get_chroma_client,
)
from src.indexer.index_builder import build_bm25_cache_only, build_collection
from src.indexer.parser_registry import build_node_parser, parser_slug

__all__ = [
    "collection_name",
    "bm25_cache_path",
    "bm25_engine_path",
    "get_chroma_client",
    "bm25_node_count",
    "cache_is_complete",
    "new_index_builds_allowed",
    "expensive_parser_builds_allowed",
    "effective_corpus_limit",
    "load_corpus_as_documents",
    "build_embed_model",
    "load_bm25_nodes",
    "load_bm25_engine",
    "list_available_index_configs",
    "collection_is_cached",
    "get_or_build_collection",
    "indexer_node",
    "build_collection",
    "build_bm25_cache_only",
    "parser_slug",
    "build_node_parser",
]
