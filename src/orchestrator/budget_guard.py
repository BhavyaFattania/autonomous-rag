from src.storage.cost_tracker import get_total
from config.settings import RunSettings
def budget_guard_node(state, settings=None) -> dict:
    total = get_total()
    if total >= RunSettings().cost_hard_ceiling_usd:
        return {"status": "BUDGET_EXCEEDED"}
    return {"status": "RUNNING"}
