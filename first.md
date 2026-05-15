# Autonomous RAG Optimizer — Master Implementation Specification
**Version:** 2.1 (Master Combined Document)
**Status:** Final — Ready for Autonomous Code Generation
**Overnight Budget Hard Ceiling:** $10.00 USD
**Date:** May 2026

> **How to read this document:** This is the authoritative single-source-of-truth combining v2.0 and v2.1. Where the two versions conflict, v2.1 always takes precedence. All model IDs, API call formats, and the OpenRouter client implementation are from v2.1. All structural sections (directory layout, Pydantic models, LangGraph graph, evaluator, indexer, storage, CLI, tests, phases) are from v2.0 with v2.1 overrides applied inline. Nothing has been omitted.

---

## Table of Contents

1. [Part 0 — Critical Pre-Read: What Was Wrong in v1](#part-0--critical-pre-read-what-was-wrong-in-v1)
2. [Part 1 — Project Overview](#part-1--project-overview-final-authoritative)
3. [Part 2 — Complete Directory Structure](#part-2--complete-directory-structure-authoritative)
4. [Part 3 — Configuration Files](#part-3--configuration-files-exact-content)
5. [Part 4 — Data Models (Pydantic)](#part-4--data-models-pydantic-complete)
6. [Part 5 — LangGraph Orchestration](#part-5--langgraph-orchestration)
7. [Part 6 — Scientist Node](#part-6--scientist-node-complete-prompt--parsing)
8. [Part 7 — Evaluator Node (RAGAS)](#part-7--evaluator-node-complete-ragas-integration)
9. [Part 8 — Indexer (Qdrant)](#part-8--indexer-qdrant-collection-per-embedding-model-strategy)
10. [Part 9 — Data Setup (HotpotQA)](#part-9--data-setup-complete-no-assumptions)
11. [Part 10 — Cost Tracking](#part-10--cost-tracking-budget-hard-stop)
12. [Part 11 — OpenRouter Client](#part-11--openrouter-client-complete-with-retry)
13. [Part 12 — Acceptance Node](#part-12--acceptance-node-complete-logic)
14. [Part 13 — Storage: SQLite Schema](#part-13--storage-sqlite-schema)
15. [Part 14 — CLI Entry Point](#part-14--cli-entry-point)
16. [Part 15 — Environment Setup](#part-15--environment-setup)
17. [Part 16 — Budget Analysis](#part-16--budget-analysis-v21-corrected)
18. [Part 17 — Test Specifications](#part-17--test-specifications)
19. [Part 18 — Implementation Order (Phases)](#part-18--implementation-order-strict-phases)
20. [Part 19 — Known Limitations and Non-Goals](#part-19--known-limitations-and-non-goals)
21. [Part 20 — Checklist for AI Code Agent](#part-20--checklist-for-ai-code-agent)

---

## Part 0 — Critical Pre-Read: What Was Wrong in v1

Before writing a single line of code, the AI code agent **MUST** understand why the previous design documents cannot be used as-is. The following flaws range from minor inconsistencies to fundamental architectural failures that would cause the system to fail at runtime.

---

### 0.1 Fatal Flaw: Package Versions Do Not Exist

The original spec pins these dependencies:

```toml
# THESE ARE WRONG — DO NOT USE
llamaindex = "^0.9.30"        # Package renamed; this import will fail
ragas = "^0.1.0"              # API completely changed in 0.2.x
langgraph = "^0.0.20"         # Ancient; state API changed in 0.1.x+
```

**Correct pinned versions for this project:**

```toml
llama-index-core = "0.12.5"
llama-index-vector-stores-qdrant = "0.4.3"
llama-index-embeddings-openai = "0.3.1"
llama-index-embeddings-cohere = "0.3.1"
llama-index-llms-openai = "0.3.9"
ragas = "0.2.9"
langgraph = "0.2.73"
langchain-core = "0.3.50"
```

**Import style that MUST be used throughout the codebase:**

```python
# CORRECT
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.qdrant import QdrantVectorStore
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall, context_precision
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

# WRONG (old API — will cause ImportError)
# from llama_index import VectorStoreIndex
# from ragas.metrics.critique import AspectCritique
```

---

### 0.2 Fatal Flaw: Model Names (v2.0) Were Incorrect — Superseded by v2.1

> ⚠️ **v2.1 Override:** The model table in v2.0 Section 0.2 used incorrect or outdated OpenRouter IDs (`deepseek/deepseek-r1`, `deepseek/deepseek-chat-v3-0324`). **These are replaced entirely by the v2.1 Model Stack in Part 3.** Do not use the v2.0 model identifiers anywhere in the codebase.

The v2.1 model stack (see [Part 3 — Model Stack](#31-model-stack-authoritative--v21)) uses the **DeepSeek V4 family** and **Qwen 3.5**, released April–February 2026. All model IDs are exact OpenRouter strings and must be used verbatim.

---

### 0.3 Fatal Flaw: "No Line Deletions" Rule Contradicts Unified Diff Format

The original spec stated: *"Diffs cannot delete lines."*

This is logically impossible. In unified diff format, changing `chunk_size=1024` to `chunk_size=512` looks like:

```diff
-CHUNK_SIZE = 1024
+CHUNK_SIZE = 512
```

The `-` line IS a deletion. You cannot change any existing value without a deletion.

**Resolution:** The "no deletions" rule is dropped entirely. The safety invariant it was trying to enforce is: *the agent may not delete entire functions, classes, or import blocks.* That is enforced differently (see Section 4.3).

---

### 0.4 Fatal Flaw: Re-indexing Cost is Completely Unaccounted For

When `chunk_size` or `embedding_model` changes, the entire document corpus must be re-chunked and re-embedded. The original cost model ignores this entirely.

**Impact:** Switching from `text-embedding-3-small` to `cohere/embed-english-v3.0` requires re-embedding all document chunks. If the HotpotQA supporting corpus has ~15,000 chunks, that is ~3M tokens of embedding calls per model switch.

**Resolution:** One dedicated Qdrant collection per `(embedding_model + chunk_size + chunk_overlap)` key. Collections are built once and reused. See Part 8 for the collection management strategy.

---

### 0.5 Fatal Flaw: t-test with n=2 Is Statistically Invalid

The spec runs evaluation twice and calls the result "statistically significant." A two-sample t-test with n=2 has zero statistical power.

**Resolution:** Minimum **3 evaluation runs** per experiment. Accept at n=3 if variance is low. See Section 6.2 for the revised acceptance criterion.

---

### 0.6 Architectural Flaw: FastAPI Is Not Needed in Phase 0–4

Adding a FastAPI server for control endpoints (`/pause`, `/resume`, `/stop`) adds port management complexity and a full HTTP server running overnight with no traffic.

**Resolution:** Replace FastAPI with a signal-based control mechanism. A `SIGTERM` handler pauses the loop. A `control.json` file in the run directory allows `pause=true`/`resume=true` without HTTP. FastAPI is deferred to Phase 5 only if a dashboard UI is needed.

---

### 0.7 Architectural Flaw: Docker-in-Docker Breaks on Hugging Face Spaces

The spec targeted "Hugging Face Spaces" for production but required Docker-in-Docker. HF Spaces does not provide Docker daemon access.

**Resolution:** For Phase 0–4, the sandbox runs as a subprocess in a restricted Python environment. Full Docker isolation is Phase 5 work. The system is developed locally first.

---

### 0.8 Design Gap: Baseline Config Is Never Defined

The system claims to optimize against a "baseline" but the baseline config values are never specified.

**The canonical baseline config (immutable starting point) — see Section 3.4.**

---

### 0.9 Design Gap: HotpotQA Setup Is Unexplained

The spec references HotpotQA but provides no instructions for downloading or formatting it. See Part 9 for the complete data pipeline.

---

### 0.10 Logic Flaw: Config Hash Collision "Append Random Suffix"

The spec said: *"If config hash collision → append random suffix, log warning."* This is wrong. A hash collision means the exact same config was proposed again. Appending a random suffix would test a different (invalid) config.

**Resolution:** **Reject the proposal** and ask the scientist for a genuinely different config.

---

### 0.11 Reasoning API Format (v2.0 Was Wrong) — v2.1 Correction

> ⚠️ **v2.1 Override:** v2.0 used a regex `<think>...</think>` strip approach. This is incorrect for the v2.1 model stack. OpenRouter returns reasoning content in a **separate `reasoning_details` array**. The `content` field already contains only the final answer. Do NOT use `strip_thinking_tags` regex anywhere. See Part 11 for the exact API format.

---

## Part 1 — Project Overview (Final, Authoritative)

### 1.1 What This System Does

A command-line Python process runs overnight (max 6 hours) and executes up to 20 RAG optimization experiments. Each experiment:

1. An LLM **scientist** reads the history of past experiments and proposes a new RAG configuration to test.
2. The configuration is **validated** and **deduplicated**.
3. If the configuration requires a different embedding model or chunk size, documents are **re-indexed** in a new Qdrant collection.
4. The modified RAG pipeline runs on **50 HotpotQA validation questions**.
5. **RAGAS evaluates** the output on 4 metrics.
6. This evaluation runs **3 times**. The median is used as the score.
7. If the median weighted score improves **≥3%** over the current best with acceptable variance, the config is accepted as the new best.
8. The experiment is **recorded to SQLite**.
9. At the end of the run, a **report is written**.

**What this system does NOT do:**
- It does NOT generate free-form Python code diffs. Config parameters live in a YAML file. The "coder" agent is eliminated in Phase 0–4 and replaced by direct config mutation.
- It does NOT run inside Docker in Phase 0–4.
- It does NOT require a FastAPI server to run.
- It does NOT require Telegram (a local log + report file is sufficient).

### 1.2 Why Config-First (No Code Diffs in Phase 0–4)

The original design has the scientist propose a config, a coder write a Python diff, git apply it, then evaluate. This chain has 6 failure points before evaluation even begins.

The insight: **all meaningful RAG optimizations in the defined search space are purely config changes.** `chunk_size`, `top_k`, `hybrid_alpha`, `embedding_model`, `reranker` — all of these are parameters loaded from `config/experiment_config.yaml`. No Python code needs to change.

Phase 0–4 therefore eliminates the coder agent, AST validator, git diff, and git branch management entirely. The scientist proposes a config JSON. The system writes it to `config/experiment_config.yaml`. The pipeline loads it. Done.

Code generation (for custom retrieval strategies) is Phase 5+ work with proper sandboxing.

---

## Part 2 — Complete Directory Structure (Authoritative)

Every file listed here **MUST** exist with this exact path. No additional files, no renamed files.

```
autonomous-rag-optimizer/
│
├── pyproject.toml                     # All dependencies, pinned exactly
├── .env.example                       # Template: OPENROUTER_API_KEY=, QDRANT_URL=, QDRANT_API_KEY=
├── .env                               # Real secrets — NEVER commit
├── .gitignore
├── README.md
│
├── config/
│   ├── baseline_config.yaml           # Immutable starting config (see Section 3.4)
│   ├── experiment_config.yaml         # Current experiment config (written by orchestrator)
│   ├── model_routing.yaml             # Which OpenRouter model for which task (see Section 3.2)
│   └── run_settings.yaml              # Max experiments, max hours, cost cap (see Section 3.3)
│
├── data/
│   ├── hotpotqa/
│   │   ├── setup_hotpotqa.py          # Download + preprocess script (run once)
│   │   ├── questions.jsonl            # 50 fixed validation questions (created by setup)
│   │   ├── gold_answers.jsonl         # Ground truth answers (created by setup)
│   │   ├── contexts.jsonl             # Supporting paragraphs (created by setup)
│   │   └── fixed_question_ids.json    # Frozen set of 50 IDs (see Section 9.2)
│   └── corpus/
│       └── hotpotqa_paragraphs.jsonl  # Flat corpus for indexing into Qdrant
│
├── src/
│   ├── __init__.py
│   │
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── state.py                   # WorkflowState TypedDict (see Section 5.1)
│   │   ├── graph.py                   # LangGraph graph definition (see Section 5.2)
│   │   └── config_loader.py           # Load/write/validate experiment_config.yaml
│   │
│   ├── scientist/
│   │   ├── __init__.py
│   │   ├── brain.py                   # Call DeepSeek V4 Pro to propose next config
│   │   ├── deduplicator.py            # SHA-256 hash check against SQLite
│   │   └── reflection.py             # Build reflection context from experiment history
│   │
│   ├── indexer/
│   │   ├── __init__.py
│   │   ├── collection_manager.py      # Qdrant collection-per-embedding-model strategy
│   │   └── chunker.py                 # Re-chunk corpus for a given chunk_size/overlap
│   │
│   ├── rag_pipeline/
│   │   ├── __init__.py
│   │   ├── retriever.py               # Hybrid retrieval (dense + BM25 + optional rerank)
│   │   ├── generator.py               # LLM answer generation via OpenRouter
│   │   ├── smoke_tester.py            # Smoke test node (Qwen3.5-Flash validator)
│   │   └── pipeline.py                # Entry point: config → List[answer]
│   │
│   ├── evaluator/
│   │   ├── __init__.py
│   │   ├── ragas_runner.py            # Run RAGAS evaluation on answer set
│   │   ├── metric_aggregator.py       # Run 3×, take median, compute variance
│   │   └── scorer.py                  # Compute weighted_score + acceptance decision
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── db.py                      # SQLite setup, migrations, connection pool
│   │   ├── experiment_log.py          # Insert/read ExperimentRecord
│   │   └── cost_tracker.py            # Track and enforce budget ceiling
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── experiment.py              # Pydantic: ExperimentRecord
│   │   ├── rag_config.py              # Pydantic: RAGConfig (validated config schema)
│   │   └── metrics.py                 # Pydantic: EvalResult, RunMetrics
│   │
│   ├── reporter/
│   │   ├── __init__.py
│   │   └── report_writer.py           # Generate overnight_run_report.md
│   │
│   └── utils/
│       ├── __init__.py
│       ├── openrouter.py              # Async OpenRouter client with retry + cost tracking
│       ├── logger.py                  # Structured JSON logging setup
│       └── hashing.py                 # SHA-256 config hash
│
├── prompts/
│   └── scientist_v1.txt               # Scientist system prompt (loaded from disk at runtime)
│
├── tests/
│   ├── conftest.py
│   ├── test_scientist.py
│   ├── test_deduplicator.py
│   ├── test_indexer.py
│   ├── test_rag_pipeline.py
│   ├── test_evaluator.py
│   ├── test_scorer.py
│   ├── test_cost_tracker.py
│   ├── test_storage.py
│   └── test_report_writer.py
│
├── scripts/
│   ├── setup_environment.sh           # Install deps, pull models, create .env
│   ├── run_overnight.py               # CLI entry point
│   └── reset_run.py                   # Wipe SQLite + experiment_config.yaml for fresh run
│
├── logs/                              # Runtime logs (gitignored)
│   └── .gitkeep
│
├── reports/                           # Generated reports (gitignored)
│   └── .gitkeep
│
└── experiments.sqlite                 # Persisted experiment log (gitignored)
```

---

## Part 3 — Configuration Files (Exact Content)

### 3.1 `pyproject.toml` (Complete, Exact)

```toml
[tool.poetry]
name = "autonomous-rag-optimizer"
version = "0.1.0"
description = "Overnight autonomous RAG hyperparameter optimization"
authors = ["Your Name"]
python = "^3.11"

[tool.poetry.dependencies]
python = "^3.11"

# LlamaIndex — modular (NOT the old monolithic llamaindex package)
llama-index-core = "0.12.5"
llama-index-vector-stores-qdrant = "0.4.3"
llama-index-embeddings-openai = "0.3.1"
llama-index-embeddings-cohere = "0.3.1"
llama-index-llms-openai = "0.3.9"
llama-index-postprocessor-cohere-rerank = "0.3.0"
llama-index-retrievers-bm25 = "0.4.1"

# Vector store
qdrant-client = "1.13.3"

# Evaluation
ragas = "0.2.9"
datasets = "3.3.2"

# Orchestration
langgraph = "0.2.73"
langchain-core = "0.3.50"
langchain-openai = "0.3.12"

# HTTP
httpx = "0.28.1"

# Config & validation
pydantic = "2.11.3"
pydantic-settings = "2.8.1"
python-dotenv = "1.1.0"
pyyaml = "6.0.2"

# Storage
aiosqlite = "0.21.0"

# Logging
structlog = "24.4.0"

# CLI
click = "8.1.8"

# Utilities
tenacity = "9.1.2"

[tool.poetry.dev-dependencies]
pytest = "8.3.5"
pytest-asyncio = "0.24.0"
pytest-mock = "3.14.0"
black = "24.10.0"
ruff = "0.8.6"
mypy = "1.13.0"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

---

### 3.2 Model Stack (Authoritative — v2.1)

> ⚠️ This section supersedes the model table in v2.0 entirely. Use **ONLY** the model IDs below. Do not use `deepseek/deepseek-r1` or `deepseek/deepseek-chat-v3-0324` anywhere in the codebase.

| Role | OpenRouter `model_id` | Reasoning Mode | Cost (in/out per 1M tokens) | Context |
|------|----------------------|----------------|-----------------------------|---------|
| **Scientist** (hypothesis) | `deepseek/deepseek-v4-pro` | `effort: "high"` | $0.435 / $0.87 | 1.05M |
| **Coder** (Phase 5+ only) | `deepseek/deepseek-v4-flash` | `effort: "high"` | $0.14 / $0.28 | 1.05M |
| **RAG Answer Gen** (primary) | `deepseek/deepseek-v4-flash:free` | none | $0 / $0 | 1.05M |
| **RAG Answer Gen** (fallback) | `deepseek/deepseek-v4-flash` | none | $0.14 / $0.28 | 1.05M |
| **RAGAS Judge** | `qwen/qwen3-30b-a3b` | none | $0.10 / $0.30 | 262K |
| **Smoke Test** | `qwen/qwen3.5-flash-02-23` | none | $0.065 / $0.26 | 1M |
| **Report Writer** | `deepseek/deepseek-v4-pro` | `effort: "high"` | $0.435 / $0.87 | 1.05M |

**Notes on model selection:**

**DeepSeek V4 Pro** (`deepseek/deepseek-v4-pro`): 1.6T total parameters, 49B activated. Released April 24, 2026. Supports reasoning efforts `high` (80% of max_tokens allocated to reasoning) and `xhigh` (95% of max_tokens). Used for scientist and report writer because the experiment hypothesis requires deep multi-step reasoning over experiment history.

**DeepSeek V4 Flash** (`deepseek/deepseek-v4-flash`): 284B total parameters, 13B activated. Same architecture as Pro, optimized for throughput. Also supports `high` and `xhigh` reasoning. Used for code writing (Phase 5+) with reasoning enabled for better code quality. Used for RAG generation **WITHOUT** reasoning (no reasoning token overhead needed for simple answer generation tasks).

**DeepSeek V4 Flash Free** (`deepseek/deepseek-v4-flash:free`): Same model as Flash but on the free tier. Used as the primary model for RAG answer generation — 3,000 calls per overnight run makes cost savings critical. The system automatically falls back to the paid Flash tier on HTTP 429 (rate limit).

**Qwen3-30B-A3B** (`qwen/qwen3-30b-a3b`): Used as RAGAS judge. Consistent rubric-following, cost-effective for the high call volume (up to 12,000 RAGAS judge calls per run).

**Qwen3.5-Flash** (`qwen/qwen3.5-flash-02-23`): Released February 2026. Fast, cheap ($0.065/M input), 1M context. Used as smoke test validator — runs 5 questions through the proposed pipeline to verify it returns coherent results before full evaluation.

---

### 3.3 `config/model_routing.yaml` (Complete, Exact — v2.1)

> ⚠️ This file replaces the v2.0 version entirely. All `model_id` values are exact OpenRouter model strings. Do not modify.

```yaml
# config/model_routing.yaml
# All model_id values are exact OpenRouter model strings. Do not modify.

models:

  scientist:
    model_id: "deepseek/deepseek-v4-pro"
    reasoning_effort: "high"
    # When reasoning_effort is set, do NOT include temperature/top_p in the request.
    # Use max_tokens: 4096. Reasoning budget will be ~3276 tokens (80% of 4096).
    max_tokens: 4096
    # Response parsing: use data["choices"][0]["message"]["content"] for the JSON answer.
    # Do NOT strip <think> tags — they will not appear in content.

  coder:
    # Phase 5+ only. Not used in Phase 0–4.
    model_id: "deepseek/deepseek-v4-flash"
    reasoning_effort: "high"
    max_tokens: 4096

  rag_generator_primary:
    model_id: "deepseek/deepseek-v4-flash:free"
    reasoning_effort: null        # No reasoning for generation tasks
    temperature: 0.1
    max_tokens: 512
    # Fallback triggered on HTTP 429 (rate limit)

  rag_generator_fallback:
    model_id: "deepseek/deepseek-v4-flash"
    reasoning_effort: null
    temperature: 0.1
    max_tokens: 512

  ragas_judge:
    model_id: "qwen/qwen3-30b-a3b"
    reasoning_effort: null
    temperature: 0.0
    max_tokens: 256

  smoke_tester:
    model_id: "qwen/qwen3.5-flash-02-23"
    reasoning_effort: null
    temperature: 0.1
    max_tokens: 256

  report_writer:
    model_id: "deepseek/deepseek-v4-pro"
    reasoning_effort: "high"
    max_tokens: 6144
```

---

### 3.4 `config/run_settings.yaml` (Complete, Exact)

```yaml
# Runtime constraints for an overnight run.
run:
  max_experiments: 20
  max_hours: 6
  cost_hard_ceiling_usd: 10.00      # HARD STOP. Never exceed this. Kill loop immediately.
  cost_warning_threshold_usd: 7.00  # Log WARNING but continue.
  consecutive_failure_limit: 3       # Pause loop after N consecutive failures.
  random_seed: 42

evaluation:
  n_eval_runs: 3                    # Number of evaluation runs per experiment (minimum 3).
  n_questions: 50                   # Questions per evaluation run.
  smoke_test_n_questions: 5         # Questions for smoke test (subset of the 50).
  max_runtime_sec_per_eval: 900     # 15 minutes. Kill eval if exceeded.

acceptance:
  min_weighted_score_improvement: 0.03   # 3% relative improvement required.
  max_variance_between_runs: 0.035       # Max std-dev across 3 runs.
  max_metric_regression: 0.02           # No single metric may fall by more than 2%.

explore_exploit:
  exploit_probability: 0.70
  explore_probability: 0.30

reflection:
  update_every_n_experiments: 3
  compact_every_n_experiments: 8
  max_history_tokens: 4000           # Truncate scientist context to this limit.
```

---

### 3.5 `config/baseline_config.yaml` (Complete, Exact, Immutable)

```yaml
# IMMUTABLE BASELINE — THE CODE AGENT MUST NEVER MODIFY THIS FILE.
# This is the starting configuration. The first experiment optimizes against this.
# The weighted_score for this config is established in Phase 0 and stored in SQLite.

chunk_size: 1024
chunk_overlap: 200
top_k: 5
hybrid_alpha: 0.5
embedding_model: "text-embedding-3-small"
reranker: null
reranker_top_n: null
generator_model: "deepseek/deepseek-v4-flash"
```

> **Note:** The `generator_model` in the baseline config is `deepseek/deepseek-v4-flash` (v2.1 model stack). The scientist prompt locks this field and must not allow the LLM to change it.

---

## Part 4 — Data Models (Pydantic, Complete)

### 4.1 `src/models/rag_config.py`

```python
from typing import Optional, Literal
from pydantic import BaseModel, field_validator, model_validator

VALID_CHUNK_SIZES = [256, 512, 768, 1024, 1536, 2048]
VALID_CHUNK_OVERLAPS = [64, 128, 200, 256, 384]
VALID_EMBEDDING_MODELS = [
    "text-embedding-3-small",
    "text-embedding-3-large",
    "cohere/embed-english-v3.0",
]
VALID_RERANKERS = [None, "CohereRerank"]
VALID_GENERATOR_MODELS = [
    "deepseek/deepseek-v4-flash",
    "deepseek/deepseek-v4-flash:free",
    "deepseek/deepseek-v4-pro",
    "qwen/qwen3-30b-a3b",
]

class RAGConfig(BaseModel):
    chunk_size: int
    chunk_overlap: int
    top_k: int
    hybrid_alpha: float
    embedding_model: str
    reranker: Optional[str]
    reranker_top_n: Optional[int]
    generator_model: str

    @field_validator("chunk_size")
    @classmethod
    def validate_chunk_size(cls, v):
        if v not in VALID_CHUNK_SIZES:
            raise ValueError(f"chunk_size must be one of {VALID_CHUNK_SIZES}, got {v}")
        return v

    @field_validator("chunk_overlap")
    @classmethod
    def validate_chunk_overlap(cls, v):
        if v not in VALID_CHUNK_OVERLAPS:
            raise ValueError(f"chunk_overlap must be one of {VALID_CHUNK_OVERLAPS}, got {v}")
        return v

    @field_validator("top_k")
    @classmethod
    def validate_top_k(cls, v):
        if not (3 <= v <= 30):
            raise ValueError(f"top_k must be between 3 and 30, got {v}")
        return v

    @field_validator("hybrid_alpha")
    @classmethod
    def validate_hybrid_alpha(cls, v):
        # Round to 1 decimal place to prevent floating-point drift
        v = round(v, 1)
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"hybrid_alpha must be between 0.0 and 1.0, got {v}")
        return v

    @field_validator("embedding_model")
    @classmethod
    def validate_embedding_model(cls, v):
        if v not in VALID_EMBEDDING_MODELS:
            raise ValueError(f"embedding_model must be one of {VALID_EMBEDDING_MODELS}")
        return v

    @field_validator("reranker")
    @classmethod
    def validate_reranker(cls, v):
        if v not in VALID_RERANKERS:
            raise ValueError(f"reranker must be one of {VALID_RERANKERS}")
        return v

    @field_validator("generator_model")
    @classmethod
    def validate_generator_model(cls, v):
        if v not in VALID_GENERATOR_MODELS:
            raise ValueError(f"generator_model must be one of {VALID_GENERATOR_MODELS}")
        return v

    @model_validator(mode="after")
    def validate_reranker_top_n(self):
        if self.reranker is not None and self.reranker_top_n is None:
            raise ValueError("reranker_top_n must be set when reranker is not null")
        if self.reranker is None and self.reranker_top_n is not None:
            raise ValueError("reranker_top_n must be null when reranker is null")
        if self.reranker_top_n is not None and not (2 <= self.reranker_top_n <= 10):
            raise ValueError(f"reranker_top_n must be between 2 and 10")
        if self.reranker_top_n is not None and self.reranker_top_n >= self.top_k:
            raise ValueError(
                f"reranker_top_n ({self.reranker_top_n}) must be less than top_k ({self.top_k})"
            )
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                f"chunk_overlap ({self.chunk_overlap}) must be less than chunk_size ({self.chunk_size})"
            )
        return self
```

---

### 4.2 `src/models/metrics.py`

```python
from pydantic import BaseModel

class SingleRunMetrics(BaseModel):
    faithfulness: float
    answer_relevancy: float
    context_recall: float
    context_precision: float

    @property
    def weighted_score(self) -> float:
        return (
            self.answer_relevancy * 0.35
            + self.faithfulness * 0.30
            + self.context_recall * 0.20
            + self.context_precision * 0.15
        )

class AggregatedMetrics(BaseModel):
    run_1: SingleRunMetrics
    run_2: SingleRunMetrics
    run_3: SingleRunMetrics
    median_faithfulness: float
    median_answer_relevancy: float
    median_context_recall: float
    median_context_precision: float
    median_weighted_score: float
    std_dev_weighted_score: float   # Standard deviation across 3 runs (not variance)

    @classmethod
    def from_runs(cls, runs: list[SingleRunMetrics]) -> "AggregatedMetrics":
        import statistics
        assert len(runs) == 3, "Exactly 3 runs required"

        def _median(key):
            return statistics.median([getattr(r, key) for r in runs])

        scores = [r.weighted_score for r in runs]
        return cls(
            run_1=runs[0], run_2=runs[1], run_3=runs[2],
            median_faithfulness=_median("faithfulness"),
            median_answer_relevancy=_median("answer_relevancy"),
            median_context_recall=_median("context_recall"),
            median_context_precision=_median("context_precision"),
            median_weighted_score=statistics.median(scores),
            std_dev_weighted_score=statistics.stdev(scores),
        )
```

---

### 4.3 `src/models/experiment.py`

```python
from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel
from src.models.rag_config import RAGConfig
from src.models.metrics import AggregatedMetrics

ExperimentStatus = Literal[
    "PENDING", "RUNNING", "ACCEPTED", "REJECTED",
    "FAILED_SMOKE", "FAILED_TIMEOUT", "FAILED_DUPLICATE",
    "FAILED_VALIDATION", "FAILED_API_ERROR", "INTERRUPTED"
]

class ExperimentRecord(BaseModel):
    experiment_id: int
    experiment_uuid: str           # uuid4 string
    config: RAGConfig
    config_hash: str               # SHA-256 of sorted JSON config
    hypothesis: str                # Scientist's rationale (max 500 chars)
    reflection_summary: Optional[str]
    metrics: Optional[AggregatedMetrics]
    baseline_weighted_score: float  # What we were beating
    status: ExperimentStatus
    failure_reason: Optional[str]
    cost_usd: float                 # API cost for this experiment
    started_at: datetime
    finished_at: Optional[datetime]
    duration_sec: Optional[float]
```

---

## Part 5 — LangGraph Orchestration

### 5.1 `src/orchestrator/state.py` (Complete TypedDict)

```python
from typing import TypedDict, Optional
from src.models.rag_config import RAGConfig
from src.models.metrics import AggregatedMetrics

class WorkflowState(TypedDict):
    # Run-level identity
    run_id: str                         # UUID for this overnight run
    experiment_id: int                  # Auto-incrementing from SQLite
    experiment_uuid: str                # UUID for this specific experiment

    # Config tracking
    baseline_config: dict               # Serialized RAGConfig (dict form)
    current_best_config: dict           # The config achieving best score so far
    proposed_config: dict               # What the scientist just proposed (not yet validated)
    validated_config: dict              # After Pydantic validation passes

    # Scientist
    hypothesis: str
    reflection_summary: str             # Updated every 3 experiments

    # Evaluation
    eval_results: list[dict]            # List of SingleRunMetrics dicts (3 items after eval)
    aggregated_metrics: dict            # AggregatedMetrics dict
    current_best_weighted_score: float  # Score of current_best_config
    proposed_weighted_score: float      # Score of proposed config

    # Status
    status: str                         # Mirrors ExperimentStatus
    failure_reason: str                 # Empty string if no failure

    # Accounting
    experiment_cost_usd: float          # Cost of THIS experiment
    total_cost_usd: float               # Cumulative cost of all experiments
    experiments_completed: int
    experiments_accepted: int
    consecutive_failures: int

    # History (for scientist context)
    successful_patterns: list[str]      # Short descriptions of accepted configs
    failed_patterns: list[str]          # Short descriptions of rejected configs

    # Timing
    run_started_at: str                 # ISO datetime string
    experiment_started_at: str          # ISO datetime string
```

**State ownership rules (enforced by code review, not runtime):**

| Node | May Write To |
|------|-------------|
| `scientist_node` | `proposed_config`, `hypothesis` |
| `validator_node` | `validated_config`, `status`, `failure_reason` |
| `deduplicator_node` | `status`, `failure_reason` |
| `indexer_node` | `status`, `failure_reason`, `experiment_cost_usd` |
| `smoke_test_node` | `status`, `failure_reason` |
| `evaluator_node` | `eval_results`, `aggregated_metrics`, `proposed_weighted_score`, `experiment_cost_usd` |
| `acceptance_node` | `status`, `current_best_config`, `current_best_weighted_score` |
| `recorder_node` | `experiments_completed`, `experiments_accepted`, `consecutive_failures`, `total_cost_usd`, `successful_patterns`, `failed_patterns` |
| `reflection_node` | `reflection_summary` |
| `budget_guard_node` | `status` (can set to `"BUDGET_EXCEEDED"`) |

---

### 5.2 `src/orchestrator/graph.py` (Complete Node and Edge Definitions)

```python
"""
LangGraph graph definition for the RAG Optimizer.

Node execution order (linear — no parallelism in Phase 0–4):

  scientist → validator → deduplicator → budget_guard
        → indexer → smoke_test → evaluator → acceptance
        → recorder → reflection → [loop back to scientist | END]

Edge conditions:
  - validator:    if status == FAILED_VALIDATION → recorder (skip eval)
  - deduplicator: if status == FAILED_DUPLICATE  → recorder (skip eval)
  - budget_guard: if total_cost_usd >= ceiling   → END
  - indexer:      if status == FAILED_API_ERROR  → recorder
  - smoke_test:   if status == FAILED_SMOKE      → recorder
  - evaluator:    if status == FAILED_TIMEOUT or FAILED_API_ERROR → recorder
  - acceptance:   always → recorder
  - recorder:     if experiments_completed >= max_experiments → report_writer → END
  - recorder:     if consecutive_failures >= limit            → report_writer → END
  - recorder:     if elapsed_hours >= max_hours               → report_writer → END
  - recorder:     else → reflection → scientist (next loop)
  - reflection:   always → scientist
"""

import uuid
from datetime import datetime, timezone
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from src.orchestrator.state import WorkflowState


def build_graph(db_path: str) -> StateGraph:
    """
    Build and compile the LangGraph state machine.
    db_path: path to experiments.sqlite for checkpointing.
    """
    workflow = StateGraph(WorkflowState)

    # Add nodes (imports deferred to avoid circular imports at module load)
    from src.scientist.brain import scientist_node
    from src.orchestrator.validator import validator_node
    from src.scientist.deduplicator import deduplicator_node
    from src.orchestrator.budget_guard import budget_guard_node
    from src.indexer.collection_manager import indexer_node
    from src.rag_pipeline.smoke_tester import smoke_test_node
    from src.evaluator.ragas_runner import evaluator_node
    from src.evaluator.scorer import acceptance_node
    from src.storage.experiment_log import recorder_node
    from src.scientist.reflection import reflection_node
    from src.reporter.report_writer import report_writer_node

    workflow.add_node("scientist", scientist_node)
    workflow.add_node("validator", validator_node)
    workflow.add_node("deduplicator", deduplicator_node)
    workflow.add_node("budget_guard", budget_guard_node)
    workflow.add_node("indexer", indexer_node)
    workflow.add_node("smoke_test", smoke_test_node)
    workflow.add_node("evaluator", evaluator_node)
    workflow.add_node("acceptance", acceptance_node)
    workflow.add_node("recorder", recorder_node)
    workflow.add_node("reflection", reflection_node)
    workflow.add_node("report_writer", report_writer_node)

    # Entry point
    workflow.set_entry_point("scientist")

    # Linear edges
    workflow.add_edge("scientist", "validator")
    workflow.add_edge("acceptance", "recorder")
    workflow.add_edge("reflection", "scientist")

    # Conditional edges
    workflow.add_conditional_edges("validator",    _after_validator)
    workflow.add_conditional_edges("deduplicator", _after_deduplicator)
    workflow.add_conditional_edges("budget_guard", _after_budget_guard)
    workflow.add_conditional_edges("indexer",      _after_indexer)
    workflow.add_conditional_edges("smoke_test",   _after_smoke_test)
    workflow.add_conditional_edges("evaluator",    _after_evaluator)
    workflow.add_conditional_edges("recorder",     _after_recorder)
    workflow.add_conditional_edges("report_writer", lambda _: END)

    # Compile with SQLite checkpointing
    memory = SqliteSaver.from_conn_string(db_path)
    return workflow.compile(checkpointer=memory)


# ─── Routing functions ────────────────────────────────────────────────────────

def _after_validator(state: WorkflowState) -> str:
    if state["status"] == "FAILED_VALIDATION":
        return "recorder"
    return "deduplicator"

def _after_deduplicator(state: WorkflowState) -> str:
    if state["status"] == "FAILED_DUPLICATE":
        return "recorder"
    return "budget_guard"

def _after_budget_guard(state: WorkflowState) -> str:
    if state["status"] == "BUDGET_EXCEEDED":
        return "report_writer"
    return "indexer"

def _after_indexer(state: WorkflowState) -> str:
    if state["status"] in ("FAILED_API_ERROR", "FAILED_TIMEOUT"):
        return "recorder"
    return "smoke_test"

def _after_smoke_test(state: WorkflowState) -> str:
    if state["status"] == "FAILED_SMOKE":
        return "recorder"
    return "evaluator"

def _after_evaluator(state: WorkflowState) -> str:
    if state["status"] in ("FAILED_TIMEOUT", "FAILED_API_ERROR"):
        return "recorder"
    return "acceptance"

def _after_recorder(state: WorkflowState) -> str:
    from src.orchestrator.config_loader import load_run_settings
    settings = load_run_settings()

    if state["status"] == "BUDGET_EXCEEDED":
        return "report_writer"

    if state["experiments_completed"] >= settings["run"]["max_experiments"]:
        return "report_writer"

    if state["consecutive_failures"] >= settings["run"]["consecutive_failure_limit"]:
        return "report_writer"

    started = datetime.fromisoformat(state["run_started_at"])
    elapsed_hours = (datetime.now(timezone.utc) - started).total_seconds() / 3600
    if elapsed_hours >= settings["run"]["max_hours"]:
        return "report_writer"

    return "reflection"
```

---

## Part 6 — Scientist Node (Complete Prompt + Parsing)

### 6.1 Scientist System Prompt (`prompts/scientist_v1.txt`)

Store as `prompts/scientist_v1.txt`. **Loaded from disk at runtime — never hardcoded.**

```
You are an expert retrieval-augmented generation (RAG) systems researcher.
Your job is to propose the next configuration to test in an automated optimization loop.

You will receive:
1. The current best configuration (as JSON)
2. The current best weighted score
3. A history of all previous experiments (config + outcome + score)
4. A reflection summary of patterns observed so far
5. Whether to exploit (refine near current best) or explore (try something new)

You must respond with ONLY a valid JSON object. No preamble. No explanation after the JSON. No markdown code fences.

The JSON must have exactly these fields:
{
  "hypothesis": "<one sentence, max 120 characters, explaining WHY this config might improve the score>",
  "chunk_size": <integer, one of: 256, 512, 768, 1024, 1536, 2048>,
  "chunk_overlap": <integer, one of: 64, 128, 200, 256, 384>,
  "top_k": <integer, 3 to 30 inclusive>,
  "hybrid_alpha": <float, 0.0 to 1.0, step 0.1, e.g. 0.3 or 0.7>,
  "embedding_model": <one of: "text-embedding-3-small", "text-embedding-3-large", "cohere/embed-english-v3.0">,
  "reranker": <null, or "CohereRerank">,
  "reranker_top_n": <null if reranker is null; integer 2-10 if reranker is set; must be less than top_k>,
  "generator_model": "deepseek/deepseek-v4-flash"
}

Rules:
- chunk_overlap MUST be less than chunk_size.
- If reranker is not null, reranker_top_n must be set and must be less than top_k.
- If reranker is null, reranker_top_n must be null.
- generator_model must always be exactly "deepseek/deepseek-v4-flash". Do not change it.
- Do not propose a config identical to any in the experiment history.
- hybrid_alpha: 0.0 means pure BM25, 1.0 means pure dense retrieval.
```

---

### 6.2 `src/scientist/brain.py` (Complete — v2.1 API format)

> ⚠️ **v2.1 Change:** The `call_openrouter` signature now takes `reasoning_effort` instead of `temperature` when using DeepSeek V4 Pro. The response is the final answer directly — no `<think>` tag stripping.

```python
# src/scientist/brain.py

import json
from src.orchestrator.state import WorkflowState
from src.utils.openrouter import call_openrouter
from src.utils.logger import get_logger

log = get_logger("scientist")

async def scientist_node(state: WorkflowState) -> dict:
    """
    Calls the scientist LLM (DeepSeek V4 Pro with reasoning) to propose the next config.
    Returns only the fields this node owns: proposed_config, hypothesis.
    On any failure, sets status=FAILED_API_ERROR or FAILED_VALIDATION.
    """
    import random
    from src.orchestrator.config_loader import load_run_settings
    settings = load_run_settings()

    exploit = random.random() < settings["explore_exploit"]["exploit_probability"]
    prompt = _build_scientist_prompt(state, exploit)

    try:
        # v2.1: reasoning_effort="high", temperature=None (must be None when reasoning is set)
        raw_response = await call_openrouter(
            model_id="deepseek/deepseek-v4-pro",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            task="scientist",
            reasoning_effort="high",
            temperature=None,       # MUST be None when reasoning_effort is set
            fallback_model_id=None, # No fallback for scientist — V4 Pro is required
        )
    except Exception as e:
        log.error("scientist_llm_failed", error=str(e))
        return {"status": "FAILED_API_ERROR", "failure_reason": f"Scientist API call failed: {e}"}

    # v2.1: raw_response IS already the final answer.
    # OpenRouter puts reasoning in reasoning_details; content field is clean.
    # Do NOT strip <think> tags.
    cleaned = raw_response.strip()

    # Remove markdown code fences if the model added them despite instructions
    import re
    cleaned = re.sub(r"```(?:json)?", "", cleaned).strip().rstrip("`").strip()

    try:
        config_dict = json.loads(cleaned)
    except json.JSONDecodeError as e:
        log.warning("scientist_json_parse_failed", raw=cleaned[:200], error=str(e))
        return {"status": "FAILED_VALIDATION", "failure_reason": f"Scientist returned invalid JSON: {e}"}

    hypothesis = config_dict.pop("hypothesis", "")
    if len(hypothesis) > 500:
        hypothesis = hypothesis[:500]

    log.info("scientist_proposed", hypothesis=hypothesis, config=config_dict)

    return {
        "proposed_config": config_dict,
        "hypothesis": hypothesis,
        "status": "RUNNING",
    }


def _build_scientist_prompt(state: WorkflowState, exploit: bool) -> str:
    from pathlib import Path
    system_prompt = Path("prompts/scientist_v1.txt").read_text()

    history_lines = []
    for i, pattern in enumerate(state.get("successful_patterns", [])):
        history_lines.append(f"ACCEPTED[{i+1}]: {pattern}")
    for i, pattern in enumerate(state.get("failed_patterns", [])):
        history_lines.append(f"REJECTED[{i+1}]: {pattern}")

    mode = "EXPLOIT (refine near current best)" if exploit else "EXPLORE (try something new)"

    user_message = f"""
System instructions:
{system_prompt}

Current best config:
{json.dumps(state["current_best_config"], indent=2)}

Current best weighted score: {state["current_best_weighted_score"]:.4f}

Experiment history:
{chr(10).join(history_lines) if history_lines else "No experiments yet. Start from baseline."}

Reflection summary:
{state.get("reflection_summary", "No reflection yet.")}

Mode for this experiment: {mode}

Respond with ONLY the JSON object.
"""
    return user_message.strip()
```

---

## Part 7 — Evaluator Node (Complete RAGAS Integration)

### 7.1 RAGAS Setup for v0.2.x

RAGAS 0.2.x has a completely different API than 0.1.x. The following is the **only** correct way to use it.

```python
# src/evaluator/ragas_runner.py

import random
import asyncio
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall, context_precision
from ragas.llms import LangchainLLMWrapper
from langchain_openai import ChatOpenAI
from src.models.metrics import SingleRunMetrics
from src.utils.logger import get_logger

log = get_logger("evaluator")


def _build_ragas_llm() -> LangchainLLMWrapper:
    """
    RAGAS requires a LangChain-compatible LLM.
    We wrap the OpenRouter Qwen3-30B via LangChain's ChatOpenAI interface
    (OpenRouter is OpenAI-compatible).
    """
    import os
    llm = ChatOpenAI(
        model="qwen/qwen3-30b-a3b",
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        temperature=0.0,
        max_tokens=256,
    )
    return LangchainLLMWrapper(llm)


async def run_single_eval(
    questions: list[str],
    answers: list[str],
    contexts: list[list[str]],
    ground_truths: list[str],
) -> SingleRunMetrics:
    """
    Run one RAGAS evaluation pass.
    Returns SingleRunMetrics (mean across all questions).
    """
    assert len(questions) == len(answers) == len(contexts) == len(ground_truths)

    data = {
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    }
    dataset = Dataset.from_dict(data)
    ragas_llm = _build_ragas_llm()

    result = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
        llm=ragas_llm,
        raise_exceptions=False,        # Don't crash on single-question failures
    )

    df = result.to_pandas()

    return SingleRunMetrics(
        faithfulness=float(df["faithfulness"].mean()),
        answer_relevancy=float(df["answer_relevancy"].mean()),
        context_recall=float(df["context_recall"].mean()),
        context_precision=float(df["context_precision"].mean()),
    )
```

---

### 7.2 Evaluation Node (3 Runs, Median, Variance Check)

```python
# src/evaluator/ragas_runner.py (continued — evaluator_node)

async def evaluator_node(state: WorkflowState) -> dict:
    """
    Runs the full RAG pipeline and RAGAS evaluation 3 times.
    Returns eval_results, aggregated_metrics, proposed_weighted_score.
    """
    from src.orchestrator.config_loader import load_run_settings
    from src.models.rag_config import RAGConfig
    from src.models.metrics import AggregatedMetrics
    from src.rag_pipeline.pipeline import run_pipeline
    import asyncio

    settings = load_run_settings()
    config = RAGConfig(**state["validated_config"])

    questions, ground_truths = _load_eval_questions(
        n=settings["evaluation"]["n_questions"]
    )

    runs: list[SingleRunMetrics] = []
    cost_this_node = 0.0

    for run_num in range(1, 4):
        log.info("eval_run_starting", run=run_num, experiment_id=state["experiment_id"])
        try:
            answers, contexts, run_cost = await asyncio.wait_for(
                run_pipeline(config, questions),
                timeout=settings["evaluation"]["max_runtime_sec_per_eval"],
            )
            cost_this_node += run_cost
            metrics = await run_single_eval(questions, answers, contexts, ground_truths)
            runs.append(metrics)
            log.info("eval_run_complete", run=run_num, weighted_score=metrics.weighted_score)
        except asyncio.TimeoutError:
            log.error("eval_run_timeout", run=run_num)
            return {
                "status": "FAILED_TIMEOUT",
                "failure_reason": f"Eval run {run_num} timed out after {settings['evaluation']['max_runtime_sec_per_eval']}s",
                "experiment_cost_usd": cost_this_node,
            }
        except Exception as e:
            log.error("eval_run_error", run=run_num, error=str(e))
            return {
                "status": "FAILED_API_ERROR",
                "failure_reason": f"Eval run {run_num} failed: {e}",
                "experiment_cost_usd": cost_this_node,
            }

    aggregated = AggregatedMetrics.from_runs(runs)
    log.info(
        "eval_complete",
        median_weighted_score=aggregated.median_weighted_score,
        std_dev=aggregated.std_dev_weighted_score,
    )

    return {
        "eval_results": [r.model_dump() for r in runs],
        "aggregated_metrics": aggregated.model_dump(),
        "proposed_weighted_score": aggregated.median_weighted_score,
        "experiment_cost_usd": state.get("experiment_cost_usd", 0.0) + cost_this_node,
        "status": "RUNNING",
    }


def _load_eval_questions(n: int) -> tuple[list[str], list[str]]:
    """Load fixed evaluation questions from data/hotpotqa/questions.jsonl."""
    import json
    from pathlib import Path
    questions, ground_truths = [], []
    lines = Path("data/hotpotqa/questions.jsonl").read_text().strip().splitlines()
    for line in lines[:n]:
        item = json.loads(line)
        questions.append(item["question"])
        ground_truths.append(item["answer"])
    assert len(questions) == n, f"Expected {n} questions, got {len(questions)}"
    return questions, ground_truths
```

---

## Part 8 — Indexer (Qdrant Collection-Per-Embedding-Model Strategy)

### 8.1 Why One Collection Per Embedding Model

Qdrant stores vectors with a fixed dimension:
- `text-embedding-3-small` → 1536 dims
- `text-embedding-3-large` → 3072 dims
- `cohere/embed-english-v3.0` → 1024 dims

These cannot share a collection. Rebuilding takes 2–8 minutes and costs ~$0.10–0.50 per rebuild. By caching one collection per `(embedding_model + chunk_size + chunk_overlap)` key, we pay this cost at most once per configuration.

### 8.2 Collection Naming Convention

```
rag_optimizer_{embedding_model_slug}_{chunk_size}_{chunk_overlap}
```

Examples:
```
rag_optimizer_te3small_1024_200
rag_optimizer_te3large_512_128
rag_optimizer_cohere_512_256
```

`embedding_model_slug` is the embedding model with `/`, `-`, `.` replaced by `_`.

### 8.3 `src/indexer/collection_manager.py` (Complete)

```python
# src/indexer/collection_manager.py

import hashlib
import json
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams
from llama_index.core import VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core import StorageContext
from src.models.rag_config import RAGConfig
from src.utils.logger import get_logger

log = get_logger("indexer")

EMBEDDING_DIMS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "cohere/embed-english-v3.0": 1024,
}


def _collection_name(config: RAGConfig) -> str:
    slug = config.embedding_model.replace("/", "_").replace("-", "_").replace(".", "_")
    return f"rag_optimizer_{slug}_{config.chunk_size}_{config.chunk_overlap}"


async def get_or_build_collection(config: RAGConfig) -> str:
    """
    Returns the Qdrant collection name for this config.
    If the collection doesn't exist, builds it (chunks corpus, embeds, upserts).
    """
    import os
    client = AsyncQdrantClient(
        url=os.environ["QDRANT_URL"],
        api_key=os.environ.get("QDRANT_API_KEY"),
    )
    collection_name = _collection_name(config)

    existing = [c.name for c in (await client.get_collections()).collections]
    if collection_name in existing:
        count = await client.count(collection_name)
        if count.count > 0:
            log.info("collection_cache_hit", collection=collection_name, vectors=count.count)
            return collection_name
        log.warning("collection_exists_but_empty", collection=collection_name)

    log.info("building_collection", collection=collection_name)
    await _build_collection(client, config, collection_name)
    return collection_name


async def _build_collection(client: AsyncQdrantClient, config: RAGConfig, collection_name: str):
    """Build a new Qdrant collection for this (embedding_model, chunk_size, chunk_overlap)."""
    import os
    from llama_index.embeddings.openai import OpenAIEmbedding
    from llama_index.embeddings.cohere import CohereEmbedding
    from pathlib import Path

    corpus_path = Path("data/corpus/hotpotqa_paragraphs.jsonl")
    assert corpus_path.exists(), (
        f"Corpus not found at {corpus_path}. Run data/hotpotqa/setup_hotpotqa.py first."
    )

    # Select embedding model
    if config.embedding_model in ("text-embedding-3-small", "text-embedding-3-large"):
        embed_model = OpenAIEmbedding(
            model=config.embedding_model,
            api_key=os.environ["OPENROUTER_API_KEY"],
            api_base="https://openrouter.ai/api/v1",
        )
    elif config.embedding_model == "cohere/embed-english-v3.0":
        embed_model = CohereEmbedding(
            model_name="embed-english-v3.0",
            cohere_api_key=os.environ["COHERE_API_KEY"],
            input_type="search_document",
        )
    else:
        raise ValueError(f"Unknown embedding model: {config.embedding_model}")

    splitter = SentenceSplitter(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
    )

    dim = EMBEDDING_DIMS[config.embedding_model]
    await client.recreate_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )

    vector_store = QdrantVectorStore(
        collection_name=collection_name,
        client=client,
    )
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    docs = _load_corpus_as_documents(corpus_path)

    VectorStoreIndex.from_documents(
        docs,
        storage_context=storage_context,
        embed_model=embed_model,
        transformations=[splitter],
        show_progress=True,
    )
    log.info("collection_built", collection=collection_name)


def _load_corpus_as_documents(corpus_path):
    """Load JSONL corpus as LlamaIndex Document objects."""
    import json
    from llama_index.core import Document
    docs = []
    for line in corpus_path.read_text().strip().splitlines():
        item = json.loads(line)
        docs.append(Document(text=item["text"], metadata={"title": item["title"]}))
    return docs


async def indexer_node(state) -> dict:
    """
    Ensures the correct Qdrant collection exists for the validated config.
    """
    config = RAGConfig(**state["validated_config"])
    try:
        collection_name = await get_or_build_collection(config)
    except Exception as e:
        log.error("indexer_failed", error=str(e))
        return {"status": "FAILED_API_ERROR", "failure_reason": f"Indexer failed: {e}"}
    return {
        "status": "RUNNING",
        "validated_config": {**state["validated_config"], "_collection_name": collection_name},
    }
```

> **Note on `COHERE_API_KEY`:** If `cohere/embed-english-v3.0` is used, a separate `COHERE_API_KEY` environment variable is required. Add it to `.env.example` as: `COHERE_API_KEY=your_cohere_api_key_here`.

---

## Part 9 — Data Setup (Complete, No Assumptions)

### 9.1 `data/hotpotqa/setup_hotpotqa.py` (Run Once)

```python
"""
Run this ONCE to set up the HotpotQA evaluation data.
Usage: python data/hotpotqa/setup_hotpotqa.py
"""

import json
import random
from pathlib import Path

OUTPUT_DIR = Path("data/hotpotqa")
CORPUS_DIR = Path("data/corpus")
RANDOM_SEED = 42
N_QUESTIONS = 50


def main():
    from datasets import load_dataset

    print("Downloading HotpotQA validation split...")
    dataset = load_dataset("hotpot_qa", "fullwiki", split="validation", trust_remote_code=True)
    print(f"Total validation examples: {len(dataset)}")

    # Deterministic sample
    random.seed(RANDOM_SEED)
    indices = sorted(random.sample(range(len(dataset)), N_QUESTIONS))
    sampled = [dataset[i] for i in indices]

    # Save fixed IDs
    fixed_ids = [item["id"] for item in sampled]
    (OUTPUT_DIR / "fixed_question_ids.json").write_text(json.dumps(fixed_ids, indent=2))
    print(f"Saved {N_QUESTIONS} fixed question IDs.")

    # Save questions + answers
    questions, gold_answers = [], []
    for item in sampled:
        questions.append({"id": item["id"], "question": item["question"], "answer": item["answer"]})
        gold_answers.append({"id": item["id"], "answer": item["answer"]})

    with open(OUTPUT_DIR / "questions.jsonl", "w") as f:
        for q in questions:
            f.write(json.dumps(q) + "\n")

    with open(OUTPUT_DIR / "gold_answers.jsonl", "w") as f:
        for a in gold_answers:
            f.write(json.dumps(a) + "\n")

    print("Saved questions.jsonl and gold_answers.jsonl.")

    # Build flat corpus from supporting facts (use FULL dataset as knowledge corpus)
    print("Building corpus from supporting paragraphs...")
    CORPUS_DIR.mkdir(exist_ok=True)
    paragraphs = []
    seen_titles = set()
    for item in dataset:
        for title, sentences in zip(item["context"]["title"], item["context"]["sentences"]):
            if title not in seen_titles:
                seen_titles.add(title)
                text = " ".join(sentences)
                paragraphs.append({"title": title, "text": text})

    with open(CORPUS_DIR / "hotpotqa_paragraphs.jsonl", "w") as f:
        for p in paragraphs:
            f.write(json.dumps(p) + "\n")

    print(f"Corpus: {len(paragraphs)} unique paragraphs written to data/corpus/hotpotqa_paragraphs.jsonl")
    print("Setup complete.")


if __name__ == "__main__":
    main()
```

### 9.2 Fixed Question ID Rationale

The 50 question IDs are frozen at setup time using `RANDOM_SEED = 42`. All experiments use exactly the same 50 questions. This ensures metrics are comparable across experiments — the only variable is the RAG configuration, not the questions.

---

## Part 10 — Cost Tracking (Budget Hard Stop)

### 10.1 `src/storage/cost_tracker.py`

```python
"""
All API calls MUST go through src/utils/openrouter.py,
which calls add_cost() after every successful call.
"""

import threading
from src.utils.logger import get_logger

log = get_logger("cost_tracker")

_lock = threading.Lock()
_total_cost_usd: float = 0.0
_hard_ceiling: float = 10.00
_warning_threshold: float = 7.00


def initialize(hard_ceiling: float, warning_threshold: float):
    global _hard_ceiling, _warning_threshold, _total_cost_usd
    with _lock:
        _hard_ceiling = hard_ceiling
        _warning_threshold = warning_threshold
        _total_cost_usd = 0.0


def add_cost(usd: float) -> float:
    """Add cost and return new total. Raises BudgetExceededError if ceiling hit."""
    global _total_cost_usd
    with _lock:
        _total_cost_usd += usd
        total = _total_cost_usd
        if total >= _hard_ceiling:
            log.critical("budget_ceiling_hit", total=total, ceiling=_hard_ceiling)
            raise BudgetExceededError(
                f"Cost ${total:.4f} exceeds ceiling ${_hard_ceiling:.2f}. Stopping."
            )
        elif total >= _warning_threshold:
            log.warning("budget_warning", total=total, threshold=_warning_threshold)
        return total


def get_total() -> float:
    with _lock:
        return _total_cost_usd


class BudgetExceededError(Exception):
    pass
```

---

## Part 11 — OpenRouter Client (Complete, With Retry — v2.1)

> ⚠️ **This is the v2.1 implementation.** It replaces the v2.0 version entirely. Key changes:
> 1. Reasoning parameter injected correctly via `"reasoning": {"effort": ...}`.
> 2. Temperature/sampling params suppressed when reasoning is active.
> 3. Free tier fallback logic for RAG generation (HTTP 429 → fallback model).
> 4. Response parsed from the `content` field only — no `<think>` tag stripping.

### 11.1 Reasoning API — Exact Format for OpenRouter

**Request format (with reasoning):**

```python
payload = {
    "model": "deepseek/deepseek-v4-pro",
    "messages": [{"role": "user", "content": "..."}],
    "temperature": 1.0,      # DeepSeek V4 thinking mode requires temperature=1.0.
                              # Do NOT set other values.
    "max_tokens": 4096,
    "reasoning": {
        "effort": "high"     # Allocates ~80% of max_tokens to reasoning budget
    }
}
```

> **Critical constraint:** When `reasoning.effort` is set, DeepSeek V4 models do NOT support `temperature`, `top_p`, `presence_penalty`, or `frequency_penalty`. Setting them will not cause an error but will have no effect. When `reasoning` is present in the payload, omit all sampling parameters except `max_tokens`.

**Response parsing (with reasoning):**

```python
data = response.json()

# The final answer is ALWAYS in data["choices"][0]["message"]["content"]
# The thinking trace is in data["choices"][0]["message"]["reasoning_details"] (list)
# Do NOT use regex to strip <think> tags. Use the content field directly.

final_answer = data["choices"][0]["message"]["content"]

# Optional: access thinking trace for debugging
reasoning_details = data["choices"][0]["message"].get("reasoning_details", [])
thinking_text = ""
for block in reasoning_details:
    if block.get("type") == "thinking":
        thinking_text += block.get("thinking", "")
```

**Request format (without reasoning — RAG gen and RAGAS judge):**

```python
payload = {
    "model": "deepseek/deepseek-v4-flash:free",   # or qwen/qwen3-30b-a3b
    "messages": [{"role": "user", "content": "..."}],
    "temperature": 0.1,
    "max_tokens": 512,
    # No "reasoning" key at all — omit it entirely
}
```

---

### 11.2 `src/utils/openrouter.py` (Complete — v2.1)

```python
# src/utils/openrouter.py

import os
import asyncio
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.storage.cost_tracker import add_cost, BudgetExceededError
from src.utils.logger import get_logger

log = get_logger("openrouter")

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
RETRYABLE_STATUS_CODES = {500, 502, 503, 504}
NON_RETRYABLE_STATUS_CODES = {400, 401, 403, 422}

# Token pricing per 1M tokens: (input_price, output_price)
MODEL_PRICING = {
    "deepseek/deepseek-v4-pro":         (0.435, 0.870),
    "deepseek/deepseek-v4-flash":       (0.140, 0.280),
    "deepseek/deepseek-v4-flash:free":  (0.000, 0.000),
    "qwen/qwen3-30b-a3b":              (0.100, 0.300),
    "qwen/qwen3.5-flash-02-23":        (0.065, 0.260),
}


class OpenRouterError(Exception):
    pass

class OpenRouterRateLimitError(OpenRouterError):
    """Raised specifically on HTTP 429 so callers can switch to fallback model."""
    pass

class OpenRouterNonRetryableError(OpenRouterError):
    pass


def compute_cost(model_id: str, prompt_tokens: int, completion_tokens: int) -> float:
    price_in, price_out = MODEL_PRICING.get(model_id, (0.0, 0.0))
    return (
        (prompt_tokens / 1_000_000) * price_in
        + (completion_tokens / 1_000_000) * price_out
    )


def _build_payload(
    model_id: str,
    messages: list[dict],
    max_tokens: int,
    reasoning_effort: str | None,
    temperature: float | None,
) -> dict:
    """
    Builds the JSON payload for an OpenRouter call.
    When reasoning_effort is set, omits ALL sampling parameters (temperature etc.)
    because DeepSeek V4 thinking mode does not support them.
    """
    payload: dict = {
        "model": model_id,
        "messages": messages,
        "max_tokens": max_tokens,
    }
    if reasoning_effort:
        # Reasoning mode: no sampling params allowed
        payload["reasoning"] = {"effort": reasoning_effort}
        # temperature, top_p, etc. must be absent
    else:
        # Normal mode: sampling params allowed
        if temperature is not None:
            payload["temperature"] = temperature
    return payload


@retry(
    retry=retry_if_exception_type(OpenRouterError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=16),
    reraise=True,
)
async def _call_once(
    model_id: str,
    messages: list[dict],
    max_tokens: int,
    reasoning_effort: str | None,
    temperature: float | None,
    task: str,
) -> str:
    """
    Single OpenRouter call with retry on transient errors.
    Raises OpenRouterRateLimitError on 429 (no retry — caller handles fallback).
    Returns the assistant content string.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise OpenRouterNonRetryableError("OPENROUTER_API_KEY not set.")

    payload = _build_payload(model_id, messages, max_tokens, reasoning_effort, temperature)

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/autonomous-rag-optimizer",
                "X-Title": "RAG Optimizer",
            },
            json=payload,
        )

    if response.status_code == 429:
        # Do NOT retry here — raise special exception so caller can use fallback model
        raise OpenRouterRateLimitError(f"Rate limit on {model_id}")

    if response.status_code in NON_RETRYABLE_STATUS_CODES:
        raise OpenRouterNonRetryableError(f"HTTP {response.status_code}: {response.text[:300]}")

    if response.status_code in RETRYABLE_STATUS_CODES:
        raise OpenRouterError(f"HTTP {response.status_code}: {response.text[:300]}")

    if response.status_code != 200:
        raise OpenRouterError(f"HTTP {response.status_code}: {response.text[:300]}")

    data = response.json()

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise OpenRouterError(f"Unexpected response shape: {e}")

    # Track cost
    usage = data.get("usage", {})
    cost = compute_cost(
        model_id,
        usage.get("prompt_tokens", 0),
        usage.get("completion_tokens", 0),
    )
    add_cost(cost)  # Raises BudgetExceededError if ceiling hit

    log.debug(
        "openrouter_call_complete",
        model=model_id,
        task=task,
        prompt_tokens=usage.get("prompt_tokens"),
        completion_tokens=usage.get("completion_tokens"),
        cost_usd=round(cost, 6),
    )

    return content


async def call_openrouter(
    model_id: str,
    messages: list[dict],
    max_tokens: int,
    task: str,
    reasoning_effort: str | None = None,
    temperature: float | None = 0.1,
    fallback_model_id: str | None = None,
) -> str:
    """
    Public entry point for all OpenRouter calls.
    If model_id gets a 429 AND fallback_model_id is provided, retries with fallback.
    BudgetExceededError propagates up — never caught here.
    """
    try:
        return await _call_once(
            model_id, messages, max_tokens, reasoning_effort, temperature, task
        )
    except OpenRouterRateLimitError:
        if fallback_model_id:
            log.warning("rate_limit_fallback", primary=model_id, fallback=fallback_model_id)
            return await _call_once(
                fallback_model_id, messages, max_tokens,
                reasoning_effort=None,  # fallback is always non-reasoning
                temperature=temperature,
                task=f"{task}_fallback",
            )
        raise
```

---

## Part 11 (continued) — RAG Generator and Smoke Test Node

### 11.3 `src/rag_pipeline/generator.py` (v2.1 — Free tier with fallback)

```python
# src/rag_pipeline/generator.py

from src.utils.openrouter import call_openrouter


async def generate_answer(question: str, contexts: list[str]) -> str:
    """
    Returns answer string.
    Uses free V4-Flash first; falls back to paid V4-Flash on rate limit.
    """
    context_text = "\n\n".join(f"[{i+1}] {c}" for i, c in enumerate(contexts))
    prompt = f"""Answer the following question using only the provided context.
If the context does not contain enough information, say "I don't know."

Context:
{context_text}

Question: {question}
Answer:"""

    answer = await call_openrouter(
        model_id="deepseek/deepseek-v4-flash:free",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=512,
        task="rag_generation",
        reasoning_effort=None,
        temperature=0.1,
        fallback_model_id="deepseek/deepseek-v4-flash",
    )
    return answer
```

---

### 11.4 `src/rag_pipeline/smoke_tester.py` (Complete — v2.1 Qwen3.5-Flash)

```python
# src/rag_pipeline/smoke_tester.py

import asyncio
from src.utils.openrouter import call_openrouter
from src.utils.logger import get_logger

log = get_logger("smoke_test")


async def smoke_test_node(state) -> dict:
    """
    Runs 5 questions through the proposed pipeline.
    Uses Qwen3.5-Flash to validate outputs are coherent (not empty, not errors).
    This is NOT a quality check — it only verifies the pipeline runs without crashing
    and returns non-empty, non-error strings.
    """
    from src.models.rag_config import RAGConfig
    from src.rag_pipeline.pipeline import run_pipeline

    config = RAGConfig(**state["validated_config"])
    questions, ground_truths = _load_smoke_questions(n=5)

    try:
        answers, contexts, cost = await asyncio.wait_for(
            run_pipeline(config, questions),
            timeout=120.0,   # 2-minute timeout for smoke test
        )
    except asyncio.TimeoutError:
        return {"status": "FAILED_SMOKE", "failure_reason": "Smoke test timed out after 120s"}
    except Exception as e:
        return {"status": "FAILED_SMOKE", "failure_reason": f"Pipeline error: {e}"}

    # Validate outputs using Qwen3.5-Flash
    for i, (q, a) in enumerate(zip(questions, answers)):
        if not a or len(a.strip()) < 5:
            return {
                "status": "FAILED_SMOKE",
                "failure_reason": f"Question {i+1} returned empty answer: '{a}'"
            }

        validation_prompt = f"""Question: {q}
Answer: {a}

Is this answer a coherent English sentence that attempts to answer the question?
Respond with ONLY "YES" or "NO"."""

        verdict = await call_openrouter(
            model_id="qwen/qwen3.5-flash-02-23",
            messages=[{"role": "user", "content": validation_prompt}],
            max_tokens=5,
            task="smoke_test",
            reasoning_effort=None,
            temperature=0.0,
        )

        if verdict.strip().upper() not in ("YES", "YES."):
            return {
                "status": "FAILED_SMOKE",
                "failure_reason": f"Question {i+1} failed coherence check. Answer: '{a[:100]}'"
            }

    log.info("smoke_test_passed", n_questions=5)
    return {
        "status": "RUNNING",
        "experiment_cost_usd": state.get("experiment_cost_usd", 0.0) + cost,
    }


def _load_smoke_questions(n: int = 5) -> tuple[list[str], list[str]]:
    """Load first N questions from the fixed eval set."""
    import json
    from pathlib import Path
    questions, answers = [], []
    lines = Path("data/hotpotqa/questions.jsonl").read_text().strip().splitlines()
    for line in lines[:n]:
        item = json.loads(line)
        questions.append(item["question"])
        answers.append(item["answer"])
    return questions, answers
```

---

## Part 12 — Acceptance Node (Complete Logic)

```python
# src/evaluator/scorer.py

import statistics
from src.orchestrator.state import WorkflowState
from src.models.metrics import AggregatedMetrics, SingleRunMetrics
from src.utils.logger import get_logger
from src.orchestrator.config_loader import load_run_settings

log = get_logger("scorer")


def acceptance_node(state: WorkflowState) -> dict:
    """
    Determines if the proposed config should be accepted as the new best.
    Uses median across 3 runs (robust to outliers).
    Three checks: minimum improvement, variance, per-metric regression.
    """
    settings = load_run_settings()
    thresholds = settings["acceptance"]

    metrics = AggregatedMetrics(**state["aggregated_metrics"])
    baseline_score = state["current_best_weighted_score"]
    proposed_score = metrics.median_weighted_score

    # Check 1: Minimum relative improvement
    relative_improvement = (proposed_score - baseline_score) / max(baseline_score, 1e-6)
    if relative_improvement < thresholds["min_weighted_score_improvement"]:
        reason = (
            f"Insufficient improvement: {relative_improvement:.4f} < "
            f"{thresholds['min_weighted_score_improvement']} required. "
            f"Proposed={proposed_score:.4f}, Baseline={baseline_score:.4f}"
        )
        log.info("experiment_rejected", reason=reason)
        return {"status": "REJECTED", "failure_reason": reason}

    # Check 2: Variance across 3 runs
    if metrics.std_dev_weighted_score > thresholds["max_variance_between_runs"]:
        reason = (
            f"High variance: std_dev={metrics.std_dev_weighted_score:.4f} > "
            f"{thresholds['max_variance_between_runs']} threshold"
        )
        log.info("experiment_rejected", reason=reason)
        return {"status": "REJECTED", "failure_reason": reason}

    # Check 3: No single metric may regress by more than max_metric_regression
    best_metrics_dict = state.get("current_best_metrics", {})
    if best_metrics_dict:
        current_best_metrics = SingleRunMetrics(**best_metrics_dict)
        for metric_name in ("faithfulness", "answer_relevancy", "context_recall", "context_precision"):
            proposed_val = getattr(metrics, f"median_{metric_name}")
            best_val = getattr(current_best_metrics, metric_name)
            regression = best_val - proposed_val
            if regression > thresholds["max_metric_regression"]:
                reason = (
                    f"Metric regression on {metric_name}: dropped by {regression:.4f} "
                    f"(max allowed: {thresholds['max_metric_regression']})"
                )
                log.info("experiment_rejected", reason=reason)
                return {"status": "REJECTED", "failure_reason": reason}

    # All checks passed — accept
    log.info(
        "experiment_accepted",
        proposed_score=proposed_score,
        previous_best=baseline_score,
        relative_gain=relative_improvement,
    )
    return {
        "status": "ACCEPTED",
        "current_best_config": state["validated_config"].copy(),
        "current_best_weighted_score": proposed_score,
        "current_best_metrics": {
            "faithfulness": metrics.median_faithfulness,
            "answer_relevancy": metrics.median_answer_relevancy,
            "context_recall": metrics.median_context_recall,
            "context_precision": metrics.median_context_precision,
        },
        "failure_reason": "",
    }
```

---

## Part 13 — Storage: SQLite Schema

### 13.1 `src/storage/db.py`

```python
"""
SQLite schema. All tables are created on first run.
WAL mode is MANDATORY for safe async access.
"""

import aiosqlite

DB_PATH = "experiments.sqlite"

CREATE_EXPERIMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS experiments (
    experiment_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_uuid  TEXT NOT NULL UNIQUE,
    run_id           TEXT NOT NULL,
    config_hash      TEXT NOT NULL,
    config_json      TEXT NOT NULL,
    hypothesis       TEXT,
    status           TEXT NOT NULL,
    failure_reason   TEXT,
    metrics_json     TEXT,
    baseline_score   REAL,
    proposed_score   REAL,
    cost_usd         REAL DEFAULT 0.0,
    started_at       TEXT NOT NULL,
    finished_at      TEXT,
    duration_sec     REAL
)
"""

CREATE_CONFIG_HASHES_TABLE = """
CREATE TABLE IF NOT EXISTS config_hashes (
    config_hash  TEXT PRIMARY KEY,
    first_seen   TEXT NOT NULL
)
"""

CREATE_RUNS_TABLE = """
CREATE TABLE IF NOT EXISTS runs (
    run_id        TEXT PRIMARY KEY,
    started_at    TEXT NOT NULL,
    finished_at   TEXT,
    total_cost    REAL DEFAULT 0.0,
    n_experiments INTEGER DEFAULT 0,
    n_accepted    INTEGER DEFAULT 0,
    best_config   TEXT,
    best_score    REAL,
    status        TEXT
)
"""

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL;")  # MANDATORY
        await db.execute("PRAGMA foreign_keys=ON;")
        await db.execute(CREATE_EXPERIMENTS_TABLE)
        await db.execute(CREATE_CONFIG_HASHES_TABLE)
        await db.execute(CREATE_RUNS_TABLE)
        await db.commit()
```

---

## Part 14 — CLI Entry Point

### 14.1 `scripts/run_overnight.py`

```python
#!/usr/bin/env python3
"""
Entry point for an overnight run.

Usage:
    python scripts/run_overnight.py --max-exp 20 --max-hours 6
    python scripts/run_overnight.py --max-exp 4 --max-hours 2  # daytime test run
    python scripts/run_overnight.py --dry-run                   # validate env only

Signal handling:
    SIGTERM or Ctrl+C: gracefully pauses after current experiment completes.
    The SQLite checkpoint allows resuming with the same command.
"""

import asyncio
import signal
import sys
import uuid
import click
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

_stop_requested = False

def _handle_signal(sig, frame):
    global _stop_requested
    print(f"\n[SIGNAL] {sig} received. Will stop after current experiment completes.")
    _stop_requested = True

signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT, _handle_signal)


@click.command()
@click.option("--max-exp",   default=20,  type=int,   help="Max experiments to run")
@click.option("--max-hours", default=6.0, type=float, help="Max runtime in hours")
@click.option("--dry-run",   is_flag=True,             help="Validate environment, print config, exit")
@click.option("--resume",    is_flag=True,             help="Resume from last checkpoint")
def main(max_exp, max_hours, dry_run, resume):
    from src.storage.db import init_db
    from src.storage.cost_tracker import initialize as init_cost
    from src.orchestrator.graph import build_graph
    from src.orchestrator.config_loader import load_run_settings
    from src.utils.logger import setup_logging

    setup_logging()

    if dry_run:
        _validate_environment()
        return

    settings = load_run_settings()
    init_cost(
        hard_ceiling=settings["run"]["cost_hard_ceiling_usd"],
        warning_threshold=settings["run"]["cost_warning_threshold_usd"],
    )

    asyncio.run(_run(max_exp, max_hours, resume, settings))


async def _run(max_exp, max_hours, resume, settings):
    from src.storage.db import init_db
    from src.orchestrator.graph import build_graph
    from src.orchestrator.config_loader import load_baseline_config

    await init_db()

    run_id = str(uuid.uuid4())
    baseline = load_baseline_config()

    initial_state = {
        "run_id": run_id,
        "experiment_id": 0,
        "experiment_uuid": "",
        "baseline_config": baseline,
        "current_best_config": baseline,
        "proposed_config": {},
        "validated_config": {},
        "hypothesis": "",
        "reflection_summary": "",
        "eval_results": [],
        "aggregated_metrics": {},
        "current_best_weighted_score": 0.0,
        "proposed_weighted_score": 0.0,
        "status": "PENDING",
        "failure_reason": "",
        "experiment_cost_usd": 0.0,
        "total_cost_usd": 0.0,
        "experiments_completed": 0,
        "experiments_accepted": 0,
        "consecutive_failures": 0,
        "successful_patterns": [],
        "failed_patterns": [],
        "run_started_at": datetime.now(timezone.utc).isoformat(),
        "experiment_started_at": "",
    }

    settings["run"]["max_experiments"] = max_exp
    settings["run"]["max_hours"] = max_hours

    graph = build_graph("experiments.sqlite")
    config = {"configurable": {"thread_id": run_id}}

    async for event in graph.astream(initial_state, config=config):
        if _stop_requested:
            print("[STOP] User requested stop. Exiting after this node.")
            break
        _log_event(event)


def _validate_environment():
    import os
    required = ["OPENROUTER_API_KEY", "QDRANT_URL"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        print(f"[ERROR] Missing environment variables: {missing}")
        sys.exit(1)
    print("[OK] Environment variables present.")
    data_path = Path("data/hotpotqa/questions.jsonl")
    if not data_path.exists():
        print(f"[ERROR] {data_path} not found. Run: python data/hotpotqa/setup_hotpotqa.py")
        sys.exit(1)
    print("[OK] HotpotQA data present.")
    print("[OK] Dry run passed. Safe to run overnight.")


def _log_event(event: dict):
    for node_name, output in event.items():
        status = output.get("status", "?") if isinstance(output, dict) else "?"
        cost = output.get("total_cost_usd", 0.0) if isinstance(output, dict) else 0.0
        print(f"  [{node_name}] status={status} cumulative_cost=${cost:.4f}")


if __name__ == "__main__":
    main()
```

---

## Part 15 — Environment Setup

### 15.1 `.env.example`

```bash
# Copy to .env and fill in real values. NEVER commit .env to git.

# Required
OPENROUTER_API_KEY=your_openrouter_api_key_here
QDRANT_URL=http://localhost:6333

# Optional — required only if using cohere/embed-english-v3.0 embedding model
COHERE_API_KEY=your_cohere_api_key_here

# Optional — Qdrant cloud (leave blank for local Docker)
QDRANT_API_KEY=

# Optional — Telegram notifications
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

### 15.2 `scripts/setup_environment.sh`

```bash
#!/bin/bash
set -e

echo "=== RAG Optimizer Environment Setup ==="

# 1. Check Python version
python3 --version | grep -q "3.11" || (echo "ERROR: Python 3.11 required" && exit 1)
echo "[OK] Python 3.11"

# 2. Install Poetry if not present
command -v poetry &>/dev/null || pip install poetry==1.8.3
echo "[OK] Poetry"

# 3. Install dependencies
poetry install
echo "[OK] Dependencies installed"

# 4. Create .env if not exists
if [ ! -f .env ]; then
    cp .env.example .env
    echo "[INFO] .env created from .env.example. Fill in your API keys."
fi

# 5. Start Qdrant via Docker (local dev)
docker compose up -d qdrant
echo "[OK] Qdrant started"

# 6. Create required directories
mkdir -p data/hotpotqa data/corpus logs reports prompts
echo "[OK] Directories created"

echo ""
echo "Next steps:"
echo "  1. Fill in OPENROUTER_API_KEY in .env"
echo "  2. Run: python data/hotpotqa/setup_hotpotqa.py"
echo "  3. Run: python scripts/run_overnight.py --dry-run"
echo "  4. Run: python scripts/run_overnight.py --max-exp 3 --max-hours 1  (smoke test)"
```

### 15.3 `docker-compose.yml` (For Local Qdrant Only)

```yaml
version: "3.9"
services:
  qdrant:
    image: qdrant/qdrant:v1.13.3
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_storage:/qdrant/storage
    environment:
      - QDRANT__SERVICE__GRPC_PORT=6334

volumes:
  qdrant_storage:
```

---

## Part 16 — Budget Analysis (v2.1 Corrected)

> **v2.1 primary change:** RAG generation is now $0 for the primary free tier. The free tier will hit rate limits under sustained load, so ~30% of calls are assumed to fall back to the paid Flash tier.

### 16.1 v2.1 Cost Estimate (DeepSeek V4 Pricing)

| Component | Calls | Avg Tokens (in/out) | Model | Unit Cost | Total |
|-----------|-------|---------------------|-------|-----------|-------|
| RAG generation (70% free) | 2,100 | 2K / 400 | V4-Flash:free | $0 | $0.00 |
| RAG generation (30% paid fallback) | 900 | 2K / 400 | V4-Flash | ~$0.00039 | $0.35 |
| RAGAS judging (4 metrics × 3 runs × 50 Qs × 20 exp) | 12,000 | 700 / 100 | Qwen3-30B | $0.0000730 | $0.88 |
| Scientist — V4 Pro reasoning high | 20 | 6K in / 1K out | V4-Pro | $0.00549 | $0.11 |
| Smoke test — Qwen3.5-Flash | 20 | 500 / 200 | Qwen3.5-Flash | $0.000085 | $0.002 |
| Re-indexing embeddings (~8 rebuilds) | varies | ~3M tokens | OpenAI embed | ~$0.06 each | $0.48 |
| Context compaction — V4-Pro | 3 | 8K / 1K | V4-Pro | $0.00435 | $0.013 |
| Report writer — V4-Pro reasoning | 1 | 12K / 3K | V4-Pro | $0.00783 | $0.008 |
| **TOTAL EXPECTED** | | | | | **~$1.84** |
| **WORST CASE** (all fallback, max retries) | | | | | **~$6.20** |
| **HARD CEILING** | | | | | **$10.00** |

### 16.2 Cost Reduction Options

If budget is exceeded during testing:
1. Reduce `n_questions` to 30 (cuts RAGAS and RAG gen cost by 40%).
2. Do not reduce `n_eval_runs` below 3 (statistical minimum).
3. Avoid `text-embedding-3-large` and `cohere` embedding models in early experiments.

---

## Part 17 — Test Specifications

All external API calls must be mocked. Each test module must cover these cases at minimum.

### 17.1 `tests/test_scientist.py`
- `test_scientist_returns_valid_config` — Mock `call_openrouter` to return valid JSON. Assert `proposed_config` is a valid `RAGConfig`.
- `test_scientist_no_think_tags_needed` — v2.1: Mock returns a clean response with no `<think>` tags. Assert JSON parsing succeeds directly (no stripping step required).
- `test_scientist_handles_invalid_json` — Mock returns gibberish. Assert status is `FAILED_VALIDATION`.
- `test_scientist_hypothesis_truncated_at_500_chars` — Mock returns hypothesis of 600 chars. Assert it is truncated to 500.
- `test_scientist_uses_reasoning_effort` — Assert the `call_openrouter` call uses `reasoning_effort="high"` and `temperature=None`.

### 17.2 `tests/test_deduplicator.py`
- `test_new_config_passes` — Hash not in DB → returns `status=RUNNING`.
- `test_duplicate_config_rejected` — Hash already in DB → returns `status=FAILED_DUPLICATE`.
- `test_explicit_retest_passes` — If `explicit_retest=True` in config dict → passes despite duplicate.

### 17.3 `tests/test_scorer.py`
- `test_accepts_with_3pct_improvement` — Baseline=0.70, proposed=0.722 → ACCEPTED.
- `test_rejects_insufficient_improvement` — Baseline=0.70, proposed=0.71 → REJECTED.
- `test_rejects_high_variance` — std_dev=0.05 → REJECTED.
- `test_rejects_metric_regression` — Any single metric drops by >2% → REJECTED.

### 17.4 `tests/test_cost_tracker.py`
- `test_add_cost_accumulates` — Three calls of $1 each → total $3.
- `test_hard_ceiling_raises` — Total reaches $10 → `BudgetExceededError`.
- `test_warning_at_threshold` — Total reaches $7 → WARNING logged, no exception.

### 17.5 `tests/test_storage.py`
- `test_init_db_creates_tables` — Init → all 3 tables exist.
- `test_insert_and_read_experiment` — Insert record → read back → all fields match.
- `test_wal_mode_enabled` — Check `PRAGMA journal_mode` returns `wal`.

### 17.6 `tests/test_openrouter.py` (v2.1 additions)
- `test_reasoning_payload_omits_temperature` — When `reasoning_effort` is set, assert `temperature` is absent from the payload.
- `test_rate_limit_triggers_fallback` — Mock primary model to return HTTP 429. Assert fallback model is called.
- `test_free_tier_fallback_on_429` — Mock `deepseek/deepseek-v4-flash:free` with 429. Assert `deepseek/deepseek-v4-flash` is called next.
- `test_budget_exceeded_propagates` — Mock `add_cost` to raise `BudgetExceededError`. Assert it propagates uncaught.

### 17.7 `tests/test_smoke_tester.py`
- `test_smoke_passes_on_coherent_answers` — Mock pipeline returns valid answers, mock Qwen3.5-Flash returns "YES". Assert `status=RUNNING`.
- `test_smoke_fails_on_empty_answer` — Mock pipeline returns empty string for question 2. Assert `status=FAILED_SMOKE`.
- `test_smoke_fails_on_incoherent_answer` — Mock Qwen3.5-Flash returns "NO". Assert `status=FAILED_SMOKE`.
- `test_smoke_timeout` — Mock pipeline to sleep 200 seconds. Assert `status=FAILED_SMOKE` with timeout message.

---

## Part 18 — Implementation Order (Strict Phases)

The code agent **MUST** implement in this exact phase order. Do not skip ahead.

### Phase 0 — Environment + Data (Day 1)

**Goal:** Be able to run baseline evaluation before any agent is built.

1. `pyproject.toml` — exact dependencies from Section 3.1.
2. `.env.example` — from Section 15.1.
3. `docker-compose.yml` — from Section 15.3.
4. `scripts/setup_environment.sh` — from Section 15.2.
5. `data/hotpotqa/setup_hotpotqa.py` — from Part 9.
6. `src/models/rag_config.py` — from Section 4.1.
7. `src/models/metrics.py` — from Section 4.2.
8. `src/models/experiment.py` — from Section 4.3.
9. `src/storage/db.py` — from Part 13.
10. `src/storage/cost_tracker.py` — from Part 10.
11. `src/utils/openrouter.py` — from Part 11 (**v2.1 version**).
12. `src/utils/logger.py` — structlog JSON formatter, one `get_logger(name)` function.
13. `src/utils/hashing.py` — `sha256(json.dumps(config_dict, sort_keys=True).encode()).hexdigest()`.
14. `config/baseline_config.yaml` — from Section 3.5.
15. `config/run_settings.yaml` — from Section 3.4.
16. `config/model_routing.yaml` — from Section 3.3 (**v2.1 version**).

**Deliverable:** Run `python data/hotpotqa/setup_hotpotqa.py` successfully. Run `pytest tests/test_cost_tracker.py tests/test_storage.py` — all pass.

---

### Phase 1 — RAG Pipeline + Evaluator (Days 2–3)

**Goal:** Be able to score any config manually before the agent loop exists.

1. `src/indexer/collection_manager.py` — from Part 8.
2. `src/rag_pipeline/retriever.py` — hybrid BM25 + dense via LlamaIndex `QueryFusionRetriever`. Load from `validated_config`.
3. `src/rag_pipeline/generator.py` — from Section 11.3 (free tier + fallback).
4. `src/rag_pipeline/pipeline.py` — `run_pipeline(config, questions) → (answers, contexts, cost)`.
5. `src/evaluator/ragas_runner.py` — from Part 7.
6. `src/evaluator/scorer.py` — from Part 12.

**Deliverable:** Script `scripts/fetch_baseline.py` runs, uses `baseline_config.yaml`, scores it, prints all 4 RAGAS metrics. Writes `baseline_score.json`.

---

### Phase 2 — Scientist + Deduplicator (Day 4)

**Goal:** LLM proposes configs using DeepSeek V4 Pro with reasoning.

1. `prompts/scientist_v1.txt` — exact text from Section 6.1.
2. `src/scientist/brain.py` — from Section 6.2 (**v2.1 reasoning API**).
3. `src/scientist/deduplicator.py` — SHA-256 hash check against `config_hashes` table.
4. `src/scientist/reflection.py` — build reflection string from last N experiment records.

**Deliverable:** `pytest tests/test_scientist.py` — all pass (mocked), including `test_scientist_uses_reasoning_effort`.

---

### Phase 3 — Orchestrator (Days 5–6)

**Goal:** Full LangGraph loop.

1. `src/orchestrator/state.py` — from Section 5.1.
2. `src/orchestrator/graph.py` — from Section 5.2.
3. `src/orchestrator/config_loader.py` — `load_run_settings()`, `load_baseline_config()`, `write_experiment_config(config)`.
4. `src/orchestrator/validator.py` — Pydantic-validate `proposed_config` into `validated_config`.
5. `src/orchestrator/budget_guard.py` — check `total_cost_usd` vs ceiling.
6. `src/rag_pipeline/smoke_tester.py` — from Section 11.4 (Qwen3.5-Flash validator).
7. `src/storage/experiment_log.py` — `recorder_node` writes experiment to SQLite.
8. `src/reporter/report_writer.py` — reads all experiments from SQLite, calls V4 Pro to generate markdown report.
9. `scripts/run_overnight.py` — from Part 14.

**Deliverable:** `python scripts/run_overnight.py --max-exp 3 --max-hours 1` completes 3 experiments end-to-end. `reports/` directory contains a markdown report.

---

### Phase 4 — Hardening (Day 7)

**Goal:** Reliable overnight run.

1. Add `BM25Retriever` integration to `src/rag_pipeline/retriever.py`.
2. Add Cohere reranker to retriever via `llama-index-postprocessor-cohere-rerank`.
3. Run 20-experiment overnight test. Review report. Fix any issues.
4. All tests passing at >80% coverage.
5. Verify smoke test node correctly gates entry to evaluator node.

---

### Phase 5+ — Future Work

- Free-form code generation with AST validation and Docker sandbox.
- FastAPI control server (`/pause`, `/resume`, `/stop`).
- Telegram notifications.
- Deployment to Hugging Face Spaces (requires Docker daemon access).
- Multi-hop reasoning custom retrievers.

---

## Part 19 — Known Limitations and Non-Goals

| Item | Status | Notes |
|------|--------|-------|
| Code generation / free-form diffs | Not in Phase 0–4 | Deferred to Phase 5 with proper sandboxing |
| Docker sandbox | Not in Phase 0–4 | Phase 5 work; requires Docker daemon access |
| Telegram notifications | Optional | Implement only after core loop works |
| FastAPI control server | Not in Phase 0–4 | Signal handling is sufficient |
| Parallel experiments | Not in scope | Sequential only |
| Production on Hugging Face Spaces | Not in scope | HF Spaces doesn't expose Docker daemon |
| Multi-hop reasoning strategies (custom retrievers) | Phase 5+ | Requires code gen + sandboxing |
| Generalization to non-HotpotQA datasets | Phase 6+ | Requires dataset abstraction layer |

---

## Part 20 — Checklist for AI Code Agent

Before declaring any file complete, verify every item:

**Imports and packages:**
- [ ] All imports use the package names from `pyproject.toml` in Section 3.1.
- [ ] No file uses `import llamaindex` or `from llamaindex import` — the package is `llama_index.core`.
- [ ] No file uses `ragas.metrics.critique` or `ragas.evaluation` (old API). Only `ragas.evaluate` and `ragas.metrics.*`.

**Model IDs (v2.1):**
- [ ] No file references `deepseek/deepseek-r1` or `deepseek/deepseek-chat-v3-0324` (v2.0 model IDs — superseded).
- [ ] Scientist node uses `deepseek/deepseek-v4-pro` with `reasoning_effort="high"` and `temperature=None`.
- [ ] RAG generator uses `deepseek/deepseek-v4-flash:free` as primary with `deepseek/deepseek-v4-flash` as fallback.
- [ ] RAGAS judge uses `qwen/qwen3-30b-a3b`.
- [ ] Smoke test uses `qwen/qwen3.5-flash-02-23`.
- [ ] Report writer uses `deepseek/deepseek-v4-pro` with `reasoning_effort="high"`.

**Reasoning API (v2.1):**
- [ ] No file uses regex `<think>.*?</think>` stripping — this is the v2.0 wrong approach.
- [ ] When `reasoning_effort` is set, `temperature` is absent from the request payload.
- [ ] The `_build_payload` function in `openrouter.py` correctly omits all sampling params when `reasoning_effort` is set.
- [ ] Response content is parsed from `data["choices"][0]["message"]["content"]` only.

**Async and error handling:**
- [ ] Every `async` function that calls `call_openrouter` is called with `await`.
- [ ] `OpenRouterRateLimitError` (HTTP 429) triggers fallback model, not retry.
- [ ] `BudgetExceededError` propagates up and is caught in `budget_guard_node`.
- [ ] `SqliteSaver.from_conn_string` is called, not `SqliteSaver(conn_string)`.

**Config validation:**
- [ ] Every node returns only the fields it owns (see ownership table in Section 5.1).
- [ ] `chunk_overlap < chunk_size` is validated in `RAGConfig` and will raise at proposal time.
- [ ] `reranker_top_n < top_k` is validated in `RAGConfig`.
- [ ] `hybrid_alpha` is rounded to 1 decimal place to prevent floating-point drift.

**Data integrity:**
- [ ] The `fixed_question_ids.json` is used to load questions in `_load_eval_questions` — NOT a random sample.
- [ ] `cost_tracker.add_cost()` is called in `call_openrouter` after every successful API call.
- [ ] SQLite is opened with `PRAGMA journal_mode=WAL`.
- [ ] `.env` is never committed — `.gitignore` includes `.env`, `experiments.sqlite`, `logs/`, `reports/`.
- [ ] The `baseline_config.yaml` file is never overwritten by any node.
- [ ] `generator_model` in the scientist prompt is always `"deepseek/deepseek-v4-flash"`. The scientist is not allowed to change the generator.

**Structure:**
- [ ] `report_writer_node` is only called from `_after_recorder` condition — never directly.
- [ ] Smoke test node is placed between `indexer_node` and `evaluator_node` in the graph.
- [ ] `prompts/scientist_v1.txt` is loaded from disk at runtime, never hardcoded.

---

*End of Master Specification. This document is complete and self-contained. All sections from v2.0 are included with v2.1 overrides applied inline. No external references are required to implement this system.*