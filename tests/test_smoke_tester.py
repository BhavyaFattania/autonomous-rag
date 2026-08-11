"""Tests for the retrieval smoke-test node."""

import asyncio
from types import SimpleNamespace
from unittest.mock import Mock

from src.rag_pipeline import pipeline, smoke_tester


async def test_smoke_test_node_logs_pipeline_errors(monkeypatch):
    async def failing_retrieval(*_args, **_kwargs):
        raise RuntimeError("retrieval failed")

    def load_one_question(*, n):
        assert n == 1
        return ["question"], []

    monkeypatch.setattr(smoke_tester, "load_eval_questions", load_one_question)
    monkeypatch.setattr(pipeline, "retrieve_contexts", failing_retrieval)
    error_log = Mock()
    monkeypatch.setattr(smoke_tester.log, "error", error_log)

    state = {
        "validated_config": {
            "chunk_size": 512,
            "chunk_overlap": 64,
            "top_k": 5,
            "hybrid_alpha": 0.7,
            "embedding_model": "openai/text-embedding-3-small",
            "reranker": None,
            "reranker_top_n": None,
            "generator_model": "deepseek/deepseek-v4-flash",
        }
    }
    settings = SimpleNamespace(
        evaluation=SimpleNamespace(smoke_test_n_questions=1, smoke_test_timeout_sec=180.0)
    )

    result = await smoke_tester.smoke_test_node(state, settings)

    assert result == {
        "status": "FAILED_SMOKE",
        "failure_reason": "Pipeline error: retrieval failed",
    }
    error_log.assert_called_once_with(
        "smoke_test_error",
        error="retrieval failed",
        exc_info=True,
    )


async def test_smoke_test_node_uses_configured_timeout(monkeypatch):
    """The smoke test must honor settings.evaluation.smoke_test_timeout_sec instead of a
    hardcoded value, both for the asyncio.wait_for call and the reported failure message."""

    captured_timeout = {}

    async def fake_wait_for(coro, timeout):
        captured_timeout["value"] = timeout
        coro.close()
        raise TimeoutError

    def load_one_question(*, n):
        return ["question"], []

    monkeypatch.setattr(smoke_tester, "load_eval_questions", load_one_question)
    monkeypatch.setattr(pipeline, "retrieve_contexts", lambda *_a, **_kw: asyncio.sleep(0))
    monkeypatch.setattr(smoke_tester.asyncio, "wait_for", fake_wait_for)

    state = {
        "validated_config": {
            "chunk_size": 512,
            "chunk_overlap": 64,
            "top_k": 5,
            "hybrid_alpha": 0.7,
            "embedding_model": "openai/text-embedding-3-small",
            "reranker": None,
            "reranker_top_n": None,
            "generator_model": "deepseek/deepseek-v4-flash",
        }
    }
    settings = SimpleNamespace(
        evaluation=SimpleNamespace(smoke_test_n_questions=1, smoke_test_timeout_sec=5.0)
    )

    result = await smoke_tester.smoke_test_node(state, settings)

    assert captured_timeout["value"] == 5.0
    assert result == {
        "status": "FAILED_SMOKE",
        "failure_reason": "Smoke test timed out after 5.0s",
    }
