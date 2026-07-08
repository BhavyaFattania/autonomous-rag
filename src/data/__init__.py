"""Data loading utilities. Exposes functions for loading evaluation datasets from HotpotQA."""

from src.data.question_loader import load_eval_question_items, load_eval_questions

__all__ = [
    "load_eval_question_items",
    "load_eval_questions",
]
