from pydantic import BaseModel, Field
from typing import Optional


class RunSettings(BaseModel):
    max_experiments: int = 40
    max_hours: int = 6
    cost_hard_ceiling_usd: float = 10.0
    cost_warning_threshold_usd: float = 7.0
    consecutive_failure_limit: int = 5
    random_seed: int = 42


class EvalSettings(BaseModel):
    baseline_score_override: Optional[float] = None
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
    accept_any_score_gain: bool = True
    min_weighted_score_improvement: float = 0.03
    competitive_score_tolerance: float = 0.02
    max_variance_between_runs: float = 0.035
    max_metric_regression: float = 0.02


class ExploreExploitSettings(BaseModel):
    exploit_probability: float = 0.45
    explore_probability: float = 0.55
    structured_exploration_experiments: int = 12
    reranker_probe_every_n_experiments: int = 6


class ReflectionSettings(BaseModel):
    update_every_n_experiments: int = 3
    compact_every_n_experiments: int = 8
    max_history_tokens: int = 4000


class ReportSettings(BaseModel):
    use_llm_report: bool = False


class SearchSpaceSettings(BaseModel):
    allowed_node_parsers: Optional[list[str]] = None
    allowed_retrievers: Optional[list[str]] = None
    allowed_chunk_sizes: Optional[list[int]] = None
    allowed_chunk_overlaps: Optional[list[int]] = None
    allowed_generator_models: Optional[list[str]] = None
    allowed_rerankers: Optional[list[Optional[str]]] = None


class Settings(BaseModel):
    run: RunSettings = Field(default_factory=RunSettings)
    evaluation: EvalSettings = Field(default_factory=EvalSettings)
    acceptance: AcceptanceSettings = Field(default_factory=AcceptanceSettings)
    explore_exploit: ExploreExploitSettings = Field(default_factory=ExploreExploitSettings)
    reflection: ReflectionSettings = Field(default_factory=ReflectionSettings)
    report: ReportSettings = Field(default_factory=ReportSettings)
    search_space: SearchSpaceSettings = Field(default_factory=SearchSpaceSettings)
