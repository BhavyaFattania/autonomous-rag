"""Tests that indexer_node publishes real progress events to the EventBus,
without touching real Chroma/embeddings (that plumbing is covered by
test_index_builder_progress.py)."""

import pytest
from src.core.events import ExperimentEvent
from src.indexer import collection_manager

_VALID_CONFIG = {
    "node_parser": "sentence",
    "chunk_size": 512,
    "chunk_overlap": 64,
    "embedding_model": "openai/text-embedding-3-small",
    "retriever": "weighted_hybrid_rrf",
    "hybrid_alpha": 0.5,
    "top_k": 5,
    "reranker": None,
    "reranker_top_n": None,
    "generator_model": "deepseek/deepseek-v4-flash",
}


class _FakeBus:
    def __init__(self):
        self.published: list[ExperimentEvent] = []

    def publish(self, event: ExperimentEvent) -> None:
        self.published.append(event)


@pytest.mark.asyncio
async def test_indexer_node_publishes_progress_events(monkeypatch):
    async def _fake_get_or_build_collection(config, settings, env=None, on_progress=None):
        on_progress(64, 150)
        on_progress(150, 150)
        return "fake_collection"

    monkeypatch.setattr(
        collection_manager, "get_or_build_collection", _fake_get_or_build_collection
    )
    monkeypatch.setattr(collection_manager, "get_total", lambda: 0.42)

    bus = _FakeBus()
    state = {"validated_config": dict(_VALID_CONFIG), "experiments_completed": 6}

    result = await collection_manager.indexer_node(
        state, settings=object(), env=None, provider=None, event_bus=bus
    )

    assert result["status"] == "RUNNING"
    assert result["validated_config"]["_collection_name"] == "fake_collection"
    assert [e.progress_current for e in bus.published] == [64, 150]
    assert [e.progress_total for e in bus.published] == [150, 150]
    assert all(e.experiment == 7 for e in bus.published)
    assert all(e.node == "indexer" for e in bus.published)
    assert all(e.cost_total_usd == 0.42 for e in bus.published)


@pytest.mark.asyncio
async def test_indexer_node_without_event_bus_does_not_crash(monkeypatch):
    async def _fake_get_or_build_collection(config, settings, env=None, on_progress=None):
        on_progress(1, 1)
        return "fake_collection"

    monkeypatch.setattr(
        collection_manager, "get_or_build_collection", _fake_get_or_build_collection
    )

    state = {"validated_config": dict(_VALID_CONFIG), "experiments_completed": 0}

    result = await collection_manager.indexer_node(state, settings=object(), event_bus=None)

    assert result["status"] == "RUNNING"


@pytest.mark.asyncio
async def test_get_or_build_collection_forwards_on_progress_on_cache_miss(monkeypatch):
    from src.models.rag_config import RAGConfig

    calls: list[tuple[int, int]] = []

    async def _fake_build_collection(
        config, name, chroma_client, settings, env=None, on_progress=None
    ):
        on_progress(1, 1)

    class _FakeCollection:
        def count(self):
            return 0

    class _FakeChromaClient:
        def get_collection(self, name):
            # get_or_build_collection's except clauses re-raise RuntimeError but
            # treat any other exception type as "not found, go build it" -- this
            # mirrors real chromadb's not-found exception, which isn't a RuntimeError.
            raise ValueError("no such collection")

        def create_collection(self, name):
            return _FakeCollection()

    monkeypatch.setattr(collection_manager, "build_collection", _fake_build_collection)
    monkeypatch.setattr(collection_manager, "_get_chroma_client", lambda: _FakeChromaClient())
    monkeypatch.setattr(collection_manager, "new_index_builds_allowed", lambda settings: True)
    monkeypatch.setattr(
        collection_manager, "expensive_parser_builds_allowed", lambda settings: True
    )

    config = RAGConfig(**_VALID_CONFIG)
    await collection_manager.get_or_build_collection(
        config, settings=object(), on_progress=lambda done, total: calls.append((done, total))
    )

    assert calls == [(1, 1)]
