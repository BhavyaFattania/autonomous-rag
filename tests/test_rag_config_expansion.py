import pytest

from src.models.rag_config import RAGConfig
from src.orchestrator.validator import validator_node
from src.rag_pipeline.retriever import _build_query_fusion_llm
from config.settings import Settings, EvalSettings


def _base(**overrides):
    config = {
        "chunk_size": 512,
        "chunk_overlap": 128,
        "top_k": 10,
        "hybrid_alpha": 0.7,
        "embedding_model": "openai/text-embedding-3-small",
        "reranker": None,
        "reranker_top_n": None,
        "generator_model": "deepseek/deepseek-v4-flash",
    }
    config.update(overrides)
    return config


def test_defaults_keep_legacy_config_valid():
    config = RAGConfig(**_base())

    assert config.node_parser == "sentence"
    assert config.retriever == "weighted_hybrid_rrf"


def test_auto_merging_requires_hierarchical_parser():
    with pytest.raises(ValueError):
        RAGConfig(**_base(node_parser="sentence", retriever="auto_merging"))

    config = RAGConfig(**_base(node_parser="hierarchical", retriever="auto_merging"))
    assert config.retriever == "auto_merging"


def test_sentence_window_dense_requires_sentence_window_parser():
    with pytest.raises(ValueError):
        RAGConfig(**_base(node_parser="sentence", retriever="sentence_window_dense"))

    config = RAGConfig(
        **_base(node_parser="sentence_window", retriever="sentence_window_dense")
    )
    assert config.window_size == 3


def test_query_fusion_gets_default_mode_and_num_queries():
    config = RAGConfig(**_base(retriever="query_fusion_rrf"))

    assert config.fusion_mode == "reciprocal_rerank"
    assert config.fusion_num_queries == 1


def test_query_fusion_single_query_uses_mock_llm():
    config = RAGConfig(**_base(retriever="query_fusion_rrf"))

    assert _build_query_fusion_llm(config).__class__.__name__ == "MockLLM"


def test_summary_embedding_remains_configurable_but_guarded_by_validator():
    config = RAGConfig(**_base(retriever="summary_embedding"))

    assert config.retriever == "summary_embedding"


def _blocking_settings() -> Settings:
    return Settings(evaluation=EvalSettings(
        allow_new_index_builds=True,
        allow_expensive_parser_builds=False,
        allow_summary_embedding_retriever=False,
    ))


def test_validator_blocks_disabled_summary_embedding():
    result = validator_node(
        {"proposed_config": _base(retriever="summary_embedding")},
        settings=_blocking_settings(),
    )

    assert result["status"] == "FAILED_VALIDATION"
    assert "summary_embedding is disabled" in result["failure_reason"]


def test_validator_blocks_uncached_semantic_parser(monkeypatch):
    monkeypatch.setattr("src.indexer.collection_manager.collection_is_cached", lambda _: False)
    result = validator_node(
        {
            "proposed_config": _base(
                node_parser="semantic",
                semantic_threshold=95,
                semantic_buffer_size=1,
            )
        },
        settings=_blocking_settings(),
    )

    assert result["status"] == "FAILED_VALIDATION"
    assert "requires a prebuilt cache" in result["failure_reason"]
