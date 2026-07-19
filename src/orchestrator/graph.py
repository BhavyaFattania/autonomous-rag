from datetime import UTC, datetime
from functools import partial

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.core.provider import Provider
from src.orchestrator.state import WorkflowState


def build_graph(
    settings,
    provider: Provider,
    checkpointer: BaseCheckpointSaver | None = None,
    env=None,
    model_routing=None,
    event_bus=None,
) -> CompiledStateGraph:
    workflow = StateGraph(WorkflowState)

    from src.evaluator.eval_node import evaluator_node
    from src.evaluator.scorer import acceptance_node
    from src.indexer.collection_manager import indexer_node
    from src.orchestrator.budget_guard import budget_guard_node
    from src.orchestrator.validator import validator_node
    from src.rag_pipeline.smoke_tester import smoke_test_node
    from src.reporter.report_writer import report_writer_node
    from src.scientist.brain import scientist_node
    from src.scientist.deduplicator import deduplicator_node
    from src.scientist.reflection import reflection_node
    from src.storage.experiment_log import recorder_node

    workflow.add_node("scientist", partial(scientist_node, settings=settings, provider=provider))
    workflow.add_node("validator", partial(validator_node, settings=settings, env=env))
    workflow.add_node("deduplicator", deduplicator_node)
    workflow.add_node("budget_guard", partial(budget_guard_node, settings=settings))
    workflow.add_node(
        "indexer",
        partial(indexer_node, settings=settings, env=env, provider=provider, event_bus=event_bus),
    )
    workflow.add_node("smoke_test", partial(smoke_test_node, settings=settings))
    workflow.add_node(
        "evaluator",
        partial(evaluator_node, settings=settings, env=env, model_routing=model_routing),
    )
    workflow.add_node("acceptance", partial(acceptance_node, settings=settings))
    workflow.add_node("recorder", recorder_node)
    workflow.add_node("reflection", partial(reflection_node, settings=settings, provider=provider))
    workflow.add_node(
        "report_writer", partial(report_writer_node, settings=settings, provider=provider)
    )

    workflow.set_entry_point("scientist")

    workflow.add_edge("scientist", "validator")
    workflow.add_edge("acceptance", "recorder")
    workflow.add_edge("reflection", "scientist")

    workflow.add_conditional_edges("validator", _after_validator)
    workflow.add_conditional_edges("deduplicator", _after_deduplicator)
    workflow.add_conditional_edges("budget_guard", _after_budget_guard)
    workflow.add_conditional_edges("indexer", _after_indexer)
    workflow.add_conditional_edges("smoke_test", _after_smoke_test)
    workflow.add_conditional_edges("evaluator", _after_evaluator)
    workflow.add_conditional_edges("recorder", _after_recorder)
    workflow.add_conditional_edges("report_writer", lambda _: END)

    return workflow.compile(checkpointer=checkpointer)


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
    if state["status"] == "BUDGET_EXCEEDED":
        return "report_writer"

    max_experiments = state.get("max_experiments", 40)
    if state.get("experiments_completed", 0) >= max_experiments:
        return "report_writer"

    if state.get("consecutive_failures", 0) >= 5:
        return "report_writer"

    started = datetime.fromisoformat(state["run_started_at"])
    elapsed_hours = (datetime.now(UTC) - started).total_seconds() / 3600
    max_hours = state.get("max_hours", 6)
    if elapsed_hours >= max_hours:
        return "report_writer"

    return "reflection"
