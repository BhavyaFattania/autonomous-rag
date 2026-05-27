from src.models.rag_config import RAGConfig

def validator_node(state) -> dict:
    try:
        config = RAGConfig(**state["proposed_config"])
        from src.orchestrator.config_loader import load_run_settings
        settings = load_run_settings()
        from src.indexer.collection_manager import collection_is_cached
        if config.node_parser in {"semantic", "semantic_double"} and not collection_is_cached(config):
            if not settings["evaluation"].get("allow_expensive_parser_builds", False):
                raise ValueError(
                    f"node_parser={config.node_parser} requires a prebuilt cache "
                    "or allow_expensive_parser_builds=true"
                )
        if config.retriever == "summary_embedding":
            if not settings["evaluation"].get("allow_summary_embedding_retriever", False):
                raise ValueError(
                    "retriever=summary_embedding is disabled for live search; "
                    "prebuild a summary index and enable allow_summary_embedding_retriever"
                )
        if not settings["evaluation"].get("allow_new_index_builds", True):
            if not collection_is_cached(config):
                raise ValueError(
                    "Config requires a new index build, but allow_new_index_builds=false"
                )
        if config.reranker == "CohereRerank":
            import os
            if not os.environ.get("COHERE_API_KEY"):
                raise ValueError("COHERE_API_KEY must be set when reranker is CohereRerank")
        return {
            "validated_config": config.model_dump(),
            "status": "RUNNING"
        }
    except Exception as e:
        return {
            "validated_config": {},
            "status": "FAILED_VALIDATION",
            "failure_reason": f"Config validation failed: {e}"
        }
