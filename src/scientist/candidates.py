# src/scientist/candidates.py

import json


def get_structured_exploration_candidates(state) -> list[dict]:
    index_configs = _available_index_configs(state)
    variants = [
        {"retriever": "dense", "top_k": 3, "hybrid_alpha": 1.0, "reranker": None, "reranker_top_n": None},
        {"retriever": "dense", "top_k": 5, "hybrid_alpha": 1.0, "reranker": None, "reranker_top_n": None},
        {"retriever": "dense", "top_k": 7, "hybrid_alpha": 1.0, "reranker": None, "reranker_top_n": None},
        {"retriever": "bm25", "top_k": 5, "hybrid_alpha": 0.0, "reranker": None, "reranker_top_n": None},
        {"retriever": "weighted_hybrid_rrf", "top_k": 5, "hybrid_alpha": 0.7, "reranker": None, "reranker_top_n": None},
        {"retriever": "weighted_hybrid_rrf", "top_k": 7, "hybrid_alpha": 0.3, "reranker": None, "reranker_top_n": None},
        {"retriever": "query_fusion_simple", "top_k": 5, "hybrid_alpha": 0.5, "fusion_num_queries": 1, "reranker": None, "reranker_top_n": None},
        {"retriever": "query_fusion_rrf", "top_k": 5, "hybrid_alpha": 0.7, "fusion_num_queries": 1, "reranker": None, "reranker_top_n": None},
        {"retriever": "sentence_window_dense", "top_k": 5, "hybrid_alpha": 1.0, "reranker": None, "reranker_top_n": None},
        {"retriever": "auto_merging", "top_k": 5, "hybrid_alpha": 1.0, "reranker": None, "reranker_top_n": None},
        {"retriever": "recursive", "top_k": 5, "hybrid_alpha": 1.0, "reranker": None, "reranker_top_n": None},
        {"retriever": "dense", "top_k": 5, "hybrid_alpha": 1.0, "reranker": "CohereRerank", "reranker_top_n": 5},
    ]
    return _combine_candidates(index_configs, variants, variants_first=True)


def get_reranker_probe_candidates(state) -> list[dict]:
    index_configs = _available_index_configs(state)
    current_best = state.get("current_best_config", {})
    preferred_chunk = {
        "embedding_model": current_best.get("embedding_model"),
        "chunk_size": current_best.get("chunk_size"),
        "chunk_overlap": current_best.get("chunk_overlap"),
    }
    ordered_index_configs = sorted(
        index_configs,
        key=lambda item: 0 if all(item.get(k) == v for k, v in preferred_chunk.items()) else 1,
    )
    variants = [
        {"retriever": "dense", "top_k": 10, "hybrid_alpha": 1.0, "reranker": "CohereRerank", "reranker_top_n": 10},
        {"retriever": "weighted_hybrid_rrf", "top_k": 10, "hybrid_alpha": 0.7, "reranker": "CohereRerank", "reranker_top_n": 10},
        {"retriever": "query_fusion_rrf", "top_k": 10, "hybrid_alpha": 0.7, "fusion_num_queries": 1, "reranker": "CohereRerank", "reranker_top_n": 10},
    ]
    return _combine_candidates(ordered_index_configs, variants, variants_first=False)


def get_fallback_candidates(state) -> list[dict]:
    indexed_configs = _available_index_configs(state)

    retrieval_variants = [
        {"retriever": "dense", "top_k": 10, "hybrid_alpha": 1.0, "reranker": None, "reranker_top_n": None},
        {"retriever": "weighted_hybrid_rrf", "top_k": 12, "hybrid_alpha": 0.7, "reranker": None, "reranker_top_n": None},
        {"retriever": "query_fusion_rrf", "top_k": 10, "hybrid_alpha": 0.7, "fusion_num_queries": 1, "reranker": None, "reranker_top_n": None},
        {"retriever": "bm25", "top_k": 10, "hybrid_alpha": 0.0, "reranker": None, "reranker_top_n": None},
        {"retriever": "dense", "top_k": 10, "hybrid_alpha": 1.0, "reranker": "CohereRerank", "reranker_top_n": 10},
    ]

    return _combine_candidates(indexed_configs, retrieval_variants, variants_first=False)


def _combine_candidates(index_configs: list[dict], variants: list[dict], variants_first: bool) -> list[dict]:
    candidates = []
    if variants_first:
        for variant in variants:
            for index_config in index_configs:
                candidates.append({
                    **index_config,
                    **variant,
                    "generator_model": "deepseek/deepseek-v4-flash",
                })
        return candidates

    for index_config in index_configs:
        for variant in variants:
            candidates.append({
                **index_config,
                **variant,
                "generator_model": "deepseek/deepseek-v4-flash",
            })
    return candidates


def _available_index_configs(state) -> list[dict]:
    from src.orchestrator.config_loader import load_run_settings

    settings = load_run_settings()
    indexed_configs = []
    from src.indexer.collection_manager import collection_is_cached, list_available_index_configs

    if not settings["evaluation"].get("allow_new_index_builds", True):
        indexed_configs = list_available_index_configs()
    if indexed_configs:
        return indexed_configs

    baseline = state.get("baseline_config") or state.get("current_best_config") or {}
    embedding_model = baseline.get("embedding_model", "openai/text-embedding-3-small")
    candidates = [
        {"embedding_model": embedding_model, "node_parser": "sentence", "chunk_size": 512, "chunk_overlap": 128},
        {"embedding_model": embedding_model, "node_parser": "sentence", "chunk_size": 1024, "chunk_overlap": 200},
        {"embedding_model": embedding_model, "node_parser": "token", "chunk_size": 768, "chunk_overlap": 128},
        {"embedding_model": embedding_model, "node_parser": "sentence_window", "chunk_size": 512, "chunk_overlap": 64, "window_size": 3},
        {"embedding_model": embedding_model, "node_parser": "hierarchical", "chunk_size": 512, "chunk_overlap": 64},
    ]
    semantic_candidates = [
        {"embedding_model": embedding_model, "node_parser": "semantic", "chunk_size": 768, "chunk_overlap": 128, "semantic_threshold": 95, "semantic_buffer_size": 1},
        {"embedding_model": embedding_model, "node_parser": "semantic_double", "chunk_size": 768, "chunk_overlap": 128, "semantic_threshold": 90, "semantic_buffer_size": 1},
    ]
    if settings["evaluation"].get("allow_expensive_parser_builds", False):
        candidates.extend(semantic_candidates)
    else:
        from src.models.rag_config import RAGConfig

        for candidate in semantic_candidates:
            try:
                config = RAGConfig(
                    **candidate,
                    top_k=5,
                    hybrid_alpha=1.0,
                    retriever="dense",
                    reranker=None,
                    reranker_top_n=None,
                    generator_model="deepseek/deepseek-v4-flash",
                )
                if collection_is_cached(config):
                    candidates.append(candidate)
            except ValueError:
                continue
    return candidates
