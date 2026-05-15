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
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

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
    return f"rag_{slug}_{config.chunk_size}_{config.chunk_overlap}"


def _bm25_cache_path(name: str) -> Path:
    return BM25_PATH / f"{name}_nodes.pkl"

def _bm25_engine_path(name: str) -> Path:
    return BM25_PATH / f"{name}_engine.pkl"


def _get_chroma_client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(path=str(CHROMA_PATH))


# ── public API ────────────────────────────────────────────────────────────────

async def get_or_build_collection(config: RAGConfig) -> str:
    """
    Returns the collection name for this config.
    Builds & persists ChromaDB + BM25 index if not already on disk.
    """
    collection_name = _collection_name(config)
    chroma_client   = _get_chroma_client()
    bm25_cache      = _bm25_cache_path(collection_name)

    # ── Cache hit: both stores exist and are populated ────────────────────────
    try:
        existing = chroma_client.get_collection(collection_name)
        count    = existing.count()
        if count > 0 and bm25_cache.exists():
            log.info("collection_cache_hit", collection=collection_name,
                     vectors=count, bm25_cached=True)
            return collection_name
        if count > 0 and not bm25_cache.exists():
            log.warning("chroma_exists_but_bm25_missing",
                        collection=collection_name)
            # Fall through to rebuild both
        if count == 0:
            log.warning("collection_exists_but_empty", collection=collection_name)
        chroma_client.delete_collection(collection_name)
    except Exception:
        pass  # Collection doesn't exist yet — build everything

    log.info("building_collection", collection=collection_name)
    await _build_collection(config, collection_name, chroma_client)
    return collection_name


async def _build_collection(
    config: RAGConfig,
    collection_name: str,
    chroma_client: chromadb.PersistentClient,
):
    """Chunk corpus → embed into ChromaDB → pickle nodes for BM25."""
    import os
    from llama_index.embeddings.openai import OpenAIEmbedding
    from llama_index.embeddings.cohere import CohereEmbedding

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
    from src.utils.openrouter_embedding import OpenRouterEmbedding
    from llama_index.core import Settings
    from llama_index.core.llms import MockLLM

    embed_model = OpenRouterEmbedding(
        model_name=config.embedding_model,
        api_key=os.environ["OPENROUTER_API_KEY"],
    )
    # Set globally so LlamaIndex never tries to load default OpenAI models
    Settings.embed_model = embed_model
    Settings.llm = MockLLM()

    # ── Chunk documents ───────────────────────────────────────────────────────
    splitter = SentenceSplitter(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
    )
    docs  = _load_corpus_as_documents(corpus_path)
    nodes = splitter.get_nodes_from_documents(docs, show_progress=True)

    log.info("nodes_parsed", count=len(nodes), collection=collection_name)

    # ── Persist BM25 state (nodes + engine) ───────────────────────────────────
    bm25_cache = _bm25_cache_path(collection_name)
    engine_cache = _bm25_engine_path(collection_name)
    
    with open(bm25_cache, "wb") as f:
        pickle.dump(nodes, f)
    
    # Pre-tokenize and build BM25 engine once
    from llama_index.retrievers.bm25 import BM25Retriever
    bm25_retriever = BM25Retriever.from_defaults(nodes=nodes)
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


def _load_corpus_as_documents(corpus_path: Path):
    """Load up to MAX_CORPUS_DOCS paragraphs from JSONL corpus."""
    from llama_index.core import Document
    docs = []
    for line in corpus_path.read_text(encoding="utf-8").strip().splitlines():
        item = json.loads(line)
        docs.append(Document(text=item["text"], metadata={"title": item["title"]}))
        if len(docs) >= MAX_CORPUS_DOCS:
            break
    log.info("corpus_loaded", docs=len(docs), capped=(len(docs) == MAX_CORPUS_DOCS))
    return docs


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
