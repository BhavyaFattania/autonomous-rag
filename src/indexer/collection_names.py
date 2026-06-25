from pathlib import Path

import chromadb
from src.indexer.parser_registry import parser_slug
from src.models.rag_config import RAGConfig

CHROMA_PATH = Path("data/chroma")
BM25_PATH = Path("data/bm25")

CHROMA_PATH.mkdir(parents=True, exist_ok=True)
BM25_PATH.mkdir(parents=True, exist_ok=True)


def collection_name(config: RAGConfig) -> str:
    slug = config.embedding_model.replace("/", "_").replace("-", "_").replace(".", "_")
    if config.node_parser == "sentence":
        return f"rag_{slug}_{config.chunk_size}_{config.chunk_overlap}"
    return f"rag_{slug}_{parser_slug(config)}"


def bm25_cache_path(name: str) -> Path:
    return BM25_PATH / f"{name}_nodes.pkl"


def bm25_engine_path(name: str) -> Path:
    return BM25_PATH / f"{name}_engine.pkl"


def get_chroma_client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(path=str(CHROMA_PATH))
