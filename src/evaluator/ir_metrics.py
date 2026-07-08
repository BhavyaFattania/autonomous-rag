"""Information Retrieval metrics evaluation (recall, precision, NDCG, MRR).

Computes retrieval quality metrics by comparing ranked results against ground truths.
Supports ranx library with fallback implementation if unavailable.
"""
from __future__ import annotations


def evaluate_ir_metrics(
    question_ids: list[str],
    retrieval_results: list[list[dict]],
    ground_truths: list[str],
    supporting_titles: list[list[str]] | None,
    k: int,
) -> dict[str, float]:
    """Compute recall@k, precision@k, NDCG@k, and MRR metrics.

    Uses supporting_titles if provided, otherwise matches ground_truth strings against result text.
    """
    qrels, runs = _build_qrels_and_run(
        question_ids=question_ids,
        retrieval_results=retrieval_results,
        ground_truths=ground_truths,
        supporting_titles=supporting_titles,
    )
    if not qrels:
        return {"recall_at_k": 0.0, "precision_at_k": 0.0, "ndcg_at_k": 0.0, "mrr": 0.0}

    try:
        from ranx import Qrels, Run, evaluate

        scores = evaluate(
            Qrels(qrels),
            Run(runs),
            metrics=[f"recall@{k}", f"precision@{k}", f"ndcg@{k}", f"mrr@{k}"],
        )
        return {
            "recall_at_k": float(scores[f"recall@{k}"]),
            "precision_at_k": float(scores[f"precision@{k}"]),
            "ndcg_at_k": float(scores[f"ndcg@{k}"]),
            "mrr": float(scores[f"mrr@{k}"]),
        }
    except Exception:
        return _evaluate_ir_fallback(qrels, runs, k)


def _build_qrels_and_run(
    question_ids: list[str],
    retrieval_results: list[list[dict]],
    ground_truths: list[str],
    supporting_titles: list[list[str]] | None,
) -> tuple[dict[str, dict[str, int]], dict[str, dict[str, float]]]:
    """Build qrels (ground truth) and run (ranked results) dicts for metric evaluation."""
    qrels: dict[str, dict[str, int]] = {}
    runs: dict[str, dict[str, float]] = {}

    for idx, qid in enumerate(question_ids):
        use_titles = bool(supporting_titles and supporting_titles[idx])
        relevant_titles = set(supporting_titles[idx]) if use_titles and supporting_titles else set()
        answer = ground_truths[idx].strip().lower()
        runs[qid] = {}
        qrels[qid] = {}

        for rank, item in enumerate(retrieval_results[idx]):
            title = str(item.get("title") or item.get("doc_id") or item.get("node_id") or "")
            doc_id = title if use_titles else str(item.get("node_id") or title or "")
            score = item.get("score")
            if not isinstance(score, int | float):
                score = 1.0 / (rank + 1)
            runs[qid][doc_id] = max(float(score), runs[qid].get(doc_id, float("-inf")))
            if use_titles and title in relevant_titles:
                qrels[qid][doc_id] = 1
            elif not use_titles and answer and answer in item.get("text", "").lower():
                qrels[qid][doc_id] = 1

        if not qrels[qid]:
            del qrels[qid]
            runs.pop(qid, None)
    return qrels, runs


def _evaluate_ir_fallback(
    qrels: dict[str, dict[str, int]],
    runs: dict[str, dict[str, float]],
    k: int,
) -> dict[str, float]:
    """Fallback IR metric computation when ranx is unavailable."""
    recalls = []
    precisions = []
    ndcgs = []
    mrrs = []
    for qid, relevant in qrels.items():
        ranked = [
            doc_id
            for doc_id, _ in sorted(
                runs.get(qid, {}).items(),
                key=lambda item: item[1],
                reverse=True,
            )[:k]
        ]
        relevant_ids = set(relevant)
        hits = [1 if doc_id in relevant_ids else 0 for doc_id in ranked]
        recalls.append(sum(hits) / max(len(relevant_ids), 1))
        precisions.append(sum(hits) / max(k, 1))
        ndcgs.append(_ndcg(hits, min(len(relevant_ids), k)))
        mrrs.append(_mrr(hits))
    return {
        "recall_at_k": _mean(recalls),
        "precision_at_k": _mean(precisions),
        "ndcg_at_k": _mean(ndcgs),
        "mrr": _mean(mrrs),
    }


def _ndcg(hits: list[int], ideal_hits: int) -> float:
    """Compute Normalized Discounted Cumulative Gain."""
    import math

    dcg = sum(hit / math.log2(rank + 2) for rank, hit in enumerate(hits))
    ideal = sum(1 / math.log2(rank + 2) for rank in range(ideal_hits))
    return dcg / ideal if ideal else 0.0


def _mrr(hits: list[int]) -> float:
    """Compute Mean Reciprocal Rank (1 / rank of first hit, or 0 if no hits)."""
    for rank, hit in enumerate(hits, start=1):
        if hit:
            return 1.0 / rank
    return 0.0


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0
