"""
Model configuration schemas for LLM providers and agent role assignments.

Defines ModelConfig (per-model params) and ModelRouting (agent-to-model mapping).
"""

from pydantic import BaseModel


class ModelConfig(BaseModel):
    """LLM configuration: model_id, reasoning effort, tokens, temperature, format options."""

    model_id: str
    reasoning_effort: str | None = None
    task: str | None = "LLM"
    max_tokens: int = 4096
    temperature: float | None = None
    top_p: float | None = None
    response_format: str | None = None
    reasoning: bool | None = None
    base_url: str | None = None


class ModelRouting(BaseModel):
    """Agent role-to-model assignment: scientist, coder, generators, judge, tester, reporter."""

    scientist: ModelConfig
    coder: ModelConfig
    rag_generator_primary: ModelConfig
    rag_generator_fallback: ModelConfig
    ragas_judge: ModelConfig
    smoke_tester: ModelConfig
    report_writer: ModelConfig
    ragas_embedding_model: ModelConfig
