"""
Configuration schemas for overnight experiment runs, evaluation, acceptance, and search space.

Hierarchically nested under Settings: run, evaluation, acceptance, explore_exploit, reflection, report, search_space.
"""

from pydantic import BaseModel, Field


class RunSettings(BaseModel):
    """Budget and concurrency limits: max_experiments, max_hours, cost ceiling, failure tolerance."""

    max_experiments: int = 40
    max_hours: int = 6
    cost_hard_ceiling_usd: float = 10.0
    cost_warning_threshold_usd: float = 7.0
    consecutive_failure_limit: int = 5
    random_seed: int = 42
    llm_provider: str = "openrouter"  # validated against src.core.provider_factory's registry


class EvalSettings(BaseModel):
    """Evaluation setup: question counts, RAGAS metrics, timeouts, smoke testing, audit frequency."""

    baseline_score_override: float | None = None
    n_eval_runs: int = 1
    n_questions: int = 10
    full_eval_n_questions: int = 50
    full_eval_every_n_experiments: int = 0
    final_best_eval_n_questions: int = 50
    run_final_best_eval: bool = True
    ragas_audit_every_n_experiments: int = 1
    ragas_audit_policy: str = "competitive"
    ragas_audit_score_tolerance: float = 0.02
    ragas_metrics: list[str] = [
        "faithfulness",
        "answer_relevancy",
        "context_precision",
        "context_recall",
        "context_utilization",
    ]
    smoke_test_n_questions: int = 2
    max_runtime_sec_per_eval: int = 300
    max_runtime_sec_per_ragas: int = 120
    ragas_timeout_backoff_factor: float = 2.0
    ragas_max_timeout_sec: int = 240
    ragas_timeout_retries: int = 1
    max_concurrent_questions: int = 8
    allow_new_index_builds: bool = False
    allow_expensive_parser_builds: bool = False
    max_docs_for_expensive_parsers: int = 1000
    allow_summary_embedding_retriever: bool = False


class AcceptanceSettings(BaseModel):
    """Acceptance criteria: score improvement thresholds, variance tolerance, regression limits."""

    accept_any_score_gain: bool = True
    min_weighted_score_improvement: float = 0.03
    competitive_score_tolerance: float = 0.02
    max_variance_between_runs: float = 0.035
    max_metric_regression: float = 0.02


class ExploreExploitSettings(BaseModel):
    """Exploration vs exploitation balance: probabilities, structured exploration count, reranker probing."""

    exploit_probability: float = 0.45
    explore_probability: float = 0.55
    structured_exploration_experiments: int = 12
    reranker_probe_every_n_experiments: int = 6


class ReflectionSettings(BaseModel):
    """Reflection frequency: brain update interval, history compaction, max token limits."""

    update_every_n_experiments: int = 3
    compact_every_n_experiments: int = 8
    max_history_tokens: int = 4000


class ReportSettings(BaseModel):
    """Report generation: LLM-based or template-based summary options."""

    use_llm_report: bool = False


class SearchSpaceSettings(BaseModel):
    """Search space constraints: allowed parsers, retrievers, chunk sizes, models, rerankers."""

    allowed_node_parsers: list[str] | None = None
    allowed_retrievers: list[str] | None = None
    allowed_chunk_sizes: list[int] | None = None
    allowed_chunk_overlaps: list[int] | None = None
    allowed_generator_models: list[str] | None = None
    allowed_rerankers: list[str | None] | None = None


class Settings(BaseModel):
    """Top-level settings container: aggregates all run, eval, acceptance, and exploration settings."""

    run: RunSettings = Field(default_factory=RunSettings)
    evaluation: EvalSettings = Field(default_factory=EvalSettings)
    acceptance: AcceptanceSettings = Field(default_factory=AcceptanceSettings)
    explore_exploit: ExploreExploitSettings = Field(default_factory=ExploreExploitSettings)
    reflection: ReflectionSettings = Field(default_factory=ReflectionSettings)
    report: ReportSettings = Field(default_factory=ReportSettings)
    search_space: SearchSpaceSettings = Field(default_factory=SearchSpaceSettings)
