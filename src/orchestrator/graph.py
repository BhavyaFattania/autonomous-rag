import uuid
from datetime import datetime, timezone
from langgraph.graph import StateGraph, END
from src.orchestrator.state import WorkflowState


from langgraph.checkpoint.base import BaseCheckpointSaver

def build_graph(checkpointer: BaseCheckpointSaver = None) -> StateGraph:
    """
    Build and compile the LangGraph state machine.
    """
    workflow = StateGraph(WorkflowState)

    # Add nodes (imports deferred to avoid circular imports at module load)
    from src.scientist.brain import scientist_node
    from src.orchestrator.validator import validator_node
    from src.scientist.deduplicator import deduplicator_node
    from src.orchestrator.budget_guard import budget_guard_node
    from src.indexer.collection_manager import indexer_node
    from src.rag_pipeline.smoke_tester import smoke_test_node
    from src.evaluator.ragas_runner import evaluator_node
    from src.evaluator.scorer import acceptance_node
    from src.storage.experiment_log import recorder_node
    from src.scientist.reflection import reflection_node
    from src.reporter.report_writer import report_writer_node

    workflow.add_node("scientist", scientist_node)
    workflow.add_node("validator", validator_node)
    workflow.add_node("deduplicator", deduplicator_node)
    workflow.add_node("budget_guard", budget_guard_node)
    workflow.add_node("indexer", indexer_node)
    workflow.add_node("smoke_test", smoke_test_node)
    workflow.add_node("evaluator", evaluator_node)
    workflow.add_node("acceptance", acceptance_node)
    workflow.add_node("recorder", recorder_node)
    workflow.add_node("reflection", reflection_node)
    workflow.add_node("report_writer", report_writer_node)

    # Entry point
    workflow.set_entry_point("scientist")

    # Linear edges
    workflow.add_edge("scientist", "validator")
    workflow.add_edge("acceptance", "recorder")
    workflow.add_edge("reflection", "scientist")

    # Conditional edges
    workflow.add_conditional_edges("validator",    _after_validator)
    workflow.add_conditional_edges("deduplicator", _after_deduplicator)
    workflow.add_conditional_edges("budget_guard", _after_budget_guard)
    workflow.add_conditional_edges("indexer",      _after_indexer)
    workflow.add_conditional_edges("smoke_test",   _after_smoke_test)
    workflow.add_conditional_edges("evaluator",    _after_evaluator)
    workflow.add_conditional_edges("recorder",     _after_recorder)
    workflow.add_conditional_edges("report_writer", lambda _: END)

    # Compile with checkpointer
    return workflow.compile(checkpointer=checkpointer)


# ─── Routing functions ────────────────────────────────────────────────────────

def _after_validator(state: WorkflowState) -> str:
    if state["status"] == "FAILED_VALIDATION":
        return "recorder"
    return "deduplicator"

def _after_deduplicator(state: WorkflowState) -> str:
    if state["status"] == "FAILED_DUPLICATE":
        return "recorder"
    return "budget_guard"

def _after_budget_guard(state: WorkflowState) -> str:
    if state["status"] == "BUDGET_EXCEEDED":
        return "report_writer"
    return "indexer"

def _after_indexer(state: WorkflowState) -> str:
    if state["status"] in ("FAILED_API_ERROR", "FAILED_TIMEOUT"):
        return "recorder"
    return "smoke_test"

def _after_smoke_test(state: WorkflowState) -> str:
    if state["status"] == "FAILED_SMOKE":
        return "recorder"
    return "evaluator"

def _after_evaluator(state: WorkflowState) -> str:
    if state["status"] in ("FAILED_TIMEOUT", "FAILED_API_ERROR"):
        return "recorder"
    return "acceptance"

def _after_recorder(state: WorkflowState) -> str:
    from src.orchestrator.config_loader import load_run_settings
    settings = load_run_settings()

    if state["status"] == "BUDGET_EXCEEDED":
        return "report_writer"

    max_experiments = state.get("max_experiments", settings["run"]["max_experiments"])
    if state.get("experiments_completed", 0) >= max_experiments:
        return "report_writer"

    if state.get("consecutive_failures", 0) >= settings["run"]["consecutive_failure_limit"]:
        return "report_writer"

    started = datetime.fromisoformat(state["run_started_at"])
    elapsed_hours = (datetime.now(timezone.utc) - started).total_seconds() / 3600
    max_hours = state.get("max_hours", settings["run"]["max_hours"])
    if elapsed_hours >= max_hours:
        return "report_writer"

    return "reflection"
