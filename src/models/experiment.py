"""Experiment tracking and results models for RAG configuration experiments."""
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
    """Complete record of a single RAG configuration experiment run."""
    experiment_id: int
    experiment_uuid: str  # UUID4 unique identifier
    config: RAGConfig
    config_hash: str  # SHA-256 of sorted JSON config for deduplication
    hypothesis: str  # Scientist's hypothesis/rationale (max 500 chars)
    reflection_summary: str | None
    metrics: AggregatedMetrics | None
    baseline_weighted_score: float  # Baseline score this experiment aimed to beat
    status: ExperimentStatus
    failure_reason: str | None
    cost_usd: float  # Total API cost for this experiment run
    started_at: datetime
    finished_at: datetime | None
    duration_sec: float | None
