import json
from pathlib import Path

QUESTIONS_PATH = Path("data/hotpotqa/questions.jsonl")


def load_eval_question_items(n: int) -> list[dict]:
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
    items = load_eval_question_items(n)
    return [item["question"] for item in items], [item["answer"] for item in items]
