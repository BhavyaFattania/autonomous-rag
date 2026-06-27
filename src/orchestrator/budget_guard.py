from src.storage.cost_tracker import get_total
def budget_guard_node(state, settings) -> dict:
    total = get_total()
    if total >= settings.run.cost_hard_ceiling_usd:
        return {"status": "BUDGET_EXCEEDED"}
    return {"status": "RUNNING"}
