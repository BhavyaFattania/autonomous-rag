from typing import Optional, Literal
from pydantic import BaseModel, field_validator, model_validator

VALID_CHUNK_SIZES = [256, 512, 768, 1024, 1536, 2048]
VALID_CHUNK_OVERLAPS = [64, 128, 200, 256, 384]
VALID_EMBEDDING_MODELS = [
    "openai/text-embedding-3-small",
]
VALID_RERANKERS = [None, "CohereRerank"]
VALID_GENERATOR_MODELS = [
    "deepseek/deepseek-v4-flash",
    "deepseek/deepseek-v4-flash:free",
    "deepseek/deepseek-v4-pro",
    "qwen/qwen3-30b-a3b",
]

class RAGConfig(BaseModel):
    chunk_size: int
    chunk_overlap: int
    top_k: int
    hybrid_alpha: float
    embedding_model: str
    reranker: Optional[str]
    reranker_top_n: Optional[int]
    generator_model: str

    @field_validator("chunk_size")
    @classmethod
    def validate_chunk_size(cls, v):
        if v not in VALID_CHUNK_SIZES:
            raise ValueError(f"chunk_size must be one of {VALID_CHUNK_SIZES}, got {v}")
        return v

    @field_validator("chunk_overlap")
    @classmethod
    def validate_chunk_overlap(cls, v):
        if v not in VALID_CHUNK_OVERLAPS:
            raise ValueError(f"chunk_overlap must be one of {VALID_CHUNK_OVERLAPS}, got {v}")
        return v

    @field_validator("top_k")
    @classmethod
    def validate_top_k(cls, v):
        if not (3 <= v <= 30):
            raise ValueError(f"top_k must be between 3 and 30, got {v}")
        return v

    @field_validator("hybrid_alpha")
    @classmethod
    def validate_hybrid_alpha(cls, v):
        # Round to 1 decimal place to prevent floating-point drift
        v = round(v, 1)
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"hybrid_alpha must be between 0.0 and 1.0, got {v}")
        return v

    @field_validator("embedding_model")
    @classmethod
    def validate_embedding_model(cls, v):
        if v not in VALID_EMBEDDING_MODELS:
            raise ValueError(f"embedding_model must be one of {VALID_EMBEDDING_MODELS}")
        return v

    @field_validator("reranker")
    @classmethod
    def validate_reranker(cls, v):
        if v not in VALID_RERANKERS:
            raise ValueError(f"reranker must be one of {VALID_RERANKERS}")
        return v

    @field_validator("generator_model")
    @classmethod
    def validate_generator_model(cls, v):
        if v not in VALID_GENERATOR_MODELS:
            raise ValueError(f"generator_model must be one of {VALID_GENERATOR_MODELS}")
        return v

    @model_validator(mode="after")
    def validate_reranker_top_n(self):
        if self.reranker is not None and self.reranker_top_n is None:
            raise ValueError("reranker_top_n must be set when reranker is not null")
        if self.reranker is None and self.reranker_top_n is not None:
            raise ValueError("reranker_top_n must be null when reranker is null")
        if self.reranker_top_n is not None and not (2 <= self.reranker_top_n <= 10):
            raise ValueError(f"reranker_top_n must be between 2 and 10")
        if self.reranker_top_n is not None and self.reranker_top_n >= self.top_k:
            raise ValueError(
                f"reranker_top_n ({self.reranker_top_n}) must be less than top_k ({self.top_k})"
            )
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                f"chunk_overlap ({self.chunk_overlap}) must be less than chunk_size ({self.chunk_size})"
            )
        return self
