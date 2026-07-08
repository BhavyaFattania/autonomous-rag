"""Validates proposed RAG configs against developer-defined search space constraints."""

from src.models.rag_config import RAGConfig


def validator_node(state, settings, env=None) -> dict:
    """Check proposed config against allowed values, parser/retriever availability, and budget constraints."""
    try:
        config = RAGConfig(**state["proposed_config"])

        search_space = settings.search_space
        allowed_node_parsers = search_space.allowed_node_parsers
        if allowed_node_parsers is not None and config.node_parser not in allowed_node_parsers:
            raise ValueError(
                f"node_parser='{config.node_parser}' is not in developer allowed list: {allowed_node_parsers}"
            )

        allowed_retrievers = search_space.allowed_retrievers
        if allowed_retrievers is not None and config.retriever not in allowed_retrievers:
            raise ValueError(
                f"retriever='{config.retriever}' is not in developer allowed list: {allowed_retrievers}"
            )

        allowed_chunk_sizes = search_space.allowed_chunk_sizes
        if allowed_chunk_sizes is not None and config.chunk_size not in allowed_chunk_sizes:
            raise ValueError(
                f"chunk_size={config.chunk_size} is not in developer allowed list: {allowed_chunk_sizes}"
            )

        allowed_chunk_overlaps = search_space.allowed_chunk_overlaps
        if (
            allowed_chunk_overlaps is not None
            and config.chunk_overlap not in allowed_chunk_overlaps
        ):
            raise ValueError(
                f"chunk_overlap={config.chunk_overlap} is not in developer allowed list: {allowed_chunk_overlaps}"
            )

        allowed_generator_models = search_space.allowed_generator_models
        if (
            allowed_generator_models is not None
            and config.generator_model not in allowed_generator_models
        ):
            raise ValueError(
                f"generator_model='{config.generator_model}' is not in developer allowed list: {allowed_generator_models}"
            )

        allowed_rerankers = search_space.allowed_rerankers
        if allowed_rerankers is not None and config.reranker not in allowed_rerankers:
            raise ValueError(
                f"reranker='{config.reranker}' is not in developer allowed list: {allowed_rerankers}"
            )

        from src.indexer.collection_manager import collection_is_cached

        if config.node_parser in {"semantic", "semantic_double"} and not collection_is_cached(
            config
        ):
            if not settings.evaluation.allow_expensive_parser_builds:
                raise ValueError(
                    f"node_parser={config.node_parser} requires a prebuilt cache "
                    "or allow_expensive_parser_builds=true"
                )
        if config.retriever == "summary_embedding":
            if not settings.evaluation.allow_summary_embedding_retriever:
                raise ValueError(
                    "retriever=summary_embedding is disabled for live search; "
                    "prebuild a summary index and enable allow_summary_embedding_retriever"
                )
        if not settings.evaluation.allow_new_index_builds:
            if not collection_is_cached(config):
                raise ValueError(
                    "Config requires a new index build, but allow_new_index_builds=false"
                )
        if config.reranker == "CohereRerank":
            if not (env or {}).get("OPENROUTER_API_KEY"):
                raise ValueError("OPENROUTER_API_KEY must be set when reranker is CohereRerank")
        return {"validated_config": config.model_dump(), "status": "RUNNING"}
    except Exception as e:
        return {
            "validated_config": {},
            "status": "FAILED_VALIDATION",
            "failure_reason": f"Config validation failed: {e}",
        }
