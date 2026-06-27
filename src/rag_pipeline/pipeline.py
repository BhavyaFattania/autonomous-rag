import asyncio
import json
import time
from pathlib import Path

from src.utils.langfuse_compat import observe

from src.models.rag_config import RAGConfig
from src.rag_pipeline.retriever import build_retriever
from src.rag_pipeline.generator import generate_answer
from src.indexer.collection_manager import get_or_build_collection
from src.utils.hashing import get_config_hash
from src.utils.logger import get_logger
from config.settings import EvalSettings
log = get_logger("pipeline")

RETRIEVAL_CACHE_PATH = Path("data/retrieval_cache")
RETRIEVAL_CACHE_PATH.mkdir(parents=True, exist_ok=True)

@observe(name="run_pipeline")
async def run_pipeline(
    config: RAGConfig,
    questions: list[str],
    collection_name: str | None = None,
    settings=None,
    env=None,
) -> tuple[list[str], list[list[str]], float]:
    """
    Run RAG pipeline for a list of questions.
    Returns (answers, contexts, cost_usd)
    """
    collection_name = collection_name or await get_or_build_collection(config, env=env)
    max_concurrency = EvalSettings().max_concurrent_questions

    cost = 0.0 # Handled globally by openrouter.py, but we could return 0.0 or track delta

    from src.storage.cost_tracker import get_total
    start_cost = get_total()

    started = time.perf_counter()
    contexts = await _get_or_build_contexts(
        config=config,
        questions=questions,
        collection_name=collection_name,
        max_concurrency=max_concurrency,
        settings=settings,
        env=env,
    )
    log.info(
        "pipeline_contexts_ready",
        questions=len(questions),
        elapsed_sec=round(time.perf_counter() - started, 2),
    )

    semaphore = asyncio.Semaphore(max_concurrency)

    async def answer_one(question: str, context: list[str]) -> str:
        async with semaphore:
            return await generate_answer(
                question,
                context,
                model_id=config.generator_model,
            )

    started = time.perf_counter()
    log.info("pipeline_generation_start", questions=len(questions), concurrency=max_concurrency)
    answers = await asyncio.gather(
        *[answer_one(question, context) for question, context in zip(questions, contexts)]
    )
    log.info(
        "pipeline_generation_complete",
        questions=len(answers),
        elapsed_sec=round(time.perf_counter() - started, 2),
    )

    end_cost = get_total()
    cost = end_cost - start_cost

    return answers, contexts, cost


async def retrieve_contexts(
    config: RAGConfig,
    questions: list[str],
    collection_name: str | None = None,
    env=None,
) -> tuple[list[list[str]], float]:
    results, cost = await retrieve_results(config, questions, collection_name=collection_name, env=env)
    return _results_to_contexts(results), cost


async def retrieve_results(
    config: RAGConfig,
    questions: list[str],
    collection_name: str | None = None,
    settings=None,
    env=None,
) -> tuple[list[list[dict]], float]:
    from src.storage.cost_tracker import get_total

    collection_name = collection_name or await get_or_build_collection(config, env=env)
    max_concurrency = EvalSettings().max_concurrent_questions
    start_cost = get_total()
    started = time.perf_counter()
    results = await _get_or_build_results(
        config=config,
        questions=questions,
        collection_name=collection_name,
        max_concurrency=max_concurrency,
        settings=settings,
        env=env,
    )
    log.info(
        "pipeline_contexts_ready",
        questions=len(questions),
        elapsed_sec=round(time.perf_counter() - started, 2),
    )
    return results, get_total() - start_cost


@observe(name="get_or_build_contexts")
async def _get_or_build_contexts(
    config: RAGConfig,
    questions: list[str],
    collection_name: str,
    max_concurrency: int,
    settings=None,
    env=None,
) -> list[list[str]]:
    results = await _get_or_build_results(
        config=config,
        questions=questions,
        collection_name=collection_name,
        max_concurrency=max_concurrency,
        settings=settings,
        env=env,
    )
    return _results_to_contexts(results)


async def _get_or_build_results(
    config: RAGConfig,
    questions: list[str],
    collection_name: str,
    max_concurrency: int,
    settings=None,
    env=None,
) -> list[list[dict]]:
    cache_path = _retrieval_cache_path(config, questions, collection_name)
    if cache_path.exists():
        try:
            data = json.loads(cache_path.read_text(encoding="utf-8"))
            results = data.get("results", [])
            if _valid_results(results, len(questions)):
                log.info("retrieval_cache_hit", path=str(cache_path), questions=len(questions))
                return results
            contexts = data.get("contexts", [])
            if _valid_contexts(contexts, len(questions)):
                log.info("retrieval_cache_hit", path=str(cache_path), questions=len(questions))
                return _contexts_to_results(contexts)
        except (OSError, json.JSONDecodeError):
            log.warning("retrieval_cache_unreadable", path=str(cache_path))

    started = time.perf_counter()
    retriever = await build_retriever(config, collection_name=collection_name, settings=settings, env=env)
    semaphore = asyncio.Semaphore(max_concurrency)

    async def retrieve_one(question: str) -> list[dict]:
        async with semaphore:
            nodes = await retriever.aretrieve(question)
            return [_node_to_result(config, node) for node in nodes]

    results = await asyncio.gather(*[retrieve_one(question) for question in questions])
    cache_path.write_text(
        json.dumps({"questions": questions, "results": results}, ensure_ascii=False),
        encoding="utf-8",
    )
    log.info(
        "retrieval_cache_saved",
        path=str(cache_path),
        questions=len(questions),
        elapsed_sec=round(time.perf_counter() - started, 2),
    )
    return results


def _retrieval_cache_path(
    config: RAGConfig,
    questions: list[str],
    collection_name: str,
) -> Path:
    key = get_config_hash({
        "collection_name": collection_name,
        "embedding_model": config.embedding_model,
        "chunk_size": config.chunk_size,
        "chunk_overlap": config.chunk_overlap,
        "node_parser": config.node_parser,
        "retriever": config.retriever,
        "window_size": config.window_size,
        "semantic_threshold": config.semantic_threshold,
        "semantic_buffer_size": config.semantic_buffer_size,
        "top_k": config.top_k,
        "hybrid_alpha": config.hybrid_alpha,
        "fusion_mode": config.fusion_mode,
        "fusion_num_queries": config.fusion_num_queries,
        "reranker": config.reranker,
        "reranker_top_n": config.reranker_top_n,
        "questions": questions,
    })
    return RETRIEVAL_CACHE_PATH / f"{key}.json"


def _valid_contexts(contexts, expected_count: int) -> bool:
    return (
        isinstance(contexts, list)
        and len(contexts) == expected_count
        and all(isinstance(context, list) for context in contexts)
    )


def _valid_results(results, expected_count: int) -> bool:
    return (
        isinstance(results, list)
        and len(results) == expected_count
        and all(isinstance(items, list) for items in results)
        and all(isinstance(item, dict) for items in results for item in items)
    )


def _contexts_to_results(contexts: list[list[str]]) -> list[list[dict]]:
    return [
        [
            {
                "node_id": f"legacy_{question_idx}_{rank}",
                "doc_id": f"legacy_{question_idx}_{rank}",
                "title": "",
                "score": 1.0 / (rank + 1),
                "text": text,
            }
            for rank, text in enumerate(context)
        ]
        for question_idx, context in enumerate(contexts)
    ]


def _results_to_contexts(results: list[list[dict]]) -> list[list[str]]:
    return [[item.get("text", "") for item in items] for items in results]


contexts_to_results = _contexts_to_results
results_to_contexts = _results_to_contexts


def _node_to_result(config: RAGConfig, node_with_score) -> dict:
    node = node_with_score.node
    metadata = dict(node.metadata or {})
    text = node.get_content()
    if config.node_parser == "sentence_window":
        text = metadata.get("window") or metadata.get("original_text") or text
    title = metadata.get("title", "")
    return {
        "node_id": node.node_id,
        "doc_id": title or node.node_id,
        "title": title,
        "score": float(node_with_score.score or 0.0),
        "text": text,
    }
