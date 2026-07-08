"""Tests for config-hash-based deduplication of experiment candidates."""

import os
from pathlib import Path

import aiosqlite
import pytest
from src.scientist.proposal import select_unused_candidate as _select_unused_candidate
from src.storage.database import Database
from src.utils.config_helpers import logical_config as _logical_config
from src.utils.hashing import get_config_hash


@pytest.fixture
def local_tmp_path(tmp_path_factory):
    """Project-local temp dir to avoid Windows system temp permission errors."""
    base = Path("pytest_temp")
    base.mkdir(exist_ok=True)
    d = base / "deduplicator_test"
    d.mkdir(exist_ok=True)
    return d


def test_deduplicator_hash_ignores_internal_config_keys():
    """Internal-only keys (e.g. "_collection_name") must not change the config hash used for dedup."""
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


async def test_scientist_candidate_selection_skips_reserved_hash(local_tmp_path):
    """select_unused_candidate must skip a candidate whose config hash is already recorded in the DB."""
    db_path = str(local_tmp_path / "experiments.sqlite")

    old_default = Database.default_path
    Database.default_path = db_path
    try:
        db = Database()
        await db.init()

        first = _candidate(top_k=5)
        second = _candidate(top_k=7)
        async with aiosqlite.connect(db_path) as conn:
            await conn.execute(
                "INSERT INTO config_hashes (config_hash, first_seen) VALUES (?, ?)",
                (get_config_hash(first), "2026-01-01T00:00:00+00:00"),
            )
            await conn.commit()

        selected = await _select_unused_candidate([first, second], {})
    finally:
        Database.default_path = old_default
        for suffix in ("", "-wal", "-shm"):
            path = str(local_tmp_path / f"experiments.sqlite{suffix}")
            if os.path.exists(path):
                os.remove(path)

    assert selected["top_k"] == 7


def _candidate(top_k: int) -> dict:
    """Build a minimal candidate RAG config dict, varying only top_k."""
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
