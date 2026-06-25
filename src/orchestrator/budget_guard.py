from src.storage.cost_tracker import get_total
from src.utils.config_loader import load_run_settings

def budget_guard_node(state) -> dict:
    settings = load_run_settings()
    total = get_total()
    if total >= settings["run"]["cost_hard_ceiling_usd"]:
        return {"status": "BUDGET_EXCEEDED"}
    return {"status": "RUNNING"}
