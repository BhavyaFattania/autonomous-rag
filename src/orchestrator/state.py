from typing import TypedDict, Optional

class WorkflowState(TypedDict):
    # Run-level identity
    run_id: str                         # UUID for this overnight run
    experiment_id: int                  # Auto-incrementing from SQLite
    experiment_uuid: str                # UUID for this specific experiment

    # Config tracking
    baseline_config: dict               # Serialized RAGConfig (dict form)
    current_best_config: dict           # The config achieving best score so far
    proposed_config: dict               # What the scientist just proposed (not yet validated)
    validated_config: dict              # After Pydantic validation passes

    # Scientist
    hypothesis: str
    scientist_reasoning: str
    reflection_summary: str             # Updated every 3 experiments

    # Evaluation
    eval_results: list[dict]            # List of SingleRunMetrics dicts (3 items after eval)
    aggregated_metrics: dict            # AggregatedMetrics dict
    current_best_weighted_score: float  # Score of current_best_config
    current_best_metrics: dict          # Median metric values for current_best_config
    proposed_weighted_score: float      # Score of proposed config

    # Status
    status: str                         # Mirrors ExperimentStatus
    failure_reason: str                 # Empty string if no failure

    # Accounting
    experiment_cost_usd: float          # Cost of THIS experiment
    total_cost_usd: float               # Cumulative cost of all experiments
    experiments_completed: int
    experiments_accepted: int
    consecutive_failures: int

    # History (for scientist context)
    successful_patterns: list[str]      # Short descriptions of accepted configs
    failed_patterns: list[str]          # Short descriptions of rejected configs

    # Timing
    run_started_at: str                 # ISO datetime string
    experiment_started_at: str          # ISO datetime string
    max_experiments: int                # CLI override for this run
    max_hours: float                    # CLI override for this run
