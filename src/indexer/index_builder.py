import pickle
from collections.abc import Callable
from pathlib import Path

import chromadb
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore

from src.core.model_catalog import EMBEDDING_CATALOG
from src.indexer.collection_cache import (
    build_embed_model,
    effective_corpus_limit,
    load_corpus_as_documents,
)
from src.indexer.collection_names import bm25_cache_path, bm25_engine_path
from src.indexer.parser_registry import build_node_parser
from src.models.rag_config import RAGConfig
from src.utils.logger import get_logger

log = get_logger("indexer")

CORPUS_PATH = Path("data/corpus/hotpotqa_paragraphs.jsonl")

_EMBED_BATCH_SIZE = 64


def _insert_nodes_with_progress(
    index: VectorStoreIndex,
    nodes: list,
    on_progress: Callable[[int, int], None] | None = None,
    batch_size: int = _EMBED_BATCH_SIZE,
) -> None:
    """Embeds and inserts `nodes` into `index` in batches, reporting real
    (done, total) counts after each batch — this is what makes the indexer's
    completion percentage genuine rather than a guessed/indeterminate bar."""
    total = len(nodes)
    if total == 0:
        return
    for start in range(0, total, batch_size):
        batch = nodes[start : start + batch_size]
        index.insert_nodes(batch)
        done = min(start + batch_size, total)
        log.debug("embedding_progress", done=done, total=total)
        if on_progress is not None:
            on_progress(done, total)


def build_bm25_cache_only(config: RAGConfig, collection_name: str, settings, env=None):
    assert (
        CORPUS_PATH.exists()
    ), f"Corpus not found at {CORPUS_PATH}. Run data/hotpotqa/setup_hotpotqa.py first."
    embed_model = build_embed_model(config, env)
    splitter = build_node_parser(config, embed_model=embed_model)
    docs = load_corpus_as_documents(CORPUS_PATH, limit=effective_corpus_limit(config, settings))
    nodes = splitter.get_nodes_from_documents(docs, show_progress=False)

    cache_path = bm25_cache_path(collection_name)
    engine_path = bm25_engine_path(collection_name)
    with open(cache_path, "wb") as f:
        pickle.dump(nodes, f)

    from llama_index.retrievers.bm25 import BM25Retriever

    bm25_retriever = BM25Retriever.from_defaults(nodes=nodes)
    bm25_retriever.bm25.corpus = bm25_retriever.corpus
    with open(engine_path, "wb") as f:
        pickle.dump(bm25_retriever.bm25, f)

    log.info("bm25_state_cached", nodes=len(nodes), engine_path=str(engine_path))


async def build_collection(
    config: RAGConfig,
    collection_name: str,
    chroma_client: chromadb.PersistentClient,
    settings,
    env=None,
    on_progress: Callable[[int, int], None] | None = None,
):
    assert (
        CORPUS_PATH.exists()
    ), f"Corpus not found at {CORPUS_PATH}. Run data/hotpotqa/setup_hotpotqa.py first."

    if config.embedding_model not in EMBEDDING_CATALOG:
        raise ValueError(f"Unknown embedding model: {config.embedding_model}")

    from llama_index.core import Settings
    from llama_index.core.llms import MockLLM

    embed_model = build_embed_model(config, env)
    Settings.embed_model = embed_model
    Settings.llm = MockLLM()

    splitter = build_node_parser(config, embed_model=embed_model)
    docs = load_corpus_as_documents(CORPUS_PATH, limit=effective_corpus_limit(config, settings))
    nodes = splitter.get_nodes_from_documents(docs, show_progress=True)

    log.info(
        "nodes_parsed",
        count=len(nodes),
        collection=collection_name,
        node_parser=config.node_parser,
    )

    cache_path = bm25_cache_path(collection_name)
    engine_path = bm25_engine_path(collection_name)

    with open(cache_path, "wb") as f:
        pickle.dump(nodes, f)

    from llama_index.retrievers.bm25 import BM25Retriever

    bm25_retriever = BM25Retriever.from_defaults(nodes=nodes)
    bm25_retriever.bm25.corpus = bm25_retriever.corpus
    with open(engine_path, "wb") as f:
        pickle.dump(bm25_retriever.bm25, f)

    log.info("bm25_state_cached", nodes=len(nodes), engine_path=str(engine_path))

    chroma_collection = chroma_client.create_collection(collection_name)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    index = VectorStoreIndex(
        nodes=[],
        storage_context=storage_context,
        embed_model=embed_model,
        show_progress=False,
    )
    _insert_nodes_with_progress(index, nodes, on_progress)
    log.info("collection_built", collection=collection_name)
