from pydantic import BaseModel


class ModelConfig(BaseModel):
    model_id: str
    reasoning_effort: str | None = None
    max_tokens: int = 4096
    temperature: float | None = None
    top_p: float | None = None
    response_format: str | None = None
    exclude_reasoning: bool | None = None


class ModelRouting(BaseModel):
    scientist: ModelConfig
    coder: ModelConfig
    rag_generator_primary: ModelConfig
    rag_generator_fallback: ModelConfig
    ragas_judge: ModelConfig
    smoke_tester: ModelConfig
    report_writer: ModelConfig
