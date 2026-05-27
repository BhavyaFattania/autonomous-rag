from src.scientist.deduplicator import _logical_config
from src.scientist.brain import _select_unused_candidate
from src.storage import db
from src.utils.hashing import get_config_hash
import aiosqlite
import os


def test_deduplicator_hash_ignores_internal_config_keys():
    stored_config = {
        "chunk_size": 512,
        "chunk_overlap": 64,
        "top_k": 5,
        "hybrid_alpha": 1.0,
    }
    validated_config = {
        **stored_config,
        "_collection_name": "rag_openai_text_embedding_3_small_hierarchical_512_64",
    }

    assert get_config_hash(_logical_config(validated_config)) == get_config_hash(stored_config)


async def test_scientist_candidate_selection_skips_reserved_hash(tmp_path):
    old_path = db.DB_PATH
    db.DB_PATH = str(tmp_path / "experiments.sqlite")
    await db.init_db()

    first = _candidate(top_k=5)
    second = _candidate(top_k=7)
    async with aiosqlite.connect(db.DB_PATH) as conn:
        await conn.execute(
            "INSERT INTO config_hashes (config_hash, first_seen) VALUES (?, ?)",
            (get_config_hash(first), "2026-01-01T00:00:00+00:00"),
        )
        await conn.commit()

    try:
        selected = await _select_unused_candidate([first, second], {})
    finally:
        db.DB_PATH = old_path
        for suffix in ("", "-wal", "-shm"):
            path = str(tmp_path / f"experiments.sqlite{suffix}")
            if os.path.exists(path):
                os.remove(path)

    assert selected["top_k"] == 7


def _candidate(top_k: int) -> dict:
    return {
        "chunk_size": 512,
        "chunk_overlap": 64,
        "top_k": top_k,
        "hybrid_alpha": 1.0,
        "embedding_model": "openai/text-embedding-3-small",
        "node_parser": "hierarchical",
        "retriever": "auto_merging",
        "window_size": None,
        "semantic_threshold": None,
        "semantic_buffer_size": None,
        "fusion_mode": None,
        "fusion_num_queries": None,
        "reranker": None,
        "reranker_top_n": None,
        "generator_model": "deepseek/deepseek-v4-flash",
    }
