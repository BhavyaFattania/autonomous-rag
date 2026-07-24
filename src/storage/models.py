"""Domain models for the experiment tracking database."""

from dataclasses import dataclass, field


@dataclass
class Experiment:
    """Single RAG configuration trial with metrics and cost tracking."""

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
    """Deduplication record mapping config hash to first seen timestamp and best score."""

    config_hash: str
    first_seen: str
    score: float | None = None


@dataclass
class HistoricalRecord:
    """Best result retrieved for a given config hash from experiment history."""

    score: float | None = None
    metrics: dict = field(default_factory=dict)
    status: str = "unknown"
    hypothesis: str = ""


@dataclass
class NodeEvent:
    """One durably-logged pipeline node tick, keyed by the experiment_uuid
    minted once per attempt by scientist_node -- the join key that lets a
    tick be looked up whether the experiment is still running or from a
    past, restarted run."""

    run_id: str
    experiment_uuid: str
    experiment_seq: int
    node: str
    status: str
    timestamp: str
    cost_total_usd: float = 0.0
    message: str = ""
    hypothesis: str = ""
    reasoning: str = ""
    config_json: str | None = None
    metrics_json: str | None = None
    failure_reason: str = ""
    progress_current: int | None = None
    progress_total: int | None = None
    raw_event_json: str | None = None
    id: int | None = None


@dataclass
class Run:
    """Single optimization run encompassing multiple experiment trials."""

    run_id: str
    started_at: str
    finished_at: str | None = None
    total_cost: float = 0.0
    n_experiments: int = 0
    n_accepted: int = 0
    best_config: str | None = None
    best_score: float | None = None
    status: str | None = None
