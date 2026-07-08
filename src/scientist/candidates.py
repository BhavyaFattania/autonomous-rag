# src/scientist/candidates.py

from src.utils.function_trace import trace_call


@trace_call
def get_structured_exploration_candidates(state, settings) -> list[dict]:
    index_configs = _available_index_configs(state, settings)
    variants = [
        {
            "retriever": "dense",
            "top_k": 3,
            "hybrid_alpha": 1.0,
            "reranker": None,
            "reranker_top_n": None,
        },
        {
            "retriever": "dense",
            "top_k": 5,
            "hybrid_alpha": 1.0,
            "reranker": None,
            "reranker_top_n": None,
        },
        {
            "retriever": "dense",
            "top_k": 7,
            "hybrid_alpha": 1.0,
            "reranker": None,
            "reranker_top_n": None,
        },
        {
            "retriever": "bm25",
            "top_k": 5,
            "hybrid_alpha": 0.0,
            "reranker": None,
            "reranker_top_n": None,
        },
        {
            "retriever": "weighted_hybrid_rrf",
            "top_k": 5,
            "hybrid_alpha": 0.7,
            "reranker": None,
            "reranker_top_n": None,
        },
        {
            "retriever": "weighted_hybrid_rrf",
            "top_k": 7,
            "hybrid_alpha": 0.3,
            "reranker": None,
            "reranker_top_n": None,
        },
        {
            "retriever": "query_fusion_simple",
            "top_k": 5,
            "hybrid_alpha": 0.5,
            "fusion_num_queries": 1,
            "reranker": None,
            "reranker_top_n": None,
        },
        {
            "retriever": "query_fusion_rrf",
            "top_k": 5,
            "hybrid_alpha": 0.7,
            "fusion_num_queries": 1,
            "reranker": None,
            "reranker_top_n": None,
        },
        {
            "retriever": "sentence_window_dense",
            "top_k": 5,
            "hybrid_alpha": 1.0,
            "reranker": None,
            "reranker_top_n": None,
        },
        {
            "retriever": "auto_merging",
            "top_k": 5,
            "hybrid_alpha": 1.0,
            "reranker": None,
            "reranker_top_n": None,
        },
        {
            "retriever": "recursive",
            "top_k": 5,
            "hybrid_alpha": 1.0,
            "reranker": None,
            "reranker_top_n": None,
        },
        {
            "retriever": "dense",
            "top_k": 5,
            "hybrid_alpha": 1.0,
            "reranker": "CohereRerank",
            "reranker_top_n": 5,
        },
    ]
    return _combine_candidates(index_configs, variants, variants_first=True, settings=settings)


@trace_call
def get_reranker_probe_candidates(state, settings) -> list[dict]:
    index_configs = _available_index_configs(state, settings)
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
        {
            "retriever": "dense",
            "top_k": 10,
            "hybrid_alpha": 1.0,
            "reranker": "CohereRerank",
            "reranker_top_n": 10,
        },
        {
            "retriever": "weighted_hybrid_rrf",
            "top_k": 10,
            "hybrid_alpha": 0.7,
            "reranker": "CohereRerank",
            "reranker_top_n": 10,
        },
        {
            "retriever": "query_fusion_rrf",
            "top_k": 10,
            "hybrid_alpha": 0.7,
            "fusion_num_queries": 1,
            "reranker": "CohereRerank",
            "reranker_top_n": 10,
        },
    ]
    return _combine_candidates(
        ordered_index_configs, variants, variants_first=False, settings=settings
    )


@trace_call
def get_fallback_candidates(state, settings) -> list[dict]:
    indexed_configs = _available_index_configs(state, settings)

    retrieval_variants = [
        {
            "retriever": "dense",
            "top_k": 10,
            "hybrid_alpha": 1.0,
            "reranker": None,
            "reranker_top_n": None,
        },
        {
            "retriever": "weighted_hybrid_rrf",
            "top_k": 12,
            "hybrid_alpha": 0.7,
            "reranker": None,
            "reranker_top_n": None,
        },
        {
            "retriever": "query_fusion_rrf",
            "top_k": 10,
            "hybrid_alpha": 0.7,
            "fusion_num_queries": 1,
            "reranker": None,
            "reranker_top_n": None,
        },
        {
            "retriever": "bm25",
            "top_k": 10,
            "hybrid_alpha": 0.0,
            "reranker": None,
            "reranker_top_n": None,
        },
        {
            "retriever": "dense",
            "top_k": 10,
            "hybrid_alpha": 1.0,
            "reranker": "CohereRerank",
            "reranker_top_n": 10,
        },
    ]

    return _combine_candidates(
        indexed_configs, retrieval_variants, variants_first=False, settings=settings
    )


@trace_call(log_return=False, label="_combine_candidates")  # return too large, skip it
def _combine_candidates(index_configs, variants, variants_first, settings) -> list[dict]:
    search_space = settings.search_space

    allowed_retrievers = search_space.allowed_retrievers
    allowed_rerankers = search_space.allowed_rerankers
    allowed_generator_models = search_space.allowed_generator_models

    # Filter variants first
    filtered_variants = []
    for var in variants:
        if allowed_retrievers is not None and var.get("retriever") not in allowed_retrievers:
            continue
        if allowed_rerankers is not None and var.get("reranker") not in allowed_rerankers:
            continue
        filtered_variants.append(var)
    variants = filtered_variants

    # Filter generator models
    gen_models = ["deepseek/deepseek-v4-flash"]
    if allowed_generator_models is not None:
        gen_models = [m for m in gen_models if m in allowed_generator_models]
        if not gen_models:
            # Fallback if the user allowed other models but not the default flash model
            gen_models = [allowed_generator_models[0]]

    generator_model = gen_models[0]

    candidates = []
    if variants_first:
        for variant in variants:
            for index_config in index_configs:
                candidates.append(
                    {
                        **index_config,
                        **variant,
                        "generator_model": generator_model,
                    }
                )
        return candidates

    for index_config in index_configs:
        for variant in variants:
            candidates.append(
                {
                    **index_config,
                    **variant,
                    "generator_model": generator_model,
                }
            )
    return candidates


@trace_call
def _available_index_configs(state, settings) -> list[dict]:
    search_space = settings.search_space
    allowed_node_parsers = search_space.allowed_node_parsers
    allowed_chunk_sizes = search_space.allowed_chunk_sizes
    allowed_chunk_overlaps = search_space.allowed_chunk_overlaps

    indexed_configs = []
    from src.indexer.collection_manager import collection_is_cached, list_available_index_configs

    if not settings.evaluation.allow_new_index_builds:
        indexed_configs = list_available_index_configs()
    if indexed_configs:
        # Filter available index configs according to search space constraints
        filtered = []
        for iconfig in indexed_configs:
            if (
                allowed_node_parsers is not None
                and iconfig.get("node_parser") not in allowed_node_parsers
            ):
                continue
            if (
                allowed_chunk_sizes is not None
                and iconfig.get("chunk_size") not in allowed_chunk_sizes
            ):
                continue
            if (
                allowed_chunk_overlaps is not None
                and iconfig.get("chunk_overlap") not in allowed_chunk_overlaps
            ):
                continue
            filtered.append(iconfig)
        return filtered

    baseline = state.get("baseline_config") or state.get("current_best_config") or {}
    embedding_model = baseline.get("embedding_model", "openai/text-embedding-3-small")
    candidates = [
        {
            "embedding_model": embedding_model,
            "node_parser": "sentence",
            "chunk_size": 512,
            "chunk_overlap": 128,
        },
        {
            "embedding_model": embedding_model,
            "node_parser": "sentence",
            "chunk_size": 1024,
            "chunk_overlap": 200,
        },
        {
            "embedding_model": embedding_model,
            "node_parser": "token",
            "chunk_size": 768,
            "chunk_overlap": 128,
        },
        {
            "embedding_model": embedding_model,
            "node_parser": "sentence_window",
            "chunk_size": 512,
            "chunk_overlap": 64,
            "window_size": 3,
        },
        {
            "embedding_model": embedding_model,
            "node_parser": "hierarchical",
            "chunk_size": 512,
            "chunk_overlap": 64,
        },
    ]
    semantic_candidates = [
        {
            "embedding_model": embedding_model,
            "node_parser": "semantic",
            "chunk_size": 768,
            "chunk_overlap": 128,
            "semantic_threshold": 95,
            "semantic_buffer_size": 1,
        },
        {
            "embedding_model": embedding_model,
            "node_parser": "semantic_double",
            "chunk_size": 768,
            "chunk_overlap": 128,
            "semantic_threshold": 90,
            "semantic_buffer_size": 1,
        },
    ]
    if settings.evaluation.allow_expensive_parser_builds:
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

    # Filter mock candidates list
    filtered = []
    for cand in candidates:
        if allowed_node_parsers is not None and cand.get("node_parser") not in allowed_node_parsers:
            continue
        if allowed_chunk_sizes is not None and cand.get("chunk_size") not in allowed_chunk_sizes:
            continue
        if (
            allowed_chunk_overlaps is not None
            and cand.get("chunk_overlap") not in allowed_chunk_overlaps
        ):
            continue
        filtered.append(cand)
    return filtered
