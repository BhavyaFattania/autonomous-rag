"""
ChromaDB dense + local BM25 retrieval.

hybrid_alpha controls weighted reciprocal-rank fusion:
  - 1.0 -> dense only
  - 0.0 -> BM25 only
  - 0.5 -> equal dense/BM25 blend
"""

import asyncio

import chromadb
from llama_index.core import StorageContext, SummaryIndex, VectorStoreIndex
from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.schema import NodeWithScore, QueryBundle
from llama_index.core.retrievers import (
    AutoMergingRetriever,
    QueryFusionRetriever,
    RecursiveRetriever,
    SummaryIndexEmbeddingRetriever,
)
from llama_index.core.retrievers.fusion_retriever import FUSION_MODES
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.vector_stores.chroma import ChromaVectorStore

from src.indexer.collection_manager import (
    _collection_name,
    CHROMA_PATH,
    load_bm25_nodes,
    load_bm25_engine,
)
from src.models.rag_config import RAGConfig
from src.utils.logger import get_logger

log = get_logger("retriever")


class WeightedHybridRetriever(BaseRetriever):
    def __init__(self, dense_retriever, bm25_retriever, alpha: float, top_k: int):
        super().__init__()
        self.dense_retriever = dense_retriever
        self.bm25_retriever = bm25_retriever
        self.alpha = alpha
        self.top_k = top_k

    def _fuse(
        self,
        dense_nodes: list[NodeWithScore],
        bm25_nodes: list[NodeWithScore],
    ) -> list[NodeWithScore]:
        fused: dict[str, dict] = {}

        def add(nodes: list[NodeWithScore], weight: float):
            for rank, node in enumerate(nodes, start=1):
                node_id = node.node.node_id
                item = fused.setdefault(node_id, {"node": node.node, "score": 0.0})
                item["score"] += weight / (60 + rank)

        add(dense_nodes, self.alpha)
        add(bm25_nodes, 1.0 - self.alpha)
        ranked = sorted(fused.values(), key=lambda item: item["score"], reverse=True)
        return [
            NodeWithScore(node=item["node"], score=item["score"])
            for item in ranked[: self.top_k]
        ]

    def _retrieve(self, query_bundle: QueryBundle) -> list[NodeWithScore]:
        dense_nodes = self.dense_retriever.retrieve(query_bundle)
        bm25_nodes = self.bm25_retriever.retrieve(query_bundle)
        return self._fuse(dense_nodes, bm25_nodes)

    async def _aretrieve(self, query_bundle: QueryBundle) -> list[NodeWithScore]:
        dense_nodes, bm25_nodes = await asyncio.gather(
            self.dense_retriever.aretrieve(query_bundle),
            self.bm25_retriever.aretrieve(query_bundle),
        )
        return self._fuse(dense_nodes, bm25_nodes)


class RerankingRetriever(BaseRetriever):
    def __init__(self, base_retriever, reranker):
        super().__init__()
        self.base_retriever = base_retriever
        self.reranker = reranker

    def _retrieve(self, query_bundle: QueryBundle) -> list[NodeWithScore]:
        nodes = self.base_retriever.retrieve(query_bundle)
        return self.reranker.postprocess_nodes(nodes, query_bundle=query_bundle)

    async def _aretrieve(self, query_bundle: QueryBundle) -> list[NodeWithScore]:
        nodes = await self.base_retriever.aretrieve(query_bundle)
        if hasattr(self.reranker, "apostprocess_nodes"):
            return await self.reranker.apostprocess_nodes(nodes, query_bundle=query_bundle)
        return self.reranker.postprocess_nodes(nodes, query_bundle=query_bundle)


async def build_retriever(config: RAGConfig, collection_name: str | None = None):
    collection_name = collection_name or _collection_name(config)

    dense_retriever, bm25_retriever, nodes, storage_context = _build_components(
        config,
        collection_name,
    )

    if config.retriever == "dense":
        log.info("retriever_mode", mode="dense", collection=collection_name)
        return _maybe_apply_reranker(dense_retriever, config)

    if config.retriever == "sentence_window_dense":
        log.info("retriever_mode", mode="sentence_window_dense", collection=collection_name)
        return _maybe_apply_reranker(dense_retriever, config)

    if config.retriever == "bm25":
        log.info("retriever_mode", mode="bm25", collection=collection_name)
        return _maybe_apply_reranker(bm25_retriever, config)

    if config.retriever == "query_fusion_simple":
        retriever = _build_query_fusion(
            config,
            dense_retriever,
            bm25_retriever,
            FUSION_MODES.SIMPLE,
        )
        log.info("retriever_mode", mode="query_fusion_simple", collection=collection_name)
        return _maybe_apply_reranker(retriever, config)

    if config.retriever == "query_fusion_rrf":
        retriever = _build_query_fusion(
            config,
            dense_retriever,
            bm25_retriever,
            FUSION_MODES.RECIPROCAL_RANK,
        )
        log.info("retriever_mode", mode="query_fusion_rrf", collection=collection_name)
        return _maybe_apply_reranker(retriever, config)

    if config.retriever == "auto_merging":
        retriever = AutoMergingRetriever(
            dense_retriever,
            storage_context=storage_context,
            simple_ratio_thresh=0.5,
        )
        log.info("retriever_mode", mode="auto_merging", collection=collection_name)
        return _maybe_apply_reranker(retriever, config)

    if config.retriever == "recursive":
        retriever = RecursiveRetriever(
            root_id="dense",
            retriever_dict={"dense": dense_retriever},
            node_dict={node.node_id: node for node in nodes},
        )
        log.info("retriever_mode", mode="recursive", collection=collection_name)
        return _maybe_apply_reranker(retriever, config)

    if config.retriever == "summary_embedding":
        from src.orchestrator.config_loader import load_run_settings

        settings = load_run_settings()
        if not settings["evaluation"].get("allow_summary_embedding_retriever", False):
            raise ValueError(
                "summary_embedding is disabled for live search because it builds "
                "a SummaryIndex over all nodes at retrieval time."
            )
        summary_index = SummaryIndex(nodes)
        retriever = SummaryIndexEmbeddingRetriever(
            summary_index,
            similarity_top_k=config.top_k,
        )
        log.info("retriever_mode", mode="summary_embedding", collection=collection_name)
        return _maybe_apply_reranker(retriever, config)

    if config.retriever != "weighted_hybrid_rrf":
        raise ValueError(f"Unknown retriever: {config.retriever}")

    if config.hybrid_alpha == 1.0:
        log.info("retriever_mode", mode="dense_via_weighted_hybrid", collection=collection_name)
        return _maybe_apply_reranker(dense_retriever, config)
    if config.hybrid_alpha == 0.0:
        log.info("retriever_mode", mode="bm25_via_weighted_hybrid", collection=collection_name)
        return _maybe_apply_reranker(bm25_retriever, config)

    log.info(
        "retriever_mode",
        mode="weighted_hybrid_rrf",
        collection=collection_name,
        alpha=config.hybrid_alpha,
        bm25_nodes=len(nodes),
    )
    retriever = WeightedHybridRetriever(
        dense_retriever=dense_retriever,
        bm25_retriever=bm25_retriever,
        alpha=config.hybrid_alpha,
        top_k=config.top_k,
    )
    return _maybe_apply_reranker(retriever, config)


def _build_components(config: RAGConfig, collection_name: str):
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    from src.utils.openrouter_embedding import OpenRouterEmbedding

    embed_model = OpenRouterEmbedding(model_name=config.embedding_model)
    chroma_collection = chroma_client.get_collection(collection_name)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)
    dense_retriever = index.as_retriever(similarity_top_k=config.top_k)

    nodes = load_bm25_nodes(collection_name)
    engine = load_bm25_engine(collection_name)
    if getattr(engine, "corpus", None) is None:
        from llama_index.core.vector_stores.utils import node_to_metadata_dict

        engine.corpus = [
            node_to_metadata_dict(node) | {"node_id": node.node_id}
            for node in nodes
        ]
    bm25_retriever = BM25Retriever(
        existing_bm25=engine,
        similarity_top_k=config.top_k,
    )
    docstore = SimpleDocumentStore()
    docstore.add_documents(nodes)
    storage_context = StorageContext.from_defaults(
        docstore=docstore,
        vector_store=vector_store,
    )
    return dense_retriever, bm25_retriever, nodes, storage_context


def _build_query_fusion(config, dense_retriever, bm25_retriever, mode):
    return QueryFusionRetriever(
        [dense_retriever, bm25_retriever],
        llm=_build_query_fusion_llm(config),
        mode=mode,
        similarity_top_k=config.top_k,
        num_queries=config.fusion_num_queries or 1,
        use_async=True,
        retriever_weights=[config.hybrid_alpha, 1.0 - config.hybrid_alpha],
    )


def _build_query_fusion_llm(config: RAGConfig):
    if (config.fusion_num_queries or 1) <= 1:
        from llama_index.core.llms import MockLLM

        return MockLLM()

    import os
    from llama_index.llms.openai import OpenAI
    from src.utils.openrouter import build_openrouter_headers

    return OpenAI(
        model=config.generator_model,
        api_key=os.environ["OPENROUTER_API_KEY"],
        api_base="https://openrouter.ai/api/v1",
        temperature=0.1,
        max_tokens=256,
        default_headers=build_openrouter_headers(),
    )


try:
    from src.rag_pipeline.openrouter_reranker import OpenRouterRerank
except ImportError:
    OpenRouterRerank = None


def _maybe_apply_reranker(retriever, config: RAGConfig):
    if config.reranker != "CohereRerank":
        return retriever

    if OpenRouterRerank is None:
        raise ValueError("OpenRouterRerank dependencies are not installed.")

    reranker = OpenRouterRerank(model="cohere/rerank-v3.5", top_n=config.reranker_top_n)
    log.info(
        "retriever_reranker_enabled_openrouter",
        model="cohere/rerank-v3.5",
        top_n=config.reranker_top_n,
    )
    return RerankingRetriever(retriever, reranker)
