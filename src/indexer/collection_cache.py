import json
import pickle
from pathlib import Path

from llama_index.core import Document
from src.indexer.collection_names import bm25_cache_path, bm25_engine_path
from src.models.rag_config import RAGConfig
from src.utils.logger import get_logger

log = get_logger("indexer")

MAX_CORPUS_DOCS = 15_000


def bm25_node_count(collection_name: str) -> int | None:
    cache_path = bm25_cache_path(collection_name)
    if not cache_path.exists():
        return None
    with open(cache_path, "rb") as f:
        return len(pickle.load(f))


def cache_is_complete(collection_name: str, vector_count: int) -> bool:
    node_count = bm25_node_count(collection_name)
    if node_count is None or not bm25_engine_path(collection_name).exists():
        return False
    return vector_count == node_count


def new_index_builds_allowed() -> bool:
    from src.orchestrator.config_loader import load_run_settings

    settings = load_run_settings()
    return settings["evaluation"].get("allow_new_index_builds", True)


def expensive_parser_builds_allowed() -> bool:
    from src.orchestrator.config_loader import load_run_settings

    settings = load_run_settings()
    return settings["evaluation"].get("allow_expensive_parser_builds", False)


def effective_corpus_limit(config: RAGConfig) -> int:
    from src.orchestrator.config_loader import load_run_settings

    settings = load_run_settings()
    if config.node_parser in {"semantic", "semantic_double"}:
        return settings["evaluation"].get("max_docs_for_expensive_parsers", 1000)
    return MAX_CORPUS_DOCS


def load_corpus_as_documents(corpus_path: Path, limit: int = MAX_CORPUS_DOCS):
    docs = []
    for line in corpus_path.read_text(encoding="utf-8").strip().splitlines():
        item = json.loads(line)
        docs.append(Document(text=item["text"], metadata={"title": item["title"]}))
        if len(docs) >= limit:
            break
    log.info("corpus_loaded", docs=len(docs), capped=(len(docs) == limit), limit=limit)
    return docs


def build_embed_model(config: RAGConfig):
    import os
    from src.utils.openrouter_embedding import OpenRouterEmbedding

    return OpenRouterEmbedding(
        model_name=config.embedding_model,
        api_key=os.environ.get("OPENROUTER_API_KEY"),
    )
