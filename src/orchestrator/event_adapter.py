"""Translates one raw LangGraph astream() tick (`{node_name: output_dict}`)
into normalized ExperimentEvents. Isolates the LangGraph stream shape from
everything downstream (TUI, legacy console log) so a LangGraph upgrade or
shape change only touches this file."""

from datetime import UTC, datetime

from src.core.events import ExperimentEvent
from src.orchestrator.overnight_display import NODE_META
from src.storage.cost_tracker import get_total


def adapt(event: dict, ctx: dict, settings) -> list[ExperimentEvent]:
    """Mutates ctx["exp_num"] on a new scientist tick, mirroring the counting
    behavior of overnight_display.log_event(). Callers share one `ctx` dict
    across an entire run."""
    events: list[ExperimentEvent] = []
    for node_name, output in event.items():
        if not isinstance(output, dict):
            continue

        if node_name == "scientist":
            ctx["exp_num"] = ctx.get("exp_num", 0) + 1

        _, _, description = NODE_META.get(node_name, ("--", "white", node_name))
        events.append(
            ExperimentEvent(
                experiment=ctx.get("exp_num", 0),
                node=node_name,
                status=output.get("status", "?"),
                timestamp=datetime.now(UTC),
                cost_total_usd=get_total(),
                cost_ceiling_usd=settings.run.cost_hard_ceiling_usd,
                message=description,
                hypothesis=output.get("hypothesis", ""),
                reasoning=output.get("scientist_reasoning", ""),
                config=output.get("proposed_config") or output.get("validated_config") or {},
                metrics=output.get("aggregated_metrics", {}),
                failure_reason=output.get("failure_reason", ""),
                raw_event={node_name: output},
            )
        )
    return events
