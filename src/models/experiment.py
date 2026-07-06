from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from src.models.metrics import AggregatedMetrics
from src.models.rag_config import RAGConfig

ExperimentStatus = Literal[
    "PENDING",
    "RUNNING",
    "ACCEPTED",
    "REJECTED",
    "FAILED_SMOKE",
    "FAILED_TIMEOUT",
    "FAILED_DUPLICATE",
    "FAILED_VALIDATION",
    "FAILED_API_ERROR",
    "INTERRUPTED",
]


class ExperimentRecord(BaseModel):
    experiment_id: int
    experiment_uuid: str  # uuid4 string
    config: RAGConfig
    config_hash: str  # SHA-256 of sorted JSON config
    hypothesis: str  # Scientist's rationale (max 500 chars)
    reflection_summary: str | None
    metrics: AggregatedMetrics | None
    baseline_weighted_score: float  # What we were beating
    status: ExperimentStatus
    failure_reason: str | None
    cost_usd: float  # API cost for this experiment
    started_at: datetime
    finished_at: datetime | None
    duration_sec: float | None
