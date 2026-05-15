"""
retriever.py — ChromaDB dense + local BM25 hybrid retriever.

BM25 uses the pre-chunked nodes pickled during indexing (data/bm25/<name>.pkl),
so it operates on the EXACT same chunks as the vector store — no re-reading the
raw corpus and no mismatch between dense and sparse token boundaries.

hybrid_alpha controls the blend:
  - 1.0  → dense only (pure vector similarity)
  - 0.0  → BM25 only (pure keyword)
  - 0.5  → equal weight via Reciprocal Rank Fusion
"""

import chromadb
from llama_index.core import VectorStoreIndex
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.vector_stores.chroma import ChromaVectorStore

from src.models.rag_config import RAGConfig
from src.indexer.collection_manager import (
    _collection_name,
    CHROMA_PATH,
    load_bm25_nodes,
    load_bm25_engine,
)
from src.utils.logger import get_logger

log = get_logger("retriever")


async def build_retriever(config: RAGConfig):
    """
    Builds a local retriever for the given RAGConfig.

    Returns:
      - Dense-only VectorIndexRetriever if hybrid_alpha == 1.0
      - QueryFusionRetriever (dense + BM25 via RRF) otherwise
    """
    collection_name = _collection_name(config)

    # ── Dense retriever from ChromaDB ─────────────────────────────────────────
    chroma_client     = chromadb.PersistentClient(path=str(CHROMA_PATH))
    from src.utils.openrouter_embedding import OpenRouterEmbedding
    embed_model = OpenRouterEmbedding(model_name=config.embedding_model)

    chroma_collection = chroma_client.get_collection(collection_name)
    vector_store      = ChromaVectorStore(chroma_collection=chroma_collection)
    index             = VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)
    dense_retriever   = index.as_retriever(similarity_top_k=config.top_k)

    if config.hybrid_alpha == 1.0:
        log.info("retriever_mode", mode="dense_only", collection=collection_name)
        return dense_retriever

    # ── BM25 retriever from pickled nodes + engine ───────────────────────────
    nodes = load_bm25_nodes(collection_name)   # same chunks as the vector store
    engine = load_bm25_engine(collection_name) # pre-calculated frequency table
    
    # Use direct constructor instead of from_defaults when providing the engine
    bm25_retriever = BM25Retriever(
        nodes=nodes,
        bm25=engine,
        similarity_top_k=config.top_k,
    )

    log.info(
        "retriever_mode", mode="hybrid_rrf",
        collection=collection_name,
        alpha=config.hybrid_alpha,
        bm25_nodes=len(nodes),
    )

    # ── Reciprocal Rank Fusion fusion ────────────────────────────────────────
    # QueryFusionRetriever with num_queries=1 performs RRF without generating
    # extra query variants (no extra LLM calls). We pass a MockLLM to satisfy
    # LlamaIndex's internal check for an LLM provider.
    from llama_index.core.llms import MockLLM
    retriever = QueryFusionRetriever(
        [dense_retriever, bm25_retriever],
        similarity_top_k=config.top_k,
        num_queries=1,        # no LLM-generated query expansion
        use_async=True,
        mode="reciprocal_rerank",
        llm=MockLLM(),
    )
    return retriever
