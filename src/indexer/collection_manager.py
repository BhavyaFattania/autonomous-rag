"""
collection_manager.py — ChromaDB + BM25 local indexer.

Each unique (embedding_model, chunk_size, chunk_overlap) combination gets:
  - A ChromaDB collection at data/chroma/
  - A BM25 index (pickled nodes) at data/bm25/<collection_name>.pkl

Both are built once and reused across experiments — no re-embedding on cache hits.
"""

import json
import pickle
import warnings
from pathlib import Path

from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

from src.indexer.parser_registry import build_node_parser, parser_slug
from src.models.rag_config import RAGConfig
from src.utils.logger import get_logger

log = get_logger("indexer")

CHROMA_PATH = Path("data/chroma")
BM25_PATH   = Path("data/bm25")

CHROMA_PATH.mkdir(parents=True, exist_ok=True)
BM25_PATH.mkdir(parents=True, exist_ok=True)

# Cap corpus size for fast experimentation.
# 15k paragraphs covers ~75% of HotpotQA gold paragraphs while cutting
# indexing time from ~5 min → ~45 sec per new config.
# Increase this if you want exhaustive retrieval at the cost of speed.
MAX_CORPUS_DOCS = 15_000


# ── helpers ───────────────────────────────────────────────────────────────────

def _collection_name(config: RAGConfig) -> str:
    slug = config.embedding_model.replace("/", "_").replace("-", "_").replace(".", "_")
    if config.node_parser == "sentence":
        return f"rag_{slug}_{config.chunk_size}_{config.chunk_overlap}"
    return f"rag_{slug}_{parser_slug(config)}"


def _bm25_cache_path(name: str) -> Path:
    return BM25_PATH / f"{name}_nodes.pkl"

def _bm25_engine_path(name: str) -> Path:
    return BM25_PATH / f"{name}_engine.pkl"


def _get_chroma_client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(path=str(CHROMA_PATH))


def _bm25_node_count(collection_name: str) -> int | None:
    cache_path = _bm25_cache_path(collection_name)
    if not cache_path.exists():
        return None
    with open(cache_path, "rb") as f:
        return len(pickle.load(f))


def _cache_is_complete(collection_name: str, vector_count: int) -> bool:
    node_count = _bm25_node_count(collection_name)
    if node_count is None or not _bm25_engine_path(collection_name).exists():
        return False
    return vector_count == node_count


def _new_index_builds_allowed() -> bool:
    from src.orchestrator.config_loader import load_run_settings

    settings = load_run_settings()
    return settings["evaluation"].get("allow_new_index_builds", True)


def _expensive_parser_builds_allowed() -> bool:
    from src.orchestrator.config_loader import load_run_settings

    settings = load_run_settings()
    return settings["evaluation"].get("allow_expensive_parser_builds", False)


def _effective_corpus_limit(config: RAGConfig) -> int:
    from src.orchestrator.config_loader import load_run_settings

    settings = load_run_settings()
    if config.node_parser in {"semantic", "semantic_double"}:
        return settings["evaluation"].get("max_docs_for_expensive_parsers", 1000)
    return MAX_CORPUS_DOCS


def list_available_index_configs() -> list[dict]:
    configs = []
    prefix = "rag_openai_text_embedding_3_small_"
    for path in BM25_PATH.glob(f"{prefix}*_nodes.pkl"):
        stem = path.name.removesuffix("_nodes.pkl")
        if not _bm25_engine_path(stem).exists():
            continue
        config_dict = _config_from_collection_stem(stem, prefix)
        if config_dict is None:
            continue
        if collection_is_cached(RAGConfig(
            top_k=5,
            hybrid_alpha=0.5,
            retriever="weighted_hybrid_rrf",
            reranker=None,
            reranker_top_n=None,
            generator_model="deepseek/deepseek-v4-flash",
            **config_dict,
        )):
            configs.append(config_dict)
    return sorted(
        configs,
        key=lambda item: (item["node_parser"], item["chunk_size"], item["chunk_overlap"]),
    )


def _config_from_collection_stem(stem: str, prefix: str) -> dict | None:
    parts = stem.removeprefix(prefix).split("_")
    if len(parts) == 2:
        try:
            chunk_size, chunk_overlap = int(parts[0]), int(parts[1])
        except ValueError:
            return None
        return {
            "embedding_model": "openai/text-embedding-3-small",
            "node_parser": "sentence",
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
        }
    if len(parts) >= 3:
        node_parser = parts[0].replace("-", "_")
        try:
            chunk_size, chunk_overlap = int(parts[1]), int(parts[2])
        except ValueError:
            return None
        config = {
            "embedding_model": "openai/text-embedding-3-small",
            "node_parser": node_parser,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
        }
        for part in parts[3:]:
            if part.startswith("w"):
                config["window_size"] = int(part[1:])
            elif part.startswith("t"):
                config["semantic_threshold"] = int(part[1:])
            elif part.startswith("b"):
                config["semantic_buffer_size"] = int(part[1:])
        return config
    return None


def collection_is_cached(config: RAGConfig) -> bool:
    collection_name = _collection_name(config)
    try:
        collection = _get_chroma_client().get_collection(collection_name)
        return _cache_is_complete(collection_name, collection.count())
    except Exception:
        return False


# ── public API ────────────────────────────────────────────────────────────────

async def get_or_build_collection(config: RAGConfig) -> str:
    """
    Returns the collection name for this config.
    Builds & persists ChromaDB + BM25 index if not already on disk.
    """
    collection_name = _collection_name(config)
    chroma_client   = _get_chroma_client()
    bm25_cache      = _bm25_cache_path(collection_name)
    engine_cache     = _bm25_engine_path(collection_name)

    # ── Cache hit: both stores exist and are populated ────────────────────────
    try:
        existing = chroma_client.get_collection(collection_name)
        count    = existing.count()
        if count > 0 and _cache_is_complete(collection_name, count):
            log.info("collection_cache_hit", collection=collection_name,
                     vectors=count, bm25_cached=True)
            return collection_name
        if count > 0 and (not bm25_cache.exists() or not engine_cache.exists()):
            if not _new_index_builds_allowed():
                raise RuntimeError(
                    f"Collection {collection_name} has Chroma vectors but no complete BM25 cache "
                    "and allow_new_index_builds=false"
                )
            log.warning("chroma_exists_but_bm25_missing",
                        collection=collection_name)
            _build_bm25_cache_only(config, collection_name)
            return collection_name
        if count == 0:
            log.warning("collection_exists_but_empty", collection=collection_name)
        elif count > 0:
            expected = _bm25_node_count(collection_name)
            log.warning(
                "collection_cache_incomplete",
                collection=collection_name,
                vectors=count,
                expected_nodes=expected,
            )
        if not _new_index_builds_allowed():
            raise RuntimeError(
                f"Collection {collection_name} is incomplete "
                f"(vectors={count}, bm25_nodes={_bm25_node_count(collection_name)}) "
                "and allow_new_index_builds=false"
            )
        chroma_client.delete_collection(collection_name)
    except RuntimeError:
        raise
    except Exception:
        pass  # Collection doesn't exist yet — build everything

    if not _new_index_builds_allowed():
        raise RuntimeError(
            f"Collection {collection_name} is not cached and allow_new_index_builds=false"
        )
    if config.node_parser in {"semantic", "semantic_double"} and not _expensive_parser_builds_allowed():
        raise RuntimeError(
            f"Collection {collection_name} requires expensive parser '{config.node_parser}' "
            "and is not cached. Prebuild it or set allow_expensive_parser_builds=true."
        )

    log.info("building_collection", collection=collection_name)
    await _build_collection(config, collection_name, chroma_client)
    return collection_name


def _build_bm25_cache_only(config: RAGConfig, collection_name: str):
    corpus_path = Path("data/corpus/hotpotqa_paragraphs.jsonl")
    embed_model = _build_embed_model(config)
    splitter = build_node_parser(config, embed_model=embed_model)
    docs = _load_corpus_as_documents(corpus_path, limit=_effective_corpus_limit(config))
    nodes = splitter.get_nodes_from_documents(docs, show_progress=False)

    bm25_cache = _bm25_cache_path(collection_name)
    engine_cache = _bm25_engine_path(collection_name)
    with open(bm25_cache, "wb") as f:
        pickle.dump(nodes, f)

    from llama_index.retrievers.bm25 import BM25Retriever
    bm25_retriever = BM25Retriever.from_defaults(nodes=nodes)
    bm25_retriever.bm25.corpus = bm25_retriever.corpus
    with open(engine_cache, "wb") as f:
        pickle.dump(bm25_retriever.bm25, f)

    log.info("bm25_state_cached", nodes=len(nodes), engine_path=str(engine_cache))


async def _build_collection(
    config: RAGConfig,
    collection_name: str,
    chroma_client: chromadb.PersistentClient,
):
    """Chunk corpus → embed into ChromaDB → pickle nodes for BM25."""
    corpus_path = Path("data/corpus/hotpotqa_paragraphs.jsonl")
    assert corpus_path.exists(), (
        f"Corpus not found at {corpus_path}. Run data/hotpotqa/setup_hotpotqa.py first."
    )

    # ── Embedding dimensions per model ────────────────────────────────────────
    EMBEDDING_DIMS = {
        "qwen/qwen3-embedding-8b":       4096,
        "qwen/qwen3-embedding-4b":       2560,
        "openai/text-embedding-3-small": 1536,
        "baai/bge-m3":                   1024,
    }
    if config.embedding_model not in EMBEDDING_DIMS:
        raise ValueError(f"Unknown embedding model: {config.embedding_model}")

    # ── Route through OpenRouter — accepts any model without enum validation ──
    from llama_index.core import Settings
    from llama_index.core.llms import MockLLM

    embed_model = _build_embed_model(config)
    # Set globally so LlamaIndex never tries to load default OpenAI models
    Settings.embed_model = embed_model
    Settings.llm = MockLLM()

    # ── Chunk documents ───────────────────────────────────────────────────────
    splitter = build_node_parser(config, embed_model=embed_model)
    docs  = _load_corpus_as_documents(corpus_path, limit=_effective_corpus_limit(config))
    nodes = splitter.get_nodes_from_documents(docs, show_progress=True)

    log.info(
        "nodes_parsed",
        count=len(nodes),
        collection=collection_name,
        node_parser=config.node_parser,
    )

    # ── Persist BM25 state (nodes + engine) ───────────────────────────────────
    bm25_cache = _bm25_cache_path(collection_name)
    engine_cache = _bm25_engine_path(collection_name)

    with open(bm25_cache, "wb") as f:
        pickle.dump(nodes, f)

    # Pre-tokenize and build BM25 engine once
    from llama_index.retrievers.bm25 import BM25Retriever
    bm25_retriever = BM25Retriever.from_defaults(nodes=nodes)
    bm25_retriever.bm25.corpus = bm25_retriever.corpus
    with open(engine_cache, "wb") as f:
        pickle.dump(bm25_retriever.bm25, f)

    log.info("bm25_state_cached", nodes=len(nodes), engine_path=str(engine_cache))

    # ── Build ChromaDB collection ─────────────────────────────────────────────
    chroma_collection = chroma_client.create_collection(collection_name)
    vector_store      = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context   = StorageContext.from_defaults(vector_store=vector_store)

    VectorStoreIndex(
        nodes,
        storage_context=storage_context,
        embed_model=embed_model,
        show_progress=True,
    )
    log.info("collection_built", collection=collection_name)


def load_bm25_nodes(collection_name: str) -> list:
    """Load the pre-chunked nodes for BM25 from disk cache."""
    cache_path = _bm25_cache_path(collection_name)
    if not cache_path.exists():
        raise FileNotFoundError(
            f"BM25 node cache not found at {cache_path}. "
            f"Delete the ChromaDB collection '{collection_name}' and re-index."
        )
    with open(cache_path, "rb") as f:
        nodes = pickle.load(f)
    return nodes


def load_bm25_engine(collection_name: str):
    """Load the pre-tokenized BM25 engine from disk cache."""
    engine_path = _bm25_engine_path(collection_name)
    if not engine_path.exists():
        # Fallback for old indices: trigger an error or rebuild (re-indexing is safer)
        raise FileNotFoundError(f"BM25 engine cache not found at {engine_path}")
    with open(engine_path, "rb") as f:
        return pickle.load(f)


def _load_corpus_as_documents(corpus_path: Path, limit: int = MAX_CORPUS_DOCS):
    """Load up to MAX_CORPUS_DOCS paragraphs from JSONL corpus."""
    from llama_index.core import Document
    docs = []
    for line in corpus_path.read_text(encoding="utf-8").strip().splitlines():
        item = json.loads(line)
        docs.append(Document(text=item["text"], metadata={"title": item["title"]}))
        if len(docs) >= limit:
            break
    log.info("corpus_loaded", docs=len(docs), capped=(len(docs) == limit), limit=limit)
    return docs


def _build_embed_model(config: RAGConfig):
    import os
    from src.utils.openrouter_embedding import OpenRouterEmbedding

    return OpenRouterEmbedding(
        model_name=config.embedding_model,
        api_key=os.environ.get("OPENROUTER_API_KEY"),
    )


# ── LangGraph node ────────────────────────────────────────────────────────────

async def indexer_node(state) -> dict:
    """Ensures the correct ChromaDB + BM25 collection exists for the validated config."""
    config = RAGConfig(**state["validated_config"])
    try:
        collection_name = await get_or_build_collection(config)
    except Exception as e:
        import traceback
        traceback.print_exc()
        log.error("indexer_failed", error=str(e))
        return {"status": "FAILED_API_ERROR", "failure_reason": f"Indexer failed: {e}"}
    return {
        "status": "RUNNING",
        "validated_config": {**state["validated_config"], "_collection_name": collection_name},
    }
