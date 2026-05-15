import aiosqlite
from pathlib import Path
from src.storage.db import DB_PATH
from src.utils.openrouter import call_openrouter

async def report_writer_node(state) -> dict:
    # Summarize the run into a markdown report
    # We will just write a basic report here since it's the end of the graph
    
    report_path = Path("reports/overnight_run_report.md")
    report_path.parent.mkdir(exist_ok=True)
    
    lines = [
        "# RAG Optimizer Overnight Run Report",
        f"**Run ID:** {state.get('run_id')}",
        f"**Total Cost:** ${state.get('total_cost_usd', 0.0):.4f}",
        f"**Experiments Completed:** {state.get('experiments_completed', 0)}",
        f"**Experiments Accepted:** {state.get('experiments_accepted', 0)}",
        "",
        "## Best Configuration",
        "```json",
        f"{state.get('current_best_config', {})}",
        "```",
        f"**Best Score:** {state.get('current_best_weighted_score', 0.0):.4f}",
        "",
        "## Successful Patterns",
        *[f"- {p}" for p in state.get('successful_patterns', [])],
        "",
        "## Failed Patterns",
        *[f"- {p}" for p in state.get('failed_patterns', [])]
    ]
    
    report_path.write_text("\n".join(lines))
    return {}
