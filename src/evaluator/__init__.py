"""Evaluation subpackage: RAGAS metrics, IR metrics, and configuration scoring."""
from src.evaluator.ir_metrics import evaluate_ir_metrics
from src.evaluator.ragas_runner import evaluator_node, run_single_eval
from src.evaluator.ragas_setup import build_ragas_embeddings, build_ragas_llm, build_ragas_metrics
from src.evaluator.scorer import acceptance_node

__all__ = [
    "evaluate_ir_metrics",
    "build_ragas_llm",
    "build_ragas_embeddings",
    "build_ragas_metrics",
    "run_single_eval",
    "evaluator_node",
    "acceptance_node",
]
