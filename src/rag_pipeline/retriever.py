"""
ChromaDB dense + local BM25 retrieval.

hybrid_alpha controls weighted reciprocal-rank fusion:
  - 1.0 -> dense only
  - 0.0 -> BM25 only
  - 0.5 -> equal dense/BM25 blend
"""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import chromadb
from llama_index.core import StorageContext, SummaryIndex, VectorStoreIndex
from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.retrievers import (
    AutoMergingRetriever,
    QueryFusionRetriever,
    RecursiveRetriever,
    SummaryIndexEmbeddingRetriever,
)
from llama_index.core.retrievers.fusion_retriever import FUSION_MODES
from llama_index.core.schema import NodeWithScore, QueryBundle
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.vector_stores.chroma import ChromaVectorStore

from src.core.provider_factory import required_env_var
from src.indexer.collection_cache import load_bm25_engine, load_bm25_nodes
from src.indexer.collection_names import CHROMA_PATH
from src.indexer.collection_names import collection_name as _idx_collection_name
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
            NodeWithScore(node=item["node"], score=item["score"]) for item in ranked[: self.top_k]
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


@dataclass
class _RetrieverContext:
    """Bundle of everything a per-mode builder might need. Individual builders
    use whichever fields their mode requires and ignore the rest -- lets every
    entry in _RETRIEVER_BUILDERS share one call signature despite the modes
    needing heterogeneous inputs (dense-only, nodes+storage_context, etc.)."""

    config: RAGConfig
    settings: Any
    collection_name: str
    dense_retriever: Any
    bm25_retriever: Any
    nodes: list
    storage_context: StorageContext
    env: dict | None


def _build_dense_mode(ctx: _RetrieverContext):
    log.info("retriever_mode", mode="dense", collection=ctx.collection_name)
    return ctx.dense_retriever


def _build_sentence_window_dense_mode(ctx: _RetrieverContext):
    log.info("retriever_mode", mode="sentence_window_dense", collection=ctx.collection_name)
    return ctx.dense_retriever


def _build_bm25_mode(ctx: _RetrieverContext):
    log.info("retriever_mode", mode="bm25", collection=ctx.collection_name)
    return ctx.bm25_retriever


def _build_query_fusion_simple_mode(ctx: _RetrieverContext):
    retriever = _build_query_fusion(
        ctx.config,
        ctx.dense_retriever,
        ctx.bm25_retriever,
        FUSION_MODES.SIMPLE,
        ctx.settings,
        ctx.env,
    )
    log.info("retriever_mode", mode="query_fusion_simple", collection=ctx.collection_name)
    return retriever


def _build_query_fusion_rrf_mode(ctx: _RetrieverContext):
    retriever = _build_query_fusion(
        ctx.config,
        ctx.dense_retriever,
        ctx.bm25_retriever,
        FUSION_MODES.RECIPROCAL_RANK,
        ctx.settings,
        ctx.env,
    )
    log.info("retriever_mode", mode="query_fusion_rrf", collection=ctx.collection_name)
    return retriever


def _build_auto_merging_mode(ctx: _RetrieverContext):
    retriever = AutoMergingRetriever(
        ctx.dense_retriever,
        storage_context=ctx.storage_context,
        simple_ratio_thresh=0.5,
    )
    log.info("retriever_mode", mode="auto_merging", collection=ctx.collection_name)
    return retriever


def _build_recursive_mode(ctx: _RetrieverContext):
    retriever = RecursiveRetriever(
        root_id="dense",
        retriever_dict={"dense": ctx.dense_retriever},
        node_dict={node.node_id: node for node in ctx.nodes},
    )
    log.info("retriever_mode", mode="recursive", collection=ctx.collection_name)
    return retriever


def _build_summary_embedding_mode(ctx: _RetrieverContext):
    if not ctx.settings.evaluation.allow_summary_embedding_retriever:
        raise ValueError(
            "summary_embedding is disabled for live search because it builds "
            "a SummaryIndex over all nodes at retrieval time."
        )
    summary_index = SummaryIndex(ctx.nodes)
    retriever = SummaryIndexEmbeddingRetriever(
        summary_index,
        similarity_top_k=ctx.config.top_k,
    )
    log.info("retriever_mode", mode="summary_embedding", collection=ctx.collection_name)
    return retriever


def _build_weighted_hybrid_rrf_mode(ctx: _RetrieverContext):
    config = ctx.config
    if config.hybrid_alpha == 1.0:
        log.info("retriever_mode", mode="dense_via_weighted_hybrid", collection=ctx.collection_name)
        return ctx.dense_retriever
    if config.hybrid_alpha == 0.0:
        log.info("retriever_mode", mode="bm25_via_weighted_hybrid", collection=ctx.collection_name)
        return ctx.bm25_retriever

    log.info(
        "retriever_mode",
        mode="weighted_hybrid_rrf",
        collection=ctx.collection_name,
        alpha=config.hybrid_alpha,
        bm25_nodes=len(ctx.nodes),
    )
    return WeightedHybridRetriever(
        dense_retriever=ctx.dense_retriever,
        bm25_retriever=ctx.bm25_retriever,
        alpha=config.hybrid_alpha,
        top_k=config.top_k,
    )


_RETRIEVER_BUILDERS: dict[str, Callable[[_RetrieverContext], BaseRetriever]] = {
    "dense": _build_dense_mode,
    "sentence_window_dense": _build_sentence_window_dense_mode,
    "bm25": _build_bm25_mode,
    "query_fusion_simple": _build_query_fusion_simple_mode,
    "query_fusion_rrf": _build_query_fusion_rrf_mode,
    "auto_merging": _build_auto_merging_mode,
    "recursive": _build_recursive_mode,
    "summary_embedding": _build_summary_embedding_mode,
    "weighted_hybrid_rrf": _build_weighted_hybrid_rrf_mode,
}


async def build_retriever(
    config: RAGConfig, settings, collection_name: str | None = None, env=None
):
    collection_name = collection_name or _idx_collection_name(config)

    dense_retriever, bm25_retriever, nodes, storage_context = _build_components(
        config,
        collection_name,
        env,
    )

    try:
        builder = _RETRIEVER_BUILDERS[config.retriever]
    except KeyError:
        raise ValueError(f"Unknown retriever: {config.retriever}") from None

    ctx = _RetrieverContext(
        config=config,
        settings=settings,
        collection_name=collection_name,
        dense_retriever=dense_retriever,
        bm25_retriever=bm25_retriever,
        nodes=nodes,
        storage_context=storage_context,
        env=env,
    )
    retriever = builder(ctx)
    return _maybe_apply_reranker(retriever, config, env)


def _build_components(config: RAGConfig, collection_name: str, env=None):
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    from src.core.model_catalog import build_embedding_model

    embed_model = build_embedding_model(config.embedding_model, env)
    chroma_collection = chroma_client.get_collection(collection_name)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)
    dense_retriever = index.as_retriever(similarity_top_k=config.top_k)

    nodes = load_bm25_nodes(collection_name)
    engine = load_bm25_engine(collection_name)
    if getattr(engine, "corpus", None) is None:
        from llama_index.core.vector_stores.utils import node_to_metadata_dict

        engine.corpus = [node_to_metadata_dict(node) | {"node_id": node.node_id} for node in nodes]
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


def _build_query_fusion(config, dense_retriever, bm25_retriever, mode, settings, env=None):
    return QueryFusionRetriever(
        [dense_retriever, bm25_retriever],
        llm=_build_query_fusion_llm(config, settings, env),
        mode=mode,
        similarity_top_k=config.top_k,
        num_queries=config.fusion_num_queries or 1,
        use_async=True,
        retriever_weights=[config.hybrid_alpha, 1.0 - config.hybrid_alpha],
    )


# api_base per provider for the query-fusion sub-query-generation LLM. `None`
# means "use the llama-index OpenAI() class's own default (OpenAI's API)".
# Mirrors provider_factory.py's _PROVIDER_REQUIRED_ENV_VAR registry shape so a
# future provider is one entry here, not a new hardcoded branch.
_QUERY_FUSION_BASE_URLS: dict[str, str | None] = {
    "openrouter": "https://openrouter.ai/api/v1",
    "openai": None,
}


def _build_query_fusion_headers(provider_name: str, api_key: str | None) -> dict:
    """OpenRouter needs branding headers; other providers need none."""
    if provider_name == "openrouter":
        from src.utils.openrouter import build_openrouter_headers

        return build_openrouter_headers(api_key)
    return {}


def _build_query_fusion_llm(config: RAGConfig, settings, env=None):
    if (config.fusion_num_queries or 1) <= 1:
        from llama_index.core.llms import MockLLM

        return MockLLM()

    from llama_index.llms.openai import OpenAI

    provider_name = settings.run.llm_provider
    api_key = (env or {}).get(required_env_var(provider_name))
    base_url = _QUERY_FUSION_BASE_URLS.get(provider_name)

    return OpenAI(
        model=config.generator_model,
        api_key=api_key,
        api_base=base_url,
        temperature=0.1,
        max_tokens=256,
        default_headers=_build_query_fusion_headers(provider_name, api_key),
    )


def _maybe_apply_reranker(retriever, config: RAGConfig, env=None):
    if config.reranker is None:
        return retriever

    from src.core.model_catalog import build_reranker

    assert config.reranker_top_n is not None  # guaranteed by RAGConfig's validator
    reranker = build_reranker(config.reranker, config.reranker_top_n, env)
    log.info(
        "retriever_reranker_enabled",
        reranker=config.reranker,
        top_n=config.reranker_top_n,
    )
    return RerankingRetriever(retriever, reranker)
