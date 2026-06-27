import json
from pathlib import Path

from src.utils.openrouter import call_openrouter


async def report_writer_node(state, settings) -> dict:
    report_path = Path("reports/overnight_run_report.md")
    report_path.parent.mkdir(exist_ok=True)

    if not settings.report.use_llm_report:
        report_path.write_text(_fallback_report(state, ""), encoding="utf-8")
        return {}

    prompt = _build_report_prompt(state)
    try:
        report = await call_openrouter(
            model_id="deepseek/deepseek-v4-pro",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=8192,
            task="report_writer",
            reasoning_effort="high",
            temperature=None,
        )
    except Exception as e:
        report = _fallback_report(state, str(e))

    report_path.write_text(report.strip() + "\n", encoding="utf-8")
    return {}


def _build_report_prompt(state) -> str:
    payload = {
        "run_id": state.get("run_id"),
        "total_cost_usd": state.get("total_cost_usd", 0.0),
        "experiments_completed": state.get("experiments_completed", 0),
        "experiments_accepted": state.get("experiments_accepted", 0),
        "experiments_competitive": state.get("experiments_competitive", 0),
        "experiments_repeated": state.get("experiments_repeated", 0),
        "current_best_config": state.get("current_best_config", {}),
        "current_best_weighted_score": state.get("current_best_weighted_score", 0.0),
        "current_best_metrics": state.get("current_best_metrics", {}),
        "successful_patterns": state.get("successful_patterns", []),
        "failed_patterns": state.get("failed_patterns", []),
        "reflection_summary": state.get("reflection_summary", ""),
    }
    return f"""
Write a concise markdown report for this autonomous RAG optimization run.
Include: final result, best config, metric summary, what improved, what failed,
and recommended next experiments. Be specific and do not overstate evidence.

Run data:
{json.dumps(payload, indent=2)}
""".strip()


def _fallback_report(state, error: str) -> str:
    return "\n".join([
        "# RAG Optimizer Overnight Run Report",
        "",
        f"Report LLM skipped or failed: {error or 'disabled in run_settings.yaml'}",
        f"Run ID: {state.get('run_id')}",
        f"Total Cost: ${state.get('total_cost_usd', 0.0):.4f}",
        f"Experiments Completed:   {state.get('experiments_completed', 0)}",
        f"Experiments Accepted:    {state.get('experiments_accepted', 0)}",
        f"Experiments Competitive: {state.get('experiments_competitive', 0)}",
        f"Experiments Repeated:    {state.get('experiments_repeated', 0)}",
        "",
        "## Best Configuration",
        "```json",
        json.dumps(state.get("current_best_config", {}), indent=2),
        "```",
        f"Best Score: {state.get('current_best_weighted_score', 0.0):.4f}",
    ])
