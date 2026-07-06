"""Domain models for the experiment tracking database."""

from dataclasses import dataclass, field


@dataclass
class Experiment:
    experiment_uuid: str
    run_id: str
    config_hash: str
    config_json: str
    status: str
    started_at: str
    hypothesis: str = ""
    failure_reason: str = ""
    metrics_json: str | None = None
    baseline_score: float = 0.0
    proposed_score: float = 0.0
    cost_usd: float = 0.0
    finished_at: str | None = None
    duration_sec: float | None = None
    experiment_id: int | None = None


@dataclass
class ConfigHash:
    config_hash: str
    first_seen: str
    score: float | None = None


@dataclass
class HistoricalRecord:
    score: float | None = None
    metrics: dict = field(default_factory=dict)
    status: str = "unknown"
    hypothesis: str = ""


@dataclass
class Run:
    run_id: str
    started_at: str
    finished_at: str | None = None
    total_cost: float = 0.0
    n_experiments: int = 0
    n_accepted: int = 0
    best_config: str | None = None
    best_score: float | None = None
    status: str | None = None
