from pydantic import BaseModel, field_validator, model_validator

VALID_CHUNK_SIZES = [256, 512, 768, 1024, 1536, 2048]
VALID_CHUNK_OVERLAPS = [64, 128, 200, 256, 384]
VALID_NODE_PARSERS = [
    "sentence",
    "token",
    "semantic",
    "semantic_double",
    "sentence_window",
    "hierarchical",
]
VALID_RETRIEVERS = [
    "dense",
    "bm25",
    "weighted_hybrid_rrf",
    "query_fusion_simple",
    "query_fusion_rrf",
    "auto_merging",
    "sentence_window_dense",
    "recursive",
    "summary_embedding",
]
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
    node_parser: str = "sentence"
    retriever: str = "weighted_hybrid_rrf"
    window_size: int | None = None
    semantic_threshold: int | None = None
    semantic_buffer_size: int | None = None
    fusion_mode: str | None = None
    fusion_num_queries: int | None = None
    reranker: str | None
    reranker_top_n: int | None
    generator_model: str

    @field_validator("node_parser")
    @classmethod
    def validate_node_parser(cls, v):
        if v not in VALID_NODE_PARSERS:
            raise ValueError(f"node_parser must be one of {VALID_NODE_PARSERS}, got {v}")
        return v

    @field_validator("retriever")
    @classmethod
    def validate_retriever(cls, v):
        if v not in VALID_RETRIEVERS:
            raise ValueError(f"retriever must be one of {VALID_RETRIEVERS}, got {v}")
        return v

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

    @field_validator("window_size")
    @classmethod
    def validate_window_size(cls, v):
        if v is not None and not (1 <= v <= 8):
            raise ValueError(f"window_size must be between 1 and 8, got {v}")
        return v

    @field_validator("semantic_threshold")
    @classmethod
    def validate_semantic_threshold(cls, v):
        if v is not None and not (80 <= v <= 99):
            raise ValueError(f"semantic_threshold must be between 80 and 99, got {v}")
        return v

    @field_validator("semantic_buffer_size")
    @classmethod
    def validate_semantic_buffer_size(cls, v):
        if v is not None and not (1 <= v <= 3):
            raise ValueError(f"semantic_buffer_size must be between 1 and 3, got {v}")
        return v

    @field_validator("fusion_mode")
    @classmethod
    def validate_fusion_mode(cls, v):
        if v is not None and v not in {"simple", "reciprocal_rerank", "relative_score"}:
            raise ValueError("fusion_mode must be simple, reciprocal_rerank, or relative_score")
        return v

    @field_validator("fusion_num_queries")
    @classmethod
    def validate_fusion_num_queries(cls, v):
        if v is not None and not (1 <= v <= 4):
            raise ValueError(f"fusion_num_queries must be between 1 and 4, got {v}")
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
            raise ValueError("reranker_top_n must be between 2 and 10")
        if self.reranker_top_n is not None and self.reranker_top_n > self.top_k:
            raise ValueError(
                f"reranker_top_n ({self.reranker_top_n}) must be less than or equal to top_k ({self.top_k})"
            )
        if self.node_parser == "sentence_window" and self.window_size is None:
            self.window_size = 3
        if self.node_parser != "sentence_window" and self.window_size is not None:
            raise ValueError("window_size is only valid with node_parser='sentence_window'")
        if self.node_parser in {"semantic", "semantic_double"}:
            self.semantic_threshold = self.semantic_threshold or 95
            self.semantic_buffer_size = self.semantic_buffer_size or 1
        if self.node_parser not in {"semantic", "semantic_double"} and (
            self.semantic_threshold is not None or self.semantic_buffer_size is not None
        ):
            raise ValueError(
                "semantic_threshold and semantic_buffer_size are only valid with semantic parsers"
            )
        if self.retriever in {"auto_merging", "recursive"} and self.node_parser != "hierarchical":
            raise ValueError(f"retriever={self.retriever} requires node_parser='hierarchical'")
        if self.retriever == "sentence_window_dense" and self.node_parser != "sentence_window":
            raise ValueError(
                "retriever='sentence_window_dense' requires node_parser='sentence_window'"
            )
        if self.retriever in {"query_fusion_simple", "query_fusion_rrf"}:
            self.fusion_num_queries = self.fusion_num_queries or 1
            if self.fusion_mode is None:
                self.fusion_mode = (
                    "simple" if self.retriever == "query_fusion_simple" else "reciprocal_rerank"
                )
        elif self.fusion_mode is not None or self.fusion_num_queries is not None:
            raise ValueError("fusion fields are only valid with query_fusion retrievers")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                f"chunk_overlap ({self.chunk_overlap}) must be less than chunk_size ({self.chunk_size})"
            )
        return self
