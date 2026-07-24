"""Translates one raw LangGraph astream() tick (`{node_name: output_dict}`)
into normalized ExperimentEvents. Isolates the LangGraph stream shape from
everything downstream (TUI, legacy console log) so a LangGraph upgrade or
shape change only touches this file."""

from datetime import UTC, datetime

from src.core.events import ExperimentEvent
from src.orchestrator.overnight_display import NODE_META


def adapt(event: dict, ctx: dict, settings, provider=None) -> list[ExperimentEvent]:
    """Mutates ctx["exp_num"] on a new scientist tick, mirroring the counting
    behavior of overnight_display.log_event(). Callers share one `ctx` dict
    across an entire run.

    Also caches the most recent evaluator tick's aggregated_metrics in ctx,
    tagged with the experiment it belongs to, and uses that cache to backfill
    a score onto the acceptance/recorder ticks -- neither node's own output
    carries aggregated_metrics, but DashboardState.apply() only reads scores
    off of those two nodes' events.

    `provider` supplies the live cost total via `provider.cost_tracker`, the
    same instance every real LLM call reports cost to (see
    provider_factory.py) -- not the deprecated src.storage.cost_tracker
    module singleton. `None` (e.g. in tests) reports 0.0."""
    events: list[ExperimentEvent] = []
    cost_total = provider.cost_tracker.get_total() if provider is not None else 0.0
    for node_name, output in event.items():
        if not isinstance(output, dict):
            continue

        if node_name == "scientist":
            ctx["exp_num"] = ctx.get("exp_num", 0) + 1

        exp_num = ctx.get("exp_num", 0)
        aggregated_metrics = output.get("aggregated_metrics", {})
        if aggregated_metrics:
            ctx["last_eval_metrics"] = aggregated_metrics
            ctx["last_eval_exp_num"] = exp_num

        config = output.get("proposed_config") or output.get("validated_config") or {}
        metrics = aggregated_metrics

        if node_name == "acceptance" and output.get("status") == "ACCEPTED":
            config = output.get("current_best_config") or config
            best_score = output.get("current_best_weighted_score")
            if best_score is not None:
                metrics = {"median_weighted_score": best_score}
            ctx["last_best_config"] = config
            ctx["last_best_config_exp_num"] = exp_num

        if node_name == "recorder":
            metrics = (
                ctx.get("last_eval_metrics", {}) if ctx.get("last_eval_exp_num") == exp_num else {}
            )
            # DashboardState.apply() updates best_config/best_score whenever
            # status == "ACCEPTED", regardless of node -- match the
            # acceptance tick's config here so that overwrite is a no-op
            # instead of clobbering best_config with {}.
            if (
                output.get("status") == "ACCEPTED"
                and ctx.get("last_best_config_exp_num") == exp_num
            ):
                config = ctx.get("last_best_config", {})

        _, _, description = NODE_META.get(node_name, ("--", "white", node_name))
        events.append(
            ExperimentEvent(
                experiment=exp_num,
                node=node_name,
                status=output.get("status", "?"),
                timestamp=datetime.now(UTC),
                cost_total_usd=cost_total,
                cost_ceiling_usd=settings.run.cost_hard_ceiling_usd,
                message=description,
                hypothesis=output.get("hypothesis", ""),
                reasoning=output.get("scientist_reasoning", ""),
                config=config,
                metrics=metrics,
                failure_reason=output.get("failure_reason", ""),
                raw_event={node_name: output},
            )
        )
    return events
