from src.models.rag_config import RAGConfig

def validator_node(state) -> dict:
    try:
        config = RAGConfig(**state["proposed_config"])
        return {
            "validated_config": config.model_dump(),
            "status": "RUNNING"
        }
    except Exception as e:
        return {
            "status": "FAILED_VALIDATION",
            "failure_reason": f"Config validation failed: {e}"
        }
