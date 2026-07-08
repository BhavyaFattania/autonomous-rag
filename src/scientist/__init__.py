"""Autonomous scientist module for RAG configuration optimization.

Drives an experiment-proposal and reflection loop that systematically explores
RAG configurations (chunking, retrieval, reranking) to maximize retrieval metrics.
Combines LLM-guided exploration with deterministic candidate generation and deduplication.
"""

from src.scientist.brain import scientist_node
from src.scientist.candidates import (
    get_fallback_candidates,
    get_reranker_probe_candidates,
    get_structured_exploration_candidates,
)
from src.scientist.deduplicator import deduplicator_node
from src.scientist.prompt_builder import build_scientist_prompt
from src.scientist.proposal import (
    fallback_proposal,
    reranker_probe_proposal,
    select_unused_candidate,
    structured_exploration_proposal,
)
from src.scientist.reflection import reflection_node

__all__ = [
    "scientist_node",
    "deduplicator_node",
    "reflection_node",
    "get_structured_exploration_candidates",
    "get_reranker_probe_candidates",
    "get_fallback_candidates",
    "fallback_proposal",
    "reranker_probe_proposal",
    "structured_exploration_proposal",
    "select_unused_candidate",
    "build_scientist_prompt",
]
