"""Tests for parser_slug, which builds a cache-key-safe slug from a RAGConfig's parser settings."""

from src.indexer.parser_registry import parser_slug
from src.models.rag_config import RAGConfig


def _config(**overrides):
    """Build a RAGConfig with sane defaults, overridable per test."""
    data = {
        "chunk_size": 512,
        "chunk_overlap": 128,
        "top_k": 10,
        "hybrid_alpha": 0.7,
        "embedding_model": "openai/text-embedding-3-small",
        "reranker": None,
        "reranker_top_n": None,
        "generator_model": "deepseek/deepseek-v4-flash",
    }
    data.update(overrides)
    return RAGConfig(**data)


def test_parser_slug_distinguishes_semantic_params():
    """Different semantic_threshold values must produce different slugs (no cache collisions)."""
    a = parser_slug(_config(node_parser="semantic", semantic_threshold=95, semantic_buffer_size=1))
    b = parser_slug(_config(node_parser="semantic", semantic_threshold=90, semantic_buffer_size=1))

    assert a != b
    assert "semantic" in a


def test_parser_slug_avoids_underscores_in_parser_name():
    """Underscores in the parser name itself are converted to hyphens to keep the slug delimiter unambiguous."""
    slug = parser_slug(_config(node_parser="semantic_double", semantic_threshold=90))

    assert slug.startswith("semantic-double_")
