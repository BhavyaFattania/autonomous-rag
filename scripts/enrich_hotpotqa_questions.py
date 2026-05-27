"""
Backfill supporting_titles into data/hotpotqa/questions.jsonl.

Usage:
    python scripts/enrich_hotpotqa_questions.py
"""

import json
import urllib.request
from pathlib import Path


URL = "http://curtis.ml.cmu.edu/datasets/hotpot/hotpot_dev_fullwiki_v1.json"
QUESTIONS_PATH = Path("data/hotpotqa/questions.jsonl")


def main():
    if not QUESTIONS_PATH.exists():
        raise FileNotFoundError(f"{QUESTIONS_PATH} not found")

    existing = [
        json.loads(line)
        for line in QUESTIONS_PATH.read_text(encoding="utf-8").strip().splitlines()
        if line.strip()
    ]
    if existing and all("supporting_titles" in item for item in existing):
        print("questions.jsonl already has supporting_titles")
        return

    print(f"Downloading HotpotQA metadata from {URL}...")
    with urllib.request.urlopen(URL) as response:
        dataset = json.loads(response.read().decode("utf-8"))
    by_id = {item["_id"]: item for item in dataset}

    enriched = []
    for item in existing:
        source = by_id.get(item["id"], {})
        supporting_titles = sorted({title for title, _ in source.get("supporting_facts", [])})
        enriched.append({**item, "supporting_titles": supporting_titles})

    with QUESTIONS_PATH.open("w", encoding="utf-8") as f:
        for item in enriched:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Updated {QUESTIONS_PATH} with supporting_titles")


if __name__ == "__main__":
    main()
