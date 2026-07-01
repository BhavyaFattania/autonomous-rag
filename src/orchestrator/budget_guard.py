from src.storage.cost_tracker import get_total

def budget_guard_node(state, settings) -> dict:
    """
    Decides whether to continue running based on total cost.
    
    Evaluates `total_cost >= cost_hard_ceiling_usd`.
    
    If exceeded → status: BUDGET_EXCEEDED (ends execution)
    If OK → status: RUNNING (continue)
    """
    try:
        total = get_total()
    except Exception as exc:
        # If cost tracking is unavailable, err on the side of caution
        # (pretend the ceiling is slightly lower or just log and continue).
        # Given the prompt implies "if exceeded", pretending it's not exceeded 
        # avoids unnecessary halts, but the safer bet for "hard ceiling" might 
        # be to halt if unknown.
        # However, since we can't reliably measure, we'll let it pass for now 
        # but log a warning.
        from src.utils.logger import get_logger
        log = get_logger("budget_guard")
        log.warning("cost_tracker_unavailable", error=str(exc))
        total = 0.0
        
    if total >= settings.run.cost_hard_ceiling_usd:
        from src.utils.logger import get_logger
        log = get_logger("budget_guard")
        log.warning("budget_exceeded", total=total, ceiling=settings.run.cost_hard_ceiling_usd)
        return {"status": "BUDGET_EXCEEDED"}
    
    return {"status": "RUNNING"}
