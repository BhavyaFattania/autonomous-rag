from src.evaluator.ir_metrics import evaluate_ir_metrics


def test_ir_metrics_use_supporting_titles_when_present():
    scores = evaluate_ir_metrics(
        question_ids=["q1"],
        retrieval_results=[[
            {"node_id": "n1", "title": "Wrong", "score": 0.9, "text": "no"},
            {"node_id": "n2", "title": "Gold", "score": 0.8, "text": "answer"},
        ]],
        ground_truths=["answer"],
        supporting_titles=[["Gold"]],
        k=2,
    )

    assert scores["recall_at_k"] == 1.0
    assert scores["precision_at_k"] == 0.5
    assert 0.0 < scores["ndcg_at_k"] < 1.0
    assert scores["mrr"] == 0.5


def test_ir_metrics_fall_back_to_answer_containment():
    scores = evaluate_ir_metrics(
        question_ids=["q1"],
        retrieval_results=[[
            {"node_id": "n1", "title": "Any", "score": 0.9, "text": "contains Apalachees"},
            {"node_id": "n2", "title": "Other", "score": 0.8, "text": "wrong"},
        ]],
        ground_truths=["Apalachees"],
        supporting_titles=[[]],
        k=2,
    )

    assert scores["recall_at_k"] == 1.0
    assert scores["mrr"] == 1.0
