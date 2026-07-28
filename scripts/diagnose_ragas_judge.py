"""One-shot diagnostic for the ragas-judge "API connection error".

Run:  poetry run python scripts/diagnose_ragas_judge.py

Isolates the four failure modes seen in experiments.sqlite history:
  1. 403 "Key limit exceeded"      -> OpenRouter account/key out of credit
  2. empty "Bearer " header        -> OPENROUTER_API_KEY missing/empty in env
  3. "no current event loop ..."   -> event-loop bug running ragas in a thread
  4. model/endpoint 4xx            -> judge model_id not served / bad request

Prints the FULL exception chain (the openai SDK hides the real error in
__cause__ and reports only a generic "Connection error.").
"""

import asyncio
import traceback

from dotenv import load_dotenv

load_dotenv()  # mirror scripts/run_overnight.py

from config.loader import load_env, load_model_routing  # noqa: E402
from datasets import Dataset  # noqa: E402
from ragas import evaluate as ragas_evaluate  # noqa: E402
from ragas.run_config import RunConfig  # noqa: E402
from src.evaluator.ragas_setup import (  # noqa: E402
    build_ragas_embeddings,
    build_ragas_llm,
    build_ragas_metrics,
)


def _dump(label, exc):
    print(f"\n{'=' * 70}\n{label}\n{'=' * 70}")
    if exc is None:
        print("  OK — succeeded, no exception")
        return
    print(f"  type : {type(exc).__module__}.{type(exc).__name__}")
    print(f"  msg  : {exc}")
    seen = exc
    depth = 0
    while (seen.__cause__ or seen.__context__) and depth < 6:
        seen = seen.__cause__ or seen.__context__
        depth += 1
        print(f"  cause[{depth}] : {type(seen).__module__}.{type(seen).__name__}: {seen}")
    print("  ---- traceback (most recent call last) ----")
    traceback.print_exception(type(exc), exc, exc.__traceback__)


def main():
    env = load_env()
    routing = load_model_routing()

    # --- 0) key sanity (no value printed) -----------------------------------
    key = (env or {}).get("OPENROUTER_API_KEY")
    print(f"OPENROUTER_API_KEY present : {key is not None}")
    print(f"OPENROUTER_API_KEY length  : {len(key) if key else 0}")
    print(f"judge model_id             : {routing.ragas_judge.model_id}")
    print(f"embedding model_id         : {routing.ragas_embedding_model.model_id}")

    # --- 1) direct judge chat call ------------------------------------------
    async def _judge_call():
        from langchain_core.prompt_values import StringPromptValue

        llm = build_ragas_llm(model_routing=routing, env=env)
        return await llm.generate_text(
            StringPromptValue(text="Reply with exactly: OK"), n=1, temperature=0.0
        )

    exc = None
    try:
        asyncio.run(_judge_call())
    except Exception as e:  # noqa: BLE001
        exc = e
    _dump("1) DIRECT judge chat call (gpt-oss-safeguard-20b)", exc)

    # --- 2) direct embedding call (only used by answer_relevancy) -----------
    async def _embed_call():
        emb = build_ragas_embeddings(model_routing=routing, env=env)
        return await emb.aembed_query("hello world")

    exc = None
    try:
        asyncio.run(_embed_call())
    except Exception as e:  # noqa: BLE001
        exc = e
    _dump("2) DIRECT embedding call (text-embedding-3-small via OpenRouter)", exc)

    # --- 3) full ragas evaluate through the production thread wrapper -------
    exc = None
    try:
        dataset = Dataset.from_dict(
            {
                "question": ["What is the capital of France?"],
                "answer": ["Paris"],
                "contexts": [["Paris is the capital of France."]],
                "ground_truth": ["Paris"],
            }
        )
        metrics = build_ragas_metrics(["context_precision", "context_recall"])
        llm = build_ragas_llm(model_routing=routing, env=env)
        cfg = RunConfig(timeout=60, max_retries=1, max_wait=5, max_workers=2)

        def _run(worker_loop):
            asyncio.set_event_loop(worker_loop)
            return ragas_evaluate(
                dataset=dataset,
                metrics=metrics,
                llm=llm,
                run_config=cfg,
                raise_exceptions=True,  # surface the real error instead of NaN
                show_progress=False,
                batch_size=8,
            )

        async def _driver():
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, _run, asyncio.new_event_loop())

        result = asyncio.run(_driver())
        print("\n3) ragas evaluate (production wrapper) RESULT:")
        print(result.to_pandas().to_string())
    except Exception as e:  # noqa: BLE001
        exc = e
        _dump("3) ragas evaluate through production thread wrapper", exc)


if __name__ == "__main__":
    main()
