import asyncio
import json
from src.orchestrator.config_loader import load_baseline_config
from src.models.rag_config import RAGConfig
from src.rag_pipeline.pipeline import run_pipeline
from src.evaluator.ragas_runner import run_single_eval
from src.data.question_loader import load_eval_question_items
from src.storage.cost_tracker import initialize, get_total
from src.models.metrics import AggregatedMetrics
from dotenv import load_dotenv

load_dotenv()

async def main():
    initialize(hard_ceiling=10.0, warning_threshold=7.0)
    config_dict = load_baseline_config()
    config = RAGConfig(**config_dict)

    questions, ground_truths = load_eval_question_items(n=5) # use 5 for baseline quick test

    print(f"Running baseline config: {config_dict}")
    runs = []
    for i in range(3):
        answers, contexts, cost = await run_pipeline(config, questions)
        metrics = await run_single_eval(questions, answers, contexts, ground_truths)
        runs.append(metrics)
        print(f"Run {i+1} score: {metrics.weighted_score}")

    agg = AggregatedMetrics.from_runs(runs)

    with open("baseline_score.json", "w") as f:
        json.dump(agg.model_dump(), f, indent=2)

    print(f"Final baseline median score: {agg.median_weighted_score}")
    print(f"Total API cost: ${get_total()}")

if __name__ == "__main__":
    asyncio.run(main())
