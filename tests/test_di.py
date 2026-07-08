"""Tests demonstrating dependency injection with mock providers."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from src.core.interfaces import (
    ICostTracker,
    ILLMClient,
)
from src.core.provider import Provider

# ── Mock Implementations ───────────────────────────────────────────────────────


class MockCostTracker:
    """Fake ICostTracker backed by an in-memory float, no persistence."""

    def __init__(self):
        self._total = 0.0
        self._ceiling = 100.0

    def initialize(self, hard_ceiling, warning_threshold, start_cost=0.0):
        self._total = start_cost
        self._ceiling = hard_ceiling

    def add_cost(self, usd: float) -> float:
        self._total += usd
        return self._total

    def get_total(self) -> float:
        return self._total


class MockLLMClient:
    """Fake ILLMClient whose call() is an AsyncMock so tests can assert/override the response."""

    def __init__(self):
        self.call = AsyncMock(return_value="mock response")

    async def call(self, model_id, messages, max_tokens, task, **kwargs):
        return await self.call(model_id, messages, max_tokens, task, **kwargs)


class MockDatabase:
    """Fake Database with no-op init/connect for tests that don't need real persistence."""

    def __init__(self):
        self.path = ":memory:"
        self.init = AsyncMock()
        self.connect = MagicMock()


class MockChromaFactory:
    """Fake Chroma client/path factory to avoid touching disk in tests."""

    def get_client(self):
        return MagicMock()

    def path(self):
        from pathlib import Path

        return Path("/tmp/mock_chroma")


class MockRagasFactory:
    """Fake factory for RAGAS LLM/embeddings/metrics, returning mocks instead of real clients."""

    def build_llm(self, model_routing, env=None):
        return MagicMock()

    def build_embeddings(self, model_name, env=None):
        return MagicMock()

    def build_metrics(self, metric_names):
        return []


class MockModelRoutingProvider:
    """Fake model-routing provider with a fixed role -> model-id mapping."""

    def __init__(self):
        self._models = {
            "scientist": "mock/scientist-model",
            "rag_generator": "mock/generator-model",
            "ragas_judge": "mock/judge-model",
        }

    def get_model_id(self, role: str) -> str:
        return self._models.get(role, "mock/default")

    def get_config(self, role: str):
        return MagicMock()


# ── Tests ──────────────────────────────────────────────────────────────────────


class TestProvider:
    """Verifies Provider correctly wires and exposes all injected dependencies."""

    def test_provider_wires_all_deps(self):
        """All constructor args are stored as-is (identity, not copies) on the Provider instance."""
        pt = MockCostTracker()
        llm = MockLLMClient()
        db = MockDatabase()
        chroma = MockChromaFactory()
        ragas = MockRagasFactory()
        routing = MockModelRoutingProvider()

        provider = Provider(
            cost_tracker=pt,
            llm_client=llm,
            database=db,
            chroma_factory=chroma,
            ragas_factory=ragas,
            model_routing_provider=routing,
            env={"OPENROUTER_API_KEY": "sk-test"},
        )

        assert provider.cost_tracker is pt
        assert provider.llm_client is llm
        assert provider.database is db
        assert provider.chroma_factory is chroma
        assert provider.ragas_factory is ragas
        assert provider.model_routing_provider is routing
        assert provider.env == {"OPENROUTER_API_KEY": "sk-test"}

    @pytest.mark.asyncio
    async def test_mock_cost_tracker(self):
        """Sanity check that the mock tracker itself accumulates cost correctly."""
        tracker = MockCostTracker()
        tracker.initialize(hard_ceiling=10.0, warning_threshold=7.0)
        assert tracker.get_total() == 0.0

        tracker.add_cost(2.5)
        assert tracker.get_total() == 2.5

        tracker.add_cost(5.0)
        assert tracker.get_total() == 7.5

    @pytest.mark.asyncio
    async def test_mock_llm_client(self):
        """Sanity check that the mock LLM client returns the stubbed response and records the call."""
        llm = MockLLMClient()

        result = await llm.call(
            model_id="mock/model",
            messages=[{"role": "user", "content": "hello"}],
            max_tokens=100,
            task="test",
        )

        assert result == "mock response"
        llm.call.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_provider_passed_to_scientist_node_with_json_response(self):
        """scientist_node produces a proposal when LLM returns valid JSON."""
        from src.scientist.brain import scientist_node

        mock_llm = MockLLMClient()
        valid_json = json.dumps(
            {
                "embedding_model": "openai/text-embedding-3-small",
                "chunk_size": 512,
                "chunk_overlap": 128,
                "node_parser": "sentence",
                "retriever": "dense",
                "top_k": 5,
                "hybrid_alpha": 1.0,
                "reranker": None,
                "generator_model": "deepseek/deepseek-v4-flash",
                "hypothesis": "Smaller chunks improve recall",
            }
        )
        mock_llm.call.return_value = valid_json

        provider = Provider(
            cost_tracker=MockCostTracker(),
            llm_client=mock_llm,
        )

        state = {
            "experiments_completed": 5,
            "history_summary": "",
            "baseline_config": {},
            "current_best_config": {},
            "current_best_weighted_score": 0.5,
            "successful_patterns": [],
            "failed_patterns": [],
        }

        mock_settings = MagicMock()
        mock_settings.explore_exploit.structured_exploration_experiments = 0
        mock_settings.explore_exploit.reranker_probe_every_n_experiments = 0
        mock_settings.explore_exploit.exploit_probability = 0.0
        mock_settings.search_space = MagicMock()

        result = await scientist_node(state, mock_settings, provider=provider)

        assert isinstance(result, dict)
        assert result.get("status") in ("RUNNING",)
        assert "experiment_uuid" in result

    def test_icost_tracker_protocol(self):
        """Verify MockCostTracker satisfies ICostTracker protocol."""
        tracker = MockCostTracker()
        assert isinstance(tracker, ICostTracker)

    def test_illm_client_protocol(self):
        """Verify MockLLMClient satisfies ILLMClient protocol."""
        llm = MockLLMClient()
        assert isinstance(llm, ILLMClient)
