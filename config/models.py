from pydantic import BaseModel
from typing import Optional


class ModelConfig(BaseModel):
    model_id: str
    reasoning_effort: Optional[str] = None
    max_tokens: int = 4096
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    response_format: Optional[str] = None
    exclude_reasoning: Optional[bool] = None


class ModelRouting(BaseModel):
    scientist: ModelConfig
    coder: ModelConfig
    rag_generator_primary: ModelConfig
    rag_generator_fallback: ModelConfig
    ragas_judge: ModelConfig
    smoke_tester: ModelConfig
    report_writer: ModelConfig
