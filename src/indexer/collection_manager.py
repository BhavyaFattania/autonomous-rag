from pathlib import Path

from src.indexer.collection_names import (
    collection_name as _collection_name,
    bm25_cache_path, bm25_engine_path,
    get_chroma_client,
)
from src.indexer.collection_cache import (
    cache_is_complete, bm25_node_count,
    new_index_builds_allowed, expensive_parser_builds_allowed,
    effective_corpus_limit,
)
from src.indexer.index_builder import build_collection, build_bm25_cache_only
from src.models.rag_config import RAGConfig
from src.utils.logger import get_logger

log = get_logger("indexer")


def list_available_index_configs() -> list[dict]:
    configs = []
    prefix = "rag_openai_text_embedding_3_small_"
    for path in bm25_cache_path("").parent.glob(f"{prefix}*_nodes.pkl"):
        stem = path.name.removesuffix("_nodes.pkl")
        if not bm25_engine_path(stem).exists():
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
    name = _collection_name(config)
    try:
        collection = get_chroma_client().get_collection(name)
        return cache_is_complete(name, collection.count())
    except Exception:
        return False


async def get_or_build_collection(config: RAGConfig) -> str:
    name = _collection_name(config)
    chroma_client = get_chroma_client()
    bm25_cache = bm25_cache_path(name)
    engine_cache = bm25_engine_path(name)

    try:
        existing = chroma_client.get_collection(name)
        count = existing.count()
        if count > 0 and cache_is_complete(name, count):
            log.info("collection_cache_hit", collection=name,
                     vectors=count, bm25_cached=True)
            return name
        if count > 0 and (not bm25_cache.exists() or not engine_cache.exists()):
            if not new_index_builds_allowed():
                raise RuntimeError(
                    f"Collection {name} has Chroma vectors but no complete BM25 cache "
                    "and allow_new_index_builds=false"
                )
            log.warning("chroma_exists_but_bm25_missing", collection=name)
            build_bm25_cache_only(config, name)
            return name
        if count == 0:
            log.warning("collection_exists_but_empty", collection=name)
        elif count > 0:
            expected = bm25_node_count(name)
            log.warning(
                "collection_cache_incomplete",
                collection=name, vectors=count, expected_nodes=expected,
            )
        if not new_index_builds_allowed():
            raise RuntimeError(
                f"Collection {name} is incomplete "
                f"(vectors={count}, bm25_nodes={bm25_node_count(name)}) "
                "and allow_new_index_builds=false"
            )
        chroma_client.delete_collection(name)
    except RuntimeError:
        raise
    except Exception:
        pass

    if not new_index_builds_allowed():
        raise RuntimeError(
            f"Collection {name} is not cached and allow_new_index_builds=false"
        )
    if config.node_parser in {"semantic", "semantic_double"} and not expensive_parser_builds_allowed():
        raise RuntimeError(
            f"Collection {name} requires expensive parser '{config.node_parser}' "
            "and is not cached. Prebuild it or set allow_expensive_parser_builds=true."
        )

    log.info("building_collection", collection=name)
    await build_collection(config, name, chroma_client)
    return name


async def indexer_node(state) -> dict:
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
