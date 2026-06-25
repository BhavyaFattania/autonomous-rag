import json
from pathlib import Path

log = None


def build_scientist_prompt(
    state,
    exploit: bool,
    *,
    recent_history: list[str] | None = None,
    history_summary: str = "",
) -> str:
    from src.orchestrator.config_loader import load_run_settings

    settings = load_run_settings()
    system_prompt = Path("prompts/scientist_v1.txt").read_text()

    search_space = settings.get("search_space") or {}
    allowed_node_parsers = search_space.get("allowed_node_parsers")
    allowed_chunk_sizes = search_space.get("allowed_chunk_sizes")
    allowed_chunk_overlaps = search_space.get("allowed_chunk_overlaps")

    indexed_configs_text = "Any valid chunk_size/chunk_overlap pair."
    if not settings["evaluation"].get("allow_new_index_builds", True):
        from src.indexer.collection_manager import list_available_index_configs
        indexed_configs = list_available_index_configs()

        filtered_configs = []
        for iconfig in indexed_configs:
            if allowed_node_parsers is not None and iconfig.get("node_parser") not in allowed_node_parsers:
                continue
            if allowed_chunk_sizes is not None and iconfig.get("chunk_size") not in allowed_chunk_sizes:
                continue
            if allowed_chunk_overlaps is not None and iconfig.get("chunk_overlap") not in allowed_chunk_overlaps:
                continue
            filtered_configs.append(iconfig)
        indexed_configs = filtered_configs

        indexed_configs_text = json.dumps(indexed_configs, indent=2)

    if recent_history is not None:
        parts = []
        if history_summary:
            parts.append(f"[Compressed summary of older experiments]\n{history_summary}")
        if recent_history:
            parts.append("[Recent experiments (verbatim)]\n" + "\n".join(recent_history))
        history_text = "\n\n".join(parts) if parts else ""
    else:
        history_lines = _build_history_lines(state)
        history_text = _truncate_history(
            history_lines,
            max_chars=settings["reflection"]["max_history_tokens"] * 4,
        )

    mode = "EXPLOIT (refine near current best)" if exploit else "EXPLORE (try something new)"

    constraints_lines = []
    for key, label in [
        ("allowed_node_parsers", "node_parser"),
        ("allowed_retrievers", "retriever"),
        ("allowed_chunk_sizes", "chunk_size"),
        ("allowed_chunk_overlaps", "chunk_overlap"),
        ("allowed_generator_models", "generator_model"),
        ("allowed_rerankers", "reranker"),
    ]:
        allowed = search_space.get(key)
        if allowed is not None:
            constraints_lines.append(f"- {label}: must be one of {allowed}")

    constraints_text = ""
    if constraints_lines:
        constraints_text = "\nCRITICAL DEVELOPER CONSTRAINTS (You must strictly follow these rules):\n" + "\n".join(constraints_lines) + "\n"

    user_message = f"""
System instructions:
{system_prompt}

Current best config:
{json.dumps(state.get("current_best_config", {}), indent=2)}

Current best composite retrieval score: {state.get("current_best_weighted_score", 0.0):.4f}

Active scoring metric:
Composite retrieval score from Recall@K, Precision@K, nDCG@K, MRR, and periodic
RAGAS context metrics. Prioritize parser, retriever, top_k, hybrid_alpha, and
reranker only when it is likely to improve the retrieval evidence.

Experiment history:
{history_text if history_text else "No experiments yet. Start from baseline."}

Reflection summary:
{state.get("reflection_summary", "No reflection yet.")}

Allowed indexed configurations:
{indexed_configs_text}

If allowed indexed configurations are listed, choose only one of those
embedding_model/node_parser/chunk_size/chunk_overlap/parser-param combinations.
Other retrieval parameters may vary.
{constraints_text}
Mode for this experiment: {mode}

Respond with ONLY the JSON object.
"""
    return user_message.strip()


def _build_history_lines(state) -> list[str]:
    lines = []
    for i, pattern in enumerate(state.get("successful_patterns", [])):
        lines.append(f"ACCEPTED[{i+1}]: {pattern}")
    for i, pattern in enumerate(state.get("failed_patterns", [])):
        lines.append(f"REJECTED[{i+1}]: {pattern}")
    return lines


def _truncate_history(history_lines: list[str], max_chars: int) -> str:
    selected = []
    total = 0
    for line in reversed(history_lines):
        line_len = len(line) + 1
        if selected and total + line_len > max_chars:
            break
        selected.append(line)
        total += line_len
    return "\n".join(reversed(selected))
