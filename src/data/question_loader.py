"""Load evaluation questions from HotpotQA dataset in JSONL format."""

import json
from pathlib import Path

QUESTIONS_PATH = Path("data/hotpotqa/questions.jsonl")


def load_eval_question_items(n: int) -> list[dict]:
    """Load first n question items from JSONL, extracting id, question, answer, supporting_titles."""
    items = []
    lines = QUESTIONS_PATH.read_text().strip().splitlines()
    for line in lines[:n]:
        item = json.loads(line)
        items.append(
            {
                "id": item["id"],
                "question": item["question"],
                "answer": item["answer"],
                "supporting_titles": item.get("supporting_titles", []),
            }
        )
    assert len(items) == n, f"Expected {n} questions, got {len(items)}"
    return items


def load_eval_questions(n: int) -> tuple[list[str], list[str]]:
    """Load first n questions and answers separately. Returns (questions, answers) tuples."""
    items = load_eval_question_items(n)
    return [item["question"] for item in items], [item["answer"] for item in items]
