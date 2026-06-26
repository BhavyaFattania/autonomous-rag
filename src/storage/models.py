"""Domain models for the experiment tracking database."""

from dataclasses import dataclass, field
from typing import Optional


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
    metrics_json: Optional[str] = None
    baseline_score: float = 0.0
    proposed_score: float = 0.0
    cost_usd: float = 0.0
    finished_at: Optional[str] = None
    duration_sec: Optional[float] = None
    experiment_id: Optional[int] = None


@dataclass
class ConfigHash:
    config_hash: str
    first_seen: str
    score: Optional[float] = None


@dataclass
class HistoricalRecord:
    score: Optional[float] = None
    metrics: dict = field(default_factory=dict)
    status: str = "unknown"
    hypothesis: str = ""


@dataclass
class Run:
    run_id: str
    started_at: str
    finished_at: Optional[str] = None
    total_cost: float = 0.0
    n_experiments: int = 0
    n_accepted: int = 0
    best_config: Optional[str] = None
    best_score: Optional[float] = None
    status: Optional[str] = None
