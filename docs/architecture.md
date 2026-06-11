# System Architecture

The Autonomous RAG Optimizer uses **LangGraph** to manage a complex cyclic state machine that proposes, tests, evaluates, and records different Retrieval-Augmented Generation (RAG) configurations.

## LangGraph Workflow Execution

The orchestration maps out three primary phases: System Initialization, the iterative Graph execution loop, and the internal operations of the Evaluator node.




## Key Workflow Highlights

1. **State Injection:** The system evaluates the baseline exactly once per code update, caching the results heavily to save time. This score acts as the target to beat for all subsequent iterations.
2. **Short-Circuiting Failures:** Nodes like `Validator`, `Deduplicator`, and `SmokeTest` act as inexpensive guardrails. If any fail, the graph skips the expensive `Indexer` and `Evaluator` nodes, immediately routing to `Recorder` to log the failure before passing context to the `Reflection` node.
3. **Evaluator Execution & Threading:** Inside the Evaluator node, `run_single_eval` delegates the synchronous RAGAS library to a separate background thread via `loop.run_in_executor`. `nest_asyncio` ensures that the thread can safely execute nested asynchronous API calls without clashing with the main thread's Windows I/O completion polling. Timeout tracking is natively handled within RAGAS configurations instead of using forceful `asyncio.wait_for` wrappers.
