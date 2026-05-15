async def reflection_node(state) -> dict:
    # A simple stub that updates reflection summary every N experiments
    from src.orchestrator.config_loader import load_run_settings
    settings = load_run_settings()
    n = settings["reflection"]["update_every_n_experiments"]
    
    completed = state.get("experiments_completed", 0)
    
    if completed > 0 and completed % n == 0:
        # In a real setup, we would call openrouter with past results to summarize
        new_summary = f"Reflection after {completed} experiments: continue exploring."
        return {"reflection_summary": new_summary}
        
    return {}
