# Evaluator Component Architecture & Code Breakdown

The `src/evaluator` directory orchestrates the evaluation of RAG pipeline runs. It calculates information retrieval (IR) metrics (Recall, Precision, NDCG, MRR) and LLM-as-a-judge metrics (via the RAGAS framework), and includes decision nodes to accept or reject new configurations during optimization experiments.

---

## Package Exports: [__init__.py](file:///d:/Documents/python/new%20life/autonomous%20rag/autonomous-rag/src/evaluator/__init__.py)

Exposes the primary integration entrypoints for the evaluator package to be consumed by the rest of the application (e.g. workflows and CLI commands).

### Exported Symbols
* `evaluator_node` (from `eval_node.py`)
* `acceptance_node` (from `scorer.py`)
* `run_single_eval` (from `ragas_runner.py`)
* `evaluate_ir_metrics` (from `ir_metrics.py`)
* `build_ragas_llm`, `build_ragas_embeddings`, `build_ragas_metrics` (from `ragas_setup.py`)

---

## 1. Pipeline Orchestrator: [eval_node.py](file:///d:/Documents/python/new%20life/autonomous%20rag/autonomous-rag/src/evaluator/eval_node.py)

This file contains the high-level workflow node that coordinates RAG retrieval and metric evaluation across multiple validation runs.

### `evaluator_node`
* **Signature**: `async def evaluator_node(state: dict, settings: Settings, env: dict | None = None, model_routing: ModelRouting | None = None) -> dict`
* **Usecase**: Acts as a state graph node during automated RAG optimization. It generates state updates containing detailed metrics and cost summaries.
* **Who Calls It**: The global agentic search workflow orchestrator (such as LangGraph loop).
* **What It Does**:
  1. Determines if a full validation suite or a smaller validation subset should run based on the experiment iteration number.
  2. Loads evaluation questions, ground truths, and supporting reference titles.
  3. Executes the retrieval pipeline (`retrieve_results`) for each evaluation question under the proposed `RAGConfig`.
  4. Runs `run_single_eval` to calculate both IR and RAGAS metrics.
  5. Computes total evaluation API costs and aggregates metrics across all runs (e.g., calculating median scores).
  6. Returns state updates containing raw metrics, aggregated metrics, and final execution status.
* **Key Arguments**:
  * `state`: LangGraph state dictionary containing `"validated_config"`, `"experiments_completed"`, `"current_best_weighted_score"`, and `"experiment_cost_usd"`.
  * `settings`: Global configuration settings containing evaluation limits, tolerances, and worker pools.
  * `env`: OS/Environment variables passed to APIs.
  * `model_routing`: Rules mapping agents and evaluators to specific models.

---

## 2. IR Metrics Engine: [ir_metrics.py](file:///d:/Documents/python/new%20life/autonomous%20rag/autonomous-rag/src/evaluator/ir_metrics.py)

Responsible for measuring the quality of retrieved contexts against gold standard reference documents.

### `evaluate_ir_metrics`
* **Signature**: `def evaluate_ir_metrics(question_ids: list[str], retrieval_results: list[list[dict]], ground_truths: list[str], supporting_titles: list[list[str]] | None, k: int) -> dict[str, float]`
* **Usecase**: Performs quantitative evaluation of the retriever's performance.
* **Who Calls It**: `run_single_eval` (inside `ragas_runner.py`).
* **What It Does**: Parses retrieved contexts and matching reference ground truths, then uses the `ranx` library to calculate:
  - `recall_at_k`
  - `precision_at_k`
  - `ndcg_at_k`
  - `mrr`
  If `ranx` fails or is not installed, it seamlessly delegates to `_evaluate_ir_fallback`.

### `_build_qrels_and_run`
* **Signature**: `def _build_qrels_and_run(question_ids: list[str], retrieval_results: list[list[dict]], ground_truths: list[str], supporting_titles: list[list[str]] | None) -> tuple[dict[str, dict[str, int]], dict[str, dict[str, float]]]`
* **Usecase**: Helper function to align raw outputs into Standard IR evaluation formats.
* **Who Calls It**: `evaluate_ir_metrics`.
* **What It Does**: Converts list structures into relevance dictionary mapping queries to ground truth (`qrels`) and query rankings with scores (`runs`). Matches on document titles/nodes or falls back to verifying if the answer string is contained in the retrieved text.

### `_evaluate_ir_fallback`
* **Signature**: `def _evaluate_ir_fallback(qrels: dict, runs: dict, k: int) -> dict[str, float]`
* **Usecase**: Pure Python fallback computations for IR metrics when C-dependencies/Rust libraries (`ranx`) are missing.
* **Who Calls It**: `evaluate_ir_metrics` (upon library exception).

### Helper Metrics Functions
* `_ndcg(hits: list[int], ideal_hits: int) -> float`: Calculates Normalized Discounted Cumulative Gain.
* `_mrr(hits: list[int]) -> float`: Calculates Mean Reciprocal Rank.
* `_mean(values: list[float]) -> float`: Computes the simple arithmetic mean of a floating-point sequence.

---

## 3. RAGAS Execution Wrapper: [ragas_runner.py](file:///d:/Documents/python/new%20life/autonomous%20rag/autonomous-rag/src/evaluator/ragas_runner.py)

Manages the execution of heavy, LLM-as-a-judge evaluation frameworks (such as faithfulness and context relevancy).

### `run_single_eval`
* **Signature**: `async def run_single_eval(questions: list[str], answers: list[str] | None, contexts: list[list[str]], ground_truths: list[str], retrieval_results: list[list[dict]] | None, question_ids: list[str] | None, supporting_titles: list[list[str]] | None, run_ragas: bool, ragas_min_fast_score: float | None, timeout_sec: int, timeout_backoff_factor: float, max_timeout_sec: int, timeout_retries: int, metrics: list[str] | None, env: dict | None, judge_config: ModelConfig | str | None = None) -> SingleRunMetrics`
* **Usecase**: Runs standard IR metrics, then checks if it should proceed with expensive RAGAS metrics based on performance thresholds.
* **Who Calls It**: `evaluator_node` (in `eval_node.py`) and overnight evaluations or CLI scripts.
* **What It Does**:
  1. Computes local IR metrics instantly.
  2. Checks whether RAGAS evaluations are required (based on the `run_ragas` flag and competitiveness thresholds).
  3. Prepares datasets for RAGAS and builds RAGAS metric objects.
  4. Runs the RAGAS evaluation pipeline in a dedicated background worker thread using `loop.run_in_executor` to prevent blocking the main asyncio event loop on long I/O calls.
  5. Implements timeout retry handling with exponential backoff and worker adjustments.
  6. Collects, cleans, and averages scores into a unified `SingleRunMetrics` object.

### `_safe_mean`
* **Signature**: `def _safe_mean(df: pd.DataFrame, column: str) -> float`
* **Usecase**: Extracts average scores from pandas dataframes without crashing on missing data or NaN elements.
* **Who Calls It**: `run_single_eval`.

---

## 4. Setup & Configurations: [ragas_setup.py](file:///d:/Documents/python/new%20life/autonomous%20rag/autonomous-rag/src/evaluator/ragas_setup.py)

Prepares the backend wrappers, client models, and custom compatibility patches for RAGAS.

### `build_ragas_llm`
* **Signature**: `def build_ragas_llm(model_routing: ModelRouting | None = None, judge_config: ModelConfig | str | None = None, env=None, api_key: str | None = None) -> LangchainLLMWrapper`
* **Usecase**: Initializes a wrapper compatible with RAGAS that utilizes OpenRouter APIs for LLM-based evaluation.
* **Who Calls It**: `run_single_eval` in `ragas_runner.py`.
* **What It Does**: Loads the judge model details from environment settings, constructs a LangChain `ChatOpenAI` client pointing to OpenRouter, applies parsing patches, and returns a RAGAS-compatible LLM wrapper.

### `build_ragas_embeddings`
* **Signature**: `def build_ragas_embeddings(model_name: str, env=None, api_key: str | None = None) -> OpenAIEmbeddings`
* **Usecase**: Builds an embeddings client used by semantic metrics (e.g. answer relevancy).
* **Who Calls It**: `run_single_eval` in `ragas_runner.py`.

### `build_ragas_metrics`
* **Signature**: `def build_ragas_metrics(metric_names: list[str]) -> list[Metric]`
* **Usecase**: Maps list of string names to corresponding instantiated Ragas metric modules (`faithfulness`, `answer_relevancy`, `context_recall`, `context_precision`, `context_utilization`).
* **Who Calls It**: `run_single_eval` in `ragas_runner.py`.

### Helper Internal Functions
* `_build_openrouter_model_kwargs(judge_config: ModelConfig) -> dict`: Configures output formats (like `json_object`).
* `_build_openrouter_extra_body(judge_config: ModelConfig) -> dict`: Injects platform flags (e.g. excluding deep reasoning tokens to minimize latency).
* `_ragas_generation_finished(response: LLMResult) -> bool`: Standardizes verification checks to ensure the LLM-as-a-judge finished generating metrics properly and did not silently get cut off due to token limits.

---

## 5. Experiment Scorer & Gatekeeper: [scorer.py](file:///d:/Documents/python/new%20life/autonomous%20rag/autonomous-rag/src/evaluator/scorer.py)

Evaluates whether a new, proposed RAG configuration is safe, stable, and sufficiently better than the current baseline configuration.

### `acceptance_node`
* **Signature**: `def acceptance_node(state: dict, settings: Settings) -> dict`
* **Usecase**: Decision-making gatekeeper in automated optimization pipelines.
* **Who Calls It**: The LangGraph state graph executor at the end of an evaluation loop.
* **What It Does**:
  1. Extracts aggregated metrics of the proposed experiment run.
  2. Compares the median score of the proposed run to the current baseline score.
  3. Rejects runs where performance drops or remains static, unless the settings explicitly allow acceptance of minor improvements.
  4. Enforces a maximum variance threshold (`max_variance_between_runs`) across validation runs to prevent unstable configurations from being accepted.
  5. Enforces safety regression guards across all primary IR metrics (Recall, NDCG, MRR) to prevent RAGAS optimizations from degrading retrieval quality.
  6. Accepts the configuration if all criteria are satisfied.

### `_accept_best_config`
* **Signature**: `def _accept_best_config(state: dict, metrics: AggregatedMetrics, proposed_score: float, baseline_score: float, relative_improvement: float) -> dict`
* **Usecase**: Updates the internal state machine variables to declare a new champion configuration.
* **Who Calls It**: `acceptance_node`.
