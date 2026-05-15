from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel
from src.models.rag_config import RAGConfig
from src.models.metrics import AggregatedMetrics

ExperimentStatus = Literal[
    "PENDING", "RUNNING", "ACCEPTED", "REJECTED",
    "FAILED_SMOKE", "FAILED_TIMEOUT", "FAILED_DUPLICATE",
    "FAILED_VALIDATION", "FAILED_API_ERROR", "INTERRUPTED"
]

class ExperimentRecord(BaseModel):
    experiment_id: int
    experiment_uuid: str           # uuid4 string
    config: RAGConfig
    config_hash: str               # SHA-256 of sorted JSON config
    hypothesis: str                # Scientist's rationale (max 500 chars)
    reflection_summary: Optional[str]
    metrics: Optional[AggregatedMetrics]
    baseline_weighted_score: float  # What we were beating
    status: ExperimentStatus
    failure_reason: Optional[str]
    cost_usd: float                 # API cost for this experiment
    started_at: datetime
    finished_at: Optional[datetime]
    duration_sec: Optional[float]
