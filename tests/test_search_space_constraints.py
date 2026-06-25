from unittest.mock import patch
from src.orchestrator.validator import validator_node
from src.scientist.candidates import get_structured_exploration_candidates
from src.scientist.prompt_builder import build_scientist_prompt as _build_scientist_prompt


def test_validator_enforces_search_space():
    mock_settings = {
        "evaluation": {
            "allow_expensive_parser_builds": False,
            "allow_new_index_builds": True,
        },
        "search_space": {
            "allowed_node_parsers": ["sentence"],
            "allowed_retrievers": ["dense"],
            "allowed_chunk_sizes": [512],
            "allowed_chunk_overlaps": [128],
            "allowed_generator_models": ["deepseek/deepseek-v4-flash"],
            "allowed_rerankers": [None],
        }
    }

    # Valid config
    state_valid = {
        "proposed_config": {
            "node_parser": "sentence",
            "retriever": "dense",
            "chunk_size": 512,
            "chunk_overlap": 128,
            "top_k": 5,
            "hybrid_alpha": 1.0,
            "embedding_model": "openai/text-embedding-3-small",
            "generator_model": "deepseek/deepseek-v4-flash",
            "reranker": None,
            "reranker_top_n": None,
        }
    }

    # Invalid config (wrong node_parser)
    state_invalid_parser = {
        "proposed_config": {
            "node_parser": "token",
            "retriever": "dense",
            "chunk_size": 512,
            "chunk_overlap": 128,
            "top_k": 5,
            "hybrid_alpha": 1.0,
            "embedding_model": "openai/text-embedding-3-small",
            "generator_model": "deepseek/deepseek-v4-flash",
            "reranker": None,
            "reranker_top_n": None,
        }
    }

    # Invalid config (wrong retriever)
    state_invalid_retriever = {
        "proposed_config": {
            "node_parser": "sentence",
            "retriever": "bm25",
            "chunk_size": 512,
            "chunk_overlap": 128,
            "top_k": 5,
            "hybrid_alpha": 0.0,
            "embedding_model": "openai/text-embedding-3-small",
            "generator_model": "deepseek/deepseek-v4-flash",
            "reranker": None,
            "reranker_top_n": None,
        }
    }

    with patch("src.orchestrator.config_loader.load_run_settings", return_value=mock_settings):
        res_valid = validator_node(state_valid)
        assert res_valid["status"] == "RUNNING"

        res_invalid_parser = validator_node(state_invalid_parser)
        assert res_invalid_parser["status"] == "FAILED_VALIDATION"
        assert "node_parser='token' is not in developer allowed list" in res_invalid_parser["failure_reason"]

        res_invalid_retriever = validator_node(state_invalid_retriever)
        assert res_invalid_retriever["status"] == "FAILED_VALIDATION"
        assert "retriever='bm25' is not in developer allowed list" in res_invalid_retriever["failure_reason"]


def test_candidates_filtering():
    mock_settings = {
        "evaluation": {
            "allow_expensive_parser_builds": False,
            "allow_new_index_builds": True,
        },
        "search_space": {
            "allowed_node_parsers": ["sentence"],
            "allowed_retrievers": ["dense"],
            "allowed_chunk_sizes": [512],
            "allowed_chunk_overlaps": [128],
        }
    }

    state = {
        "baseline_config": {
            "embedding_model": "openai/text-embedding-3-small",
        }
    }

    with patch("src.orchestrator.config_loader.load_run_settings", return_value=mock_settings):
        candidates = get_structured_exploration_candidates(state)
        assert len(candidates) > 0
        for cand in candidates:
            assert cand["node_parser"] == "sentence"
            assert cand["retriever"] == "dense"
            assert cand["chunk_size"] == 512
            assert cand["chunk_overlap"] == 128


def test_brain_prompt_incorporates_constraints():
    mock_settings = {
        "reflection": {
            "max_history_tokens": 1000,
        },
        "evaluation": {
            "allow_new_index_builds": True,
        },
        "search_space": {
            "allowed_node_parsers": ["sentence"],
            "allowed_retrievers": ["dense", "weighted_hybrid_rrf"],
        }
    }

    state = {
        "current_best_config": {
            "embedding_model": "openai/text-embedding-3-small",
        },
        "current_best_weighted_score": 0.5,
    }

    with patch("src.orchestrator.config_loader.load_run_settings", return_value=mock_settings):
        prompt = _build_scientist_prompt(state, exploit=False)
        assert "CRITICAL DEVELOPER CONSTRAINTS" in prompt
        assert "- node_parser: must be one of ['sentence']" in prompt
        assert "- retriever: must be one of ['dense', 'weighted_hybrid_rrf']" in prompt
