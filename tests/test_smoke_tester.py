"""Tests for the retrieval smoke-test node."""

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
    settings = SimpleNamespace(evaluation=SimpleNamespace(smoke_test_n_questions=1))

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
