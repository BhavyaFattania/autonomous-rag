# tests/test_brain.py
"""Unit tests for src/scientist/brain.py and src/scientist/reflection.py."""

from unittest.mock import patch

from src.scientist.brain import _build_scientist_prompt, _truncate_history
from src.scientist.reflection import _truncate_to_sentence


# ─── _build_scientist_prompt ─────────────────────────────────────────────────

BASE_SETTINGS = {
    "reflection": {"max_history_tokens": 500},
    "evaluation": {"allow_new_index_builds": True},
    "search_space": {},
    "explore_exploit": {"exploit_probability": 0.5},
}

BASE_STATE = {
    "current_best_config": {
        "embedding_model": "openai/text-embedding-3-small",
        "chunk_size": 512,
    },
    "current_best_weighted_score": 0.55,
    "successful_patterns": [],
    "failed_patterns": [],
    "reflection_summary": "",
}


def _make_prompt(state=None, exploit=False, settings_override=None):
    s = {**BASE_SETTINGS, **(settings_override or {})}
    st = {**BASE_STATE, **(state or {})}
    with patch("src.orchestrator.config_loader.load_run_settings", return_value=s):
        with patch("pathlib.Path.read_text", return_value="SYSTEM_INSTRUCTIONS"):
            return _build_scientist_prompt(st, exploit=exploit)


def test_prompt_contains_system_instructions():
    prompt = _make_prompt()
    assert "SYSTEM_INSTRUCTIONS" in prompt


def test_prompt_contains_best_config():
    prompt = _make_prompt()
    assert "chunk_size" in prompt
    assert "512" in prompt


def test_prompt_mode_exploit():
    prompt = _make_prompt(exploit=True)
    assert "EXPLOIT" in prompt


def test_prompt_mode_explore():
    prompt = _make_prompt(exploit=False)
    assert "EXPLORE" in prompt


def test_prompt_no_constraints_when_search_space_empty():
    prompt = _make_prompt()
    assert "CRITICAL DEVELOPER CONSTRAINTS" not in prompt


def test_prompt_injects_node_parser_constraint():
    settings = {
        **BASE_SETTINGS,
        "search_space": {"allowed_node_parsers": ["sentence", "token"]},
    }
    prompt = _make_prompt(settings_override=settings)
    assert "CRITICAL DEVELOPER CONSTRAINTS" in prompt
    assert "node_parser: must be one of ['sentence', 'token']" in prompt


def test_prompt_injects_retriever_constraint():
    settings = {
        **BASE_SETTINGS,
        "search_space": {"allowed_retrievers": ["dense"]},
    }
    prompt = _make_prompt(settings_override=settings)
    assert "retriever: must be one of ['dense']" in prompt


def test_prompt_injects_chunk_size_constraint():
    settings = {
        **BASE_SETTINGS,
        "search_space": {"allowed_chunk_sizes": [512, 1024]},
    }
    prompt = _make_prompt(settings_override=settings)
    assert "chunk_size: must be one of [512, 1024]" in prompt


def test_prompt_history_appended():
    state = {
        **BASE_STATE,
        "successful_patterns": ["parser=sentence score=0.60"],
        "failed_patterns": ["parser=token score=0.40"],
    }
    prompt = _make_prompt(state=state)
    assert "ACCEPTED[1]" in prompt
    assert "REJECTED[1]" in prompt


def test_prompt_reflection_summary_included():
    state = {**BASE_STATE, "reflection_summary": "Use dense retriever for high recall."}
    prompt = _make_prompt(state=state)
    assert "Use dense retriever for high recall." in prompt


def test_prompt_ends_with_json_instruction():
    prompt = _make_prompt()
    assert "Respond with ONLY the JSON object." in prompt


# ─── _truncate_history ────────────────────────────────────────────────────────

def test_truncate_history_empty():
    assert _truncate_history([], max_chars=100) == ""


def test_truncate_history_within_limit():
    lines = ["ACCEPTED[1]: abc", "REJECTED[1]: def"]
    result = _truncate_history(lines, max_chars=1000)
    assert "ACCEPTED[1]: abc" in result
    assert "REJECTED[1]: def" in result


def test_truncate_history_preserves_most_recent():
    # Most recent lines are at the end; truncation should keep them.
    lines = [f"ACCEPTED[{i}]: line {i}" for i in range(20)]
    result = _truncate_history(lines, max_chars=80)
    # The last line must survive
    assert "ACCEPTED[19]: line 19" in result
    # Early lines must be dropped
    assert "ACCEPTED[0]: line 0" not in result


def test_truncate_history_single_line():
    lines = ["ACCEPTED[1]: short line"]
    assert _truncate_history(lines, max_chars=10) == "ACCEPTED[1]: short line"


# ─── _truncate_to_sentence (reflection) ──────────────────────────────────────

def test_truncate_to_sentence_no_truncation_needed():
    text = "Short text."
    assert _truncate_to_sentence(text, max_chars=1000) == text


def test_truncate_to_sentence_at_newline():
    text = "Line one.\nLine two.\n" + "X" * 5000
    result = _truncate_to_sentence(text, max_chars=25)
    assert result.endswith("\n") or result.endswith(".")
    assert "X" not in result


def test_truncate_to_sentence_at_period():
    text = "First sentence. Second sentence. " + "Z" * 5000
    result = _truncate_to_sentence(text, max_chars=40)
    assert result.endswith(".")
    assert "Z" not in result


def test_truncate_to_sentence_fallback():
    # No punctuation in the window — should return raw truncation
    text = "a" * 100
    result = _truncate_to_sentence(text, max_chars=20)
    assert len(result) <= 20
