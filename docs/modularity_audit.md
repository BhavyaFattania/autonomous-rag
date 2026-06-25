# Evidence-Based Modularity Audit: Autonomous RAG Optimizer

> **Date:** 2026-06-24
> **Scope:** Full repository — 52 source files across 10 modules, 12 test files, 3 configs, 1 prompt template
> **Method:** Static analysis of imports, responsibilities, function boundaries, and cross-file coupling

---

## 1. Repository Overview

### 1.1 Full Directory Tree

```
autonomous-rag/
├── config/
│   ├── baseline_config.yaml          ← Starting RAG config (immutable)
│   ├── model_routing.yaml            ← OpenRouter model strings per role
│   └── run_settings.yaml             ← Budget, eval, exploration settings
├── data/
│   ├── bm25/                         ← Pickled BM25 indexes (auto-generated)
│   ├── chroma/                       ← ChromaDB persistent store (auto-generated)
│   ├── corpus/hotpotqa_paragraphs.jsonl
│   ├── eval_cache/                   ← Baseline+experiment eval cache
│   ├── hotpotqa/questions.jsonl      ← Eval question-answer pairs
│   └── retrieval_cache/              ← Cached retrieval results per config
├── docs/
│   ├── architecture.md
│   ├── developer_guide.md
│   ├── goal.md
│   ├── overnight_execution_guide.md
│   ├── ruflo_agents.md
│   ├── ruflo_features.md
│   ├── scientist_io.md
│   └── sparc_skills.md
├── prompts/
│   └── scientist_v1.txt              ← LLM scientist system prompt (71 lines)
├── reports/
│   ├── overnight_run_report.md
│   └── score_over_experiments.png
├── scratch/
│   └── test_brain.py                 ← Ad-hoc scientist test, not part of test suite
├── scripts/
│   ├── run_overnight.py              ← PRIMARY ENTRY POINT (490 lines)
│   ├── fetch_baseline.py             ← Evaluate baseline once
│   ├── enrich_hotpotqa_questions.py  ← One-shot data enrichment
│   └── test_loop.py                  ← Event-loop test (trivial)
├── src/
│   ├── evaluator/                    ← Metric computation & acceptance
│   │   ├── ir_metrics.py             ← Precision/Recall/NDCG/MRR (pure)
│   │   ├── ragas_runner.py           ← RAGAS evaluation + LangGraph node (388 lines)
│   │   └── scorer.py                 ← Accept/reject decision logic
│   ├── indexer/                      ← Vector index & BM25 management
│   │   ├── collection_manager.py     ← ChromaDB + BM25 build/cache/indexer_node (317 lines)
│   │   └── parser_registry.py        ← LlamaIndex node parser factory
│   ├── models/                       ← Pydantic data models
│   │   ├── experiment.py             ← ExperimentRecord model
│   │   ├── metrics.py                ← SingleRunMetrics + AggregatedMetrics
│   │   └── rag_config.py             ← RAGConfig with field validators (179 lines)
│   ├── orchestrator/                 ← LangGraph state machine
│   │   ├── budget_guard.py           ← Cost-ceiling check
│   │   ├── config_loader.py          ← YAML file loading with LRU cache
│   │   ├── graph.py                  ← StateGraph builder + routing functions
│   │   ├── state.py                  ← WorkflowState TypedDict
│   │   └── validator.py              ← Config validation + search space checks
│   ├── rag_pipeline/                 ← Retrieval + generation
│   │   ├── generator.py              ← LLM answer generation
│   │   ├── openrouter_reranker.py    ← Cohere rerank via OpenRouter
│   │   ├── pipeline.py               ← Orchestration + caching (221 lines)
│   │   ├── retriever.py              ← ChromaDB/BM25/hybrid retrievers (235 lines)
│   │   └── smoke_tester.py           ← Quick retrieval sanity check
│   ├── reporter/
│   │   └── report_writer.py          ← Final markdown report
│   ├── scientist/                    ← Config proposal & reflection
│   │   ├── brain.py                  ← LLM scientist node (303 lines)
│   │   ├── candidates.py             ← Fallback/exploration/reranker candidates
│   │   ├── deduplicator.py           ← SQLite duplicate detection
│   │   └── reflection.py             ← LLM-based run reflection
│   ├── storage/                      ← Persistence layer
│   │   ├── cost_tracker.py           ← Global mutable cost singleton
│   │   ├── db.py                     ← SQLite schema + init
│   │   └── experiment_log.py         ← Experiment persistence + counters
│   └── utils/                        ← Shared infrastructure
│       ├── conversation_summary.py   ← Sliding-window LLM compression
│       ├── hashing.py                ← SHA-256 config hashing (7 lines)
│       ├── json_repair.py            ← RAGAS output parser monkey-patch
│       ├── logger.py                 ← structlog setup
│       ├── openrouter.py             ← OpenRouter HTTP client + pricing (205 lines)
│       └── openrouter_embedding.py   ← LlamaIndex BaseEmbedding adapter
├── tests/
│   ├── conftest.py
│   ├── test_brain.py
│   ├── test_cost_tracker.py
│   ├── test_deduplicator.py
│   ├── test_ir_metrics.py
│   ├── test_openrouter.py
│   ├── test_parser_registry.py
│   ├── test_rag_config_expansion.py
│   ├── test_ragas_runner_parser.py
│   ├── test_scorer.py
│   ├── test_search_space_constraints.py
│   └── test_storage.py
├── pyproject.toml
├── requirements.txt
├── docker-compose.yml               ← Empty stub (services: {})
├── AGENTS.md, CLAUDE.md, README.md
└── .env                             ← API keys (gitignored)
```

### 1.2 Execution Flow

```
scripts/run_overnight.py
  1. CLI parsing (click)
  2. Signal handling (SIGTERM/SIGINT → graceful stop)
  3. DB init (SQLite schema)
  4. Cost tracker init (global singleton)
  5. Baseline config load + optional eval
  6. Build LangGraph StateGraph
  7. astream loop: for each event → update state → display

LangGraph nodes (defined in src/orchestrator/graph.py):
  scientist  → validator → deduplicator → budget_guard
    → indexer → smoke_test → evaluator → acceptance → recorder
    → reflection → scientist (loop)
    → report_writer (END)
```

### 1.3 Major Subsystems

| Subsystem | Module | Responsibility |
|-----------|--------|----------------|
| Orchestration | `orchestrator/` | State machine, routing, validation, budget |
| Scientist | `scientist/` | LLM-driven config proposal, dedup, reflection |
| RAG Pipeline | `rag_pipeline/` | Retrieval, generation, smoke testing, reranking |
| Indexer | `indexer/` | ChromaDB + BM25 index building & caching |
| Evaluator | `evaluator/` | IR metrics, RAGAS evaluation, accept/reject |
| Storage | `storage/` | SQLite persistence, cost tracking |
| Data Models | `models/` | Pydantic schemas for config, metrics, experiments |
| Utilities | `utils/` | HTTP client, embeddings, hashing, logging, JSON repair |

---

## 2. Design-Level Modularity Analysis

### 2.1 Conceptual Architecture

**Rating: GOOD (7/10) — Clean layered structure on paper**

The architecture follows a clear pipeline pattern:

```
Entry Point
    ↓
Orchestrator (state machine + routing)
    ├── Scientist (propose)
    ├── Indexer (build)
    ├── Pipeline (run)
    ├── Evaluator (measure)
    ├── Scorer (decide)
    └── Storage (persist)
        ↑
    Config (loaded once, consumed everywhere)
```

The folder structure maps sensibly to responsibilities:
- `models/` → data shapes (clean)
- `utils/` → shared infra (loose but standard)
- `storage/` → persistence (reasonable)
- `orchestrator/` → workflow control (appropriate)

**Boundaries are conceptually correct:**
- Scientist proposes → Validator checks → Evaluator measures → Scorer accepts/rejects
- Pipeline is separate from evaluation
- Models are pure data objects
- Utils provide infra without business logic

### 2.2 Design Strengths

1. **LangGraph as state machine:** The linear node progression with conditional routing (`_after_validator`, `_after_deduplicator`, etc.) is well-suited for this pipeline.
2. **Separation of proposal from evaluation:** Scientist only proposes; Evaluator only measures; Scorer only decides.
3. **Config-driven settings:** `run_settings.yaml` centralizes 35+ tuning parameters.
4. **Model routing via YAML:** `model_routing.yaml` keeps LLM model strings out of code.
5. **Caching strategy:** Retrieval cache (`data/retrieval_cache/`), index cache (`data/chroma/`, `data/bm25/`), and eval cache (`data/eval_cache/`) reduce redundant work.
6. **Sliding-window history compression:** Prevents unbounded prompt growth across 40+ experiments.

### 2.3 Design Weaknesses

1. **No dependency injection layer:** Every node function is a top-level import in `graph.py`, hardcoding the wiring.
2. **Config is a global service:** `load_run_settings()` is called from 10+ files across all layers. No typed config object.
3. **No repository abstraction for storage:** SQLite is accessed directly from at least 4 files (brain.py, deduplicator.py, experiment_log.py, run_overnight.py).
4. **No abstract interfaces for vector store or LLM:** ChromaDB and OpenRouter are directly instantiated.
5. **Entry point is overloaded:** `run_overnight.py` handles CLI, display, state management, baseline eval, and final eval.

### 2.4 Design Score Rubric

| Criterion | Weight | Score | Evidence |
|-----------|--------|-------|----------|
| Folder structure | 20% | 8/10 | Clear mapping to responsibility areas; one ambiguous placement (config_loader in orchestrator/) |
| Layer separation | 25% | 7/10 | Clean conceptual layers; violated in practice (see §3) |
| Interface boundaries | 20% | 4/10 | No abstract interfaces; direct imports everywhere |
| Config management | 15% | 6/10 | Centralized YAML but no typed model; hardcoded paths |
| Extensibility | 20% | 6/10 | Adding new retriever node or evaluator requires changes in 4+ files |

**Design-level Score: 6.2/10** → **MODERATE**

---

## 3. Implementation-Level Modularity Analysis

### 3.1 Import Graph (Full Dependency Map)

#### 3.1.1 File Imports (src/ — internal dependencies only)

```
src/orchestrator/graph.py
  Internal: src.orchestrator.state, src.orchestrator.config_loader
  Deferred: src.scientist.brain, src.orchestrator.validator, src.scientist.deduplicator,
            src.orchestrator.budget_guard, src.indexer.collection_manager,
            src.rag_pipeline.smoke_tester, src.evaluator.ragas_runner,
            src.evaluator.scorer, src.storage.experiment_log, src.scientist.reflection,
            src.reporter.report_writer
  External: uuid, datetime, langgraph.graph, langgraph.checkpoint.base

src/scientist/brain.py
  Internal (top-level): src.utils.openrouter, src.utils.logger
  Internal (deferred):  src.orchestrator.config_loader, src.utils.conversation_summary,
                        src.scientist.candidates, src.models.rag_config, src.utils.hashing,
                        src.storage.db, src.indexer.collection_manager
  External: json, re, random, time, uuid, aiosqlite, pathlib, langfuse.decorators

src/scientist/candidates.py
  Internal (top-level): json (stdlib only)
  Internal (deferred):  src.orchestrator.config_loader, src.indexer.collection_manager,
                        src.models.rag_config
  External: none

src/scientist/deduplicator.py
  Internal (top-level): src.storage.db, src.utils.logger
  Internal (deferred):  src.utils.hashing, datetime
  External: aiosqlite, json

src/scientist/reflection.py
  Internal (top-level): src.utils.logger, src.utils.openrouter
  Internal (deferred):  src.orchestrator.config_loader, langfuse.decorators
  External: none

src/orchestrator/config_loader.py
  Internal (top-level): src.models.rag_config
  External: yaml, functools

src/orchestrator/state.py
  Internal: none
  External: typing

src/orchestrator/validator.py
  Internal (top-level): src.models.rag_config
  Internal (deferred):  src.orchestrator.config_loader, src.indexer.collection_manager
  External: os

src/orchestrator/budget_guard.py
  Internal (top-level): src.storage.cost_tracker, src.orchestrator.config_loader
  External: none

src/indexer/collection_manager.py
  Internal (top-level): src.indexer.parser_registry, src.models.rag_config, src.utils.logger
  Internal (deferred):  src.orchestrator.config_loader, src.utils.openrouter_embedding
  External: json, pickle, warnings, pathlib, chromadb,
            llama_index.core, llama_index.vector_stores.chroma

src/indexer/parser_registry.py
  Internal (top-level): src.models.rag_config
  External: llama_index.core.node_parser

src/rag_pipeline/pipeline.py
  Internal (top-level): src.models.rag_config, src.rag_pipeline.retriever,
                        src.rag_pipeline.generator, src.indexer.collection_manager,
                        src.utils.hashing, src.utils.logger
  Internal (deferred):  src.orchestrator.config_loader, src.storage.cost_tracker
  External: asyncio, json, time, pathlib, langfuse.decorators

src/rag_pipeline/retriever.py
  Internal (top-level): src.indexer.collection_manager, src.models.rag_config, src.utils.logger
  Internal (deferred):  src.orchestrator.config_loader, src.utils.openrouter_embedding,
                        src.rag_pipeline.openrouter_reranker
  External: asyncio, chromadb, llama_index.core.*, llama_index.retrievers.bm25,
            llama_index.vector_stores.chroma

src/rag_pipeline/generator.py
  Internal (top-level): src.utils.openrouter
  External: langfuse.decorators

src/rag_pipeline/smoke_tester.py
  Internal (top-level): src.utils.logger
  Internal (deferred):  src.models.rag_config, src.orchestrator.config_loader,
                        src.rag_pipeline.pipeline
  External: asyncio, json, pathlib, traceback

src/rag_pipeline/openrouter_reranker.py
  Internal (top-level): src.utils.logger
  External: os, httpx, pydantic, llama_index.core.postprocessor.types,
            llama_index.core.schema, tenacity

src/evaluator/ragas_runner.py
  Internal (top-level): src.models.metrics, src.evaluator.ir_metrics, src.utils.logger,
                        src.utils.json_repair
  Internal (deferred):  src.orchestrator.config_loader, src.models.rag_config,
                        src.models.metrics, src.rag_pipeline.pipeline
  External: random, asyncio, json, re, time, yaml, datasets, ragas.*,
            langchain_openai, langchain_core.*

src/evaluator/scorer.py
  Internal (top-level): src.models.metrics, src.utils.logger, src.orchestrator.config_loader
  External: none

src/evaluator/ir_metrics.py
  Internal: none
  Internal (deferred): ranx
  External: __future__, math

src/storage/db.py
  Internal: none
  External: aiosqlite

src/storage/experiment_log.py
  Internal (top-level): src.storage.db, src.storage.cost_tracker, src.utils.hashing
  External: json, uuid, aiosqlite, datetime

src/storage/cost_tracker.py
  Internal (top-level): src.utils.logger
  External: threading

src/utils/openrouter.py
  Internal (top-level): src.storage.cost_tracker, src.utils.logger
  External: os, asyncio, httpx, tenacity, langfuse.decorators

src/utils/openrouter_embedding.py
  Internal: none
  External: os, typing, llama_index.core.embeddings, llama_index.core.bridge.pydantic, openai

src/utils/logger.py
  Internal: none
  External: sys, structlog, logging

src/utils/hashing.py
  Internal: none
  External: json, hashlib

src/utils/json_repair.py
  Internal (top-level): src.utils.logger
  External: json, re, langchain_core.*, ragas.llms, ragas.prompt.*

src/utils/conversation_summary.py
  Internal (top-level): src.utils.logger
  Internal (deferred):  src.utils.openrouter
  External: __future__

src/reporter/report_writer.py
  Internal (top-level): src.utils.openrouter
  Internal (deferred):  src.orchestrator.config_loader
  External: json, pathlib
```

#### 3.1.2 Script Dependencies

```
scripts/run_overnight.py
  Internal: src.storage.db, src.storage.cost_tracker, src.orchestrator.config_loader,
            src.utils.logger, src.orchestrator.graph, src.models.rag_config,
            src.models.metrics, src.evaluator.ragas_runner, src.rag_pipeline.pipeline,
            src.utils.hashing
  External: sys, subprocess, pathlib, asyncio, signal, uuid, datetime,
            click, dotenv, rich.*, langgraph.checkpoint.sqlite.aio, langfuse.langchain

scripts/fetch_baseline.py
  Internal: src.orchestrator.config_loader, src.models.rag_config,
            src.rag_pipeline.pipeline, src.evaluator.ragas_runner,
            src.storage.cost_tracker, src.models.metrics
  External: asyncio, json, dotenv

scratch/test_brain.py
  Internal: src.scientist.brain, src.utils.openrouter, src.orchestrator.config_loader
  External: asyncio, sys, json, pathlib, dotenv
```

#### 3.1.3 Test Dependencies

```
tests/test_brain.py       → src.scientist.brain, src.scientist.reflection
tests/test_cost_tracker.py → src.storage.cost_tracker
tests/test_deduplicator.py → src.scientist.deduplicator, src.scientist.brain, src.storage, src.utils.hashing
tests/test_ir_metrics.py   → src.evaluator.ir_metrics
tests/test_openrouter.py   → src.utils.openrouter
tests/test_parser_registry.py → src.indexer.parser_registry, src.models.rag_config
tests/test_ragas_runner_parser.py → src.evaluator.ragas_runner, src.utils.json_repair
tests/test_rag_config_expansion.py → src.models.rag_config, src.orchestrator.validator, src.rag_pipeline.retriever
tests/test_scorer.py       → src.evaluator, src.evaluator.scorer, src.models.metrics
tests/test_search_space_constraints.py → src.orchestrator.validator, src.scientist.candidates, src.scientist.brain
tests/test_storage.py      → src.storage
```

### 3.2 Fan-In / Fan-Out (Estimated from Static Import Analysis)

#### Highest Fan-In (Most Imported Modules)

| Module | Est. Fan-In | Imported By |
|--------|-------------|-------------|
| `src.utils.logger` | ~15+ | Almost every file via `get_logger()` |
| `src.orchestrator.config_loader` | ~12 | brain, candidates, validator, budget_guard, collection_manager, pipeline, retriever, smoke_tester, ragas_runner, scorer, reflection, report_writer, graph, run_overnight, fetch_baseline |
| `src.models.rag_config` | ~10 | config_loader, collection_manager, parser_registry, pipeline, retriever, smoke_tester, validator, brain, candidates, ragas_runner, experiment, run_overnight, fetch_baseline |
| `src.utils.openrouter` | ~8 | brain, generator, reflection, report_writer, conversation_summary, openrouter_embedding |
| `src.storage.cost_tracker` | ~6 | budget_guard, experiment_log, openrouter, pipeline, run_overnight, fetch_baseline |
| `src.utils.hashing` | ~6 | pipeline, brain, deduplicator, experiment_log, run_overnight |
| `src.storage.db` | ~5 | brain, deduplicator, experiment_log, run_overnight, tests |
| `src.models.metrics` | ~5 | ragas_runner, scorer, experiment, run_overnight, fetch_baseline |
| `src.indexer.collection_manager` | ~5 | retriever, pipeline, brain, candidates, validator, graph |
| `src.evaluator.ir_metrics` | ~2 | ragas_runner only |

#### Highest Fan-Out (Files with Most Internal Dependencies)

| File | Est. Fan-Out | Depends On |
|------|-------------|------------|
| `run_overnight.py` | ~10 | config_loader, db, cost_tracker, logger, graph, RAGConfig, AggregatedMetrics, ragas_runner, pipeline, hashing |
| `ragas_runner.py` | ~8 | metrics, ir_metrics, logger, json_repair, config_loader, RAGConfig, AggregatedMetrics, pipeline |
| `brain.py` | ~8 | openrouter, logger, config_loader, conversation_summary, candidates, RAGConfig, hashing, db, collection_manager |
| `pipeline.py` | ~7 | RAGConfig, retriever, generator, collection_manager, hashing, logger, config_loader, cost_tracker |
| `collection_manager.py` | ~6 | parser_registry, RAGConfig, logger, config_loader, openrouter_embedding |
| `retriever.py` | ~6 | collection_manager, RAGConfig, logger, openrouter_embedding, config_loader, openrouter_reranker |
| `experiment_log.py` | ~5 | db, cost_tracker, hashing |
| `candidates.py` | ~4 | config_loader, collection_manager, RAGConfig |
| `deduplicator.py` | ~4 | storage.db, logger, hashing |
| `scorer.py` | ~3 | metrics, logger, config_loader |

### 3.3 Graph Centrality

```
                    ┌──────────────────┐
                    │  config_loader   │◄──── Central hub — 12+ dependents
                    │  (12 fan-in)     │
                    └────────┬─────────┘
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
   ┌──────────┐      ┌─────────────┐     ┌────────────┐
   │  brain   │      │  pipeline   │     │  scorer    │
   │ (8 deps) │      │  (8 deps)   │     │  validator │
   └────┬─────┘      └──────┬──────┘     └────────────┘
        │                   │
        ▼                   ▼
   ┌──────────┐      ┌─────────────┐
   │  openrouter│    │  retriever  │
   │  (5 deps) │     │  (6 deps)   │
   └────┬─────┘      └──────┬──────┘
        │                   │
        ▼                   ▼
   ┌──────────┐      ┌─────────────┐
   │cost_tracker│    │coll_manager │
   │ (global)  │     │ (god file)  │
   └──────────┘      └─────────────┘
```

### 3.4 Cross-Layer Violations (Evidence)

**Violation 1: Pipeline imports Orchestrator config**
- File: `src/rag_pipeline/pipeline.py`, lines 37, 101
- Code: `from src.orchestrator.config_loader import load_run_settings`
- Problem: Pipeline is infrastructure (calls LLMs, runs retrieval). It should receive settings, not load them.

**Violation 2: Indexer imports Orchestrator config**
- File: `src/indexer/collection_manager.py`, lines 75, 82, 89
- Code: `from src.orchestrator.config_loader import load_run_settings`
- Problem: Index building (infrastructure) loads orchestration settings directly.

**Violation 3: Evaluator imports Pipeline**
- File: `src/evaluator/ragas_runner.py`, line 283
- Code: `from src.rag_pipeline.pipeline import retrieve_results`
- Problem: Evaluator imports pipeline infrastructure. If pipeline → evaluator → pipeline, this risks an evaluation cycle.

**Violation 4: Domain code reads SQLite directly**
- File: `src/scientist/brain.py`, lines 172-188
- Code:
  ```python
  import src.storage.db as storage_db
  import aiosqlite
  ...
  async with aiosqlite.connect(storage_db.DB_PATH) as db:
      cursor = await db.execute("SELECT config_hash FROM experiments WHERE ...")
  ```
- Problem: Business logic (scientist) bypasses storage abstraction and queries raw SQLite.

**Violation 5: Private API exposed from indexer to retriever**
- File: `src/rag_pipeline/retriever.py`, lines 27-32
- Code:
  ```python
  from src.indexer.collection_manager import (
      _collection_name,   # ← prefixed with _ (private by convention)
      CHROMA_PATH,        # ← internal constant
      load_bm25_nodes,    # ← internal function
      load_bm25_engine,   # ← internal function
  )
  ```
- Problem: `_collection_name` begins with underscore, indicating private API. External consumers importing private symbols indicates failed encapsulation.

**Violation 6: Duplicate `_logical_config()` function (3 copies)**
- File: `src/scientist/deduplicator.py`, line 12-13:
  ```python
  def _logical_config(config: dict) -> dict:
      return {k: v for k, v in config.items() if not k.startswith("_")}
  ```
- File: `src/storage/experiment_log.py`, lines 16-17:
  ```python
  def _logical_config(config: dict) -> dict:
      return {k: v for k, v in config.items() if not k.startswith("_")}
  ```
- File: `src/evaluator/scorer.py`, lines 8-9:
  ```python
  def _logical_config(config: dict) -> dict:
      return {k: v for k, v in config.items() if not k.startswith("_")}
  ```
- Problem: Identical logic copy-pasted across 3 files. Not shared from a utility module.

**Violation 7: Duplicate `_contexts_to_results()` function (2 copies)**
- File: `src/rag_pipeline/pipeline.py`, lines 226-239
- File: `src/evaluator/ragas_runner.py`, lines 419-431
- Both implement:
  ```python
  def _contexts_to_results(contexts: list[list[str]]) -> list[list[dict]]:
      return [[{
          "node_id": f"legacy_{question_idx}_{rank}",
          "doc_id": f"legacy_{question_idx}_{rank}",
          "title": "",
          "score": 1.0 / (rank + 1),
          "text": text,
      } for rank, text in enumerate(context)] for question_idx, context in enumerate(contexts)]
  ```
- Problem: Identical function in two modules. Should be shared.

**Violation 8: Duplicate question-loading logic (3 callers)**
- Pattern `Path("data/hotpotqa/questions.jsonl").read_text().strip().splitlines()` appears in:
  - `src/rag_pipeline/smoke_tester.py`, line 55
  - `src/evaluator/ragas_runner.py`, line 400
  - `scripts/run_overnight.py`, line 278 (via `_load_eval_question_items`)
- Problem: Every evaluation-related file reads the raw JSONL with identical code.

### 3.5 Global Mutable State (Evidence)

**File: `src/storage/cost_tracker.py`**
```python
_lock = threading.Lock()
_total_cost_usd: float = 0.0
_hard_ceiling: float = 10.00
_warning_threshold: float = 7.00

def initialize(hard_ceiling, warning_threshold, start_cost=0.0):
    global _hard_ceiling, _warning_threshold, _total_cost_usd
    with _lock:
        _hard_ceiling = hard_ceiling
        _warning_threshold = warning_threshold
        _total_cost_usd = start_cost

def add_cost(usd: float) -> float:
    global _total_cost_usd
    with _lock:
        _total_cost_usd += usd
        ...
```
- Problem: Sequential tests cannot be isolated because cost state persists across imports. A test that calls `add_cost()` affects subsequent tests unless `initialize()` is called between them.

### 3.6 Hardcoded Dependencies (Evidence)

1. **Filesystem paths hardcoded in 10+ locations:**
   - `config/run_settings.yaml` — `src/orchestrator/config_loader.py`, line 10
   - `config/baseline_config.yaml` — `src/orchestrator/config_loader.py`, line 17
   - `data/hotpotqa/questions.jsonl` — `smoke_tester.py:55`, `ragas_runner.py:400`, `run_overnight.py:278`
   - `data/retrieval_cache/` — `src/rag_pipeline/pipeline.py`, line 24
   - `data/chroma/` — `src/indexer/collection_manager.py`, line 26
   - `data/bm25/` — `src/indexer/collection_manager.py`, line 27
   - `data/corpus/hotpotqa_paragraphs.jsonl` — `collection_manager.py`, line 236
   - `experiments.sqlite` — `src/storage/db.py`, line 8
   - `reports/overnight_run_report.md` — `src/reporter/report_writer.py`, line 10

2. **API base URL hardcoded:**
   - `https://openrouter.ai/api/v1` in `openrouter.py:12`, `retriever.py:253-254`, `ragas_runner.py:56`, `openrouter_reranker.py:37`

3. **Environment variable name hardcoded:**
   - `OPENROUTER_API_KEY` read in `openrouter.py:94`, `validator.py:55`, `retriever.py:253`, `ragas_runner.py:57`, `collection_manager.py:370`, `openrouter_reranker.py:33`

### 3.7 God Files Analysis

**File: `src/evaluator/ragas_runner.py` (388 lines)**
Responsibilities:
- RAGAS LLM builder (`_build_ragas_llm`)
- RAGAS embedding builder (`_build_ragas_embeddings`)
- Model kwargs builder (`_build_openrouter_model_kwargs`)
- Extra body builder (`_build_openrouter_extra_body`)
- Judge config loader (`_load_ragas_judge_config`)
- Metric builder (`_build_ragas_metrics`)
- Generation finished check (`_ragas_generation_finished`)
- Single eval runner (`run_single_eval`)
- Safe mean calculator (`_safe_mean`)
- Full evaluation LangGraph node (`evaluator_node`)
- Question loader (`_load_eval_question_items`, `_load_eval_questions`)
- Context-to-results converter (`_contexts_to_results` — duplicate)

**File: `src/indexer/collection_manager.py` (317 lines)**
Responsibilities:
- ChromaDB client management (`_get_chroma_client`)
- BM25 cache management (path builders, loaders)
- Collection name generation (`_collection_name`)
- Cache completeness checking (`_cache_is_complete`, `collection_is_cached`)
- Index building (`_build_collection`, `_build_bm25_cache_only`)
- Corpus loading (`_load_corpus_as_documents`)
- Embedding model builder (`_build_embed_model`)
- Available config listing (`list_available_index_configs`)
- Config-parse from collection stem (`_config_from_collection_stem`)
- LangGraph node (`indexer_node`)
- Settings access functions (`_new_index_builds_allowed`, `_expensive_parser_builds_allowed`, `_effective_corpus_limit`)

**File: `src/scientist/brain.py` (303 lines)**
Responsibilities:
- Scientist LLM invocation (`scientist_node`)
- Fallback proposal generation (`_fallback_proposal`)
- Reranker probe proposal (`_reranker_probe_proposal`)
- Structured exploration proposal (`_structured_exploration_proposal`)
- Candidate selection with SQLite dedup (`_select_unused_candidate`)
- Strategy guards (`_should_run_structured_exploration`, `_should_force_reranker_probe`)
- History builder from state (`_build_history_lines`)
- Scientist prompt builder (`_build_scientist_prompt`)
- History truncation (`_truncate_history`)
- History compression with LLM (via `sliding_window_compress`)
- Direct SQLite queries (`aiosqlite.connect(storage_db.DB_PATH)`)

**File: `scripts/run_overnight.py` (490 lines)**
Responsibilities:
- CLI argument parsing (click)
- Virtual environment detection (`_ensure_venv`)
- Signal handling (SIGTERM/SIGINT)
- Environment validation (`_validate_environment`)
- Banner printing (`_print_banner`)
- Event logging (`_log_event`)
- Config table display (`_print_config_table`)
- Metrics table display (`_print_metrics`)
- Elapsed time formatting (`_fmt_elapsed`)
- Baseline evaluation (`_evaluate_baseline`)
- Final evaluation (`_evaluate_final_best`)
- Run loop orchestration (`_run`)
- Empty metrics factory (`_empty_metrics`)
- Node metadata + status style dictionaries (global constants)

### 3.8 Hidden Side Effects (Evidence)

1. **`cost_tracker.add_cost()`** — modifies module-level `_total_cost_usd` and raises `BudgetExceededError`. Every HTTP call in `openrouter.py` has this side effect.

2. **`get_or_build_collection()`** — writes ChromaDB data to disk (`data/chroma/`), BM25 pickle files (`data/bm25/`), with no return value indicating writes occurred.

3. **`_get_or_build_results()`** in pipeline.py — writes JSON cache files to `data/retrieval_cache/`. The function name suggests "get or build" but the caching is a side effect invisible to callers.

4. **`install_ragas_output_parser_compat_patch()`** — monkey-patches `RagasOutputParser.parse_output_string` at runtime (line 21 of json_repair.py). Calling this function mutates global class state in a third-party library.

### 3.9 Long Parameter List (Evidence)

- `run_single_eval()` in `ragas_runner.py` — **15 parameters**:
  ```python
  async def run_single_eval(
      questions, answers, contexts, ground_truths,
      retrieval_results=None, question_ids=None, supporting_titles=None,
      run_ragas=True, ragas_min_fast_score=None,
      timeout_sec=120, timeout_backoff_factor=2.0,
      max_timeout_sec=240, timeout_retries=1, metrics=None,
  )
  ```
  - Problem: 15 parameters indicate the function does too much or lacks abstraction.

### 3.10 Implementation Score Rubric

| Criterion | Weight | Score | Evidence |
|-----------|--------|-------|----------|
| Single-responsibility per file | 15% | 3/10 | 4 god files (ragas_runner, collection_manager, brain, run_overnight) |
| Code duplication | 15% | 4/10 | 3 copies of `_logical_config`, 2 copies of `_contexts_to_results`, 3 callers of raw question loading |
| Cross-layer violations | 15% | 3/10 | 8 documented cross-layer imports; 10+ files call `load_run_settings()` |
| Encapsulation | 15% | 3/10 | Private symbols leaked; direct SQLite in domain code; global state |
| Hardcoded infrastructure | 10% | 3/10 | 10+ hardcoded paths; 4+ locations with hardcoded API URL |
| Testability | 15% | 4/10 | Most files require real DB/LLM/filesystem; global state prevents isolation |
| Replaceability | 15% | 3/10 | No interfaces; ChromaDB/OpenRouter/SQLite are baked into call sites |

**Implementation-level Score: 3.3/10** → **POOR**

---

## 4. File-by-File Evidence Report

### 4.1 Well-Modularized Files (Score 8-10/10)

| File | Reason |
|------|--------|
| `src/orchestrator/state.py` | Pure TypedDict with 0 dependencies |
| `src/models/metrics.py` | Pydantic model + median computation, no side effects |
| `src/utils/logger.py` | 35 lines, single concern, structlog config |
| `src/utils/hashing.py` | 7 lines, single function, pure |
| `src/evaluator/ir_metrics.py` | Pure functions, ranx fallback, no infrastructure deps |
| `src/indexer/parser_registry.py` | 71 lines, clean factory pattern |
| `src/models/experiment.py` | 27 lines, pure Pydantic model |
| `src/orchestrator/budget_guard.py` | 9 lines, single check |
| `src/rag_pipeline/generator.py` | 40 lines, one function, single dependency |

### 4.2 Files Requiring Refactoring (Detailed)

#### `src/evaluator/ragas_runner.py` (388 lines)

**Responsibilities (7+):**
1. Build RAGAS LLM wrapper (`_build_ragas_llm`)
2. Build RAGAS embedding wrapper (`_build_ragas_embeddings`)
3. Load model routing config (`_load_ragas_judge_config`)
4. Construct OpenRouter model kwargs (`_build_openrouter_model_kwargs`, `_build_openrouter_extra_body`)
5. Select RAGAS metrics (`_build_ragas_metrics`)
6. Run single evaluation (`run_single_eval` — 15 parameters)
7. Run full evaluation as LangGraph node (`evaluator_node`)
8. Load questions from file (`_load_eval_question_items`, `_load_eval_questions`)
9. Convert contexts to results format (`_contexts_to_results` — duplicate of pipeline.py)

**Evidence of problem:**
- The `evaluator_node` function (lines 275-391) does its own question loading, RAGAS config loading, retrieval calling, evaluation running, and timeout handling. This is ~115 lines for what should be a thin wrapper.
- Langfuse `@observe` decorator on line 6 of import block, used on `run_single_eval`.
- The RAGAS LLM is rebuilt on every evaluation call (line 192).

#### `src/indexer/collection_manager.py` (317 lines)

**Responsibilities (10+):**
- Collection caching logic
- ChromaDB client creation
- BM25 cache path management
- Collection name derivation
- Cache completeness verification
- Full index building (ChromaDB + BM25)
- BM25-only cache building
- Corpus document loading
- Embedding model construction
- LangGraph node function
- Settings accessor helpers (3 small functions)

**Evidence of problem:**
- Imports `load_run_settings()` from orchestrator in 3 separate deferred locations (lines 75, 82, 89).
- 4 functions (`_new_index_builds_allowed`, `_expensive_parser_builds_allowed`, `_effective_corpus_limit`) each independently call `load_run_settings()` with identical caching — triplicate parsing of the same config.
- `list_available_index_configs()` (lines 97-120) and `_config_from_collection_stem()` (lines 123-156) implement complex filesystem-iteration + string-parsing logic for config reconstruction — brittle and untestable.

#### `src/scientist/brain.py` (303 lines)

**Responsibilities (9+):**
- LLM invocation with reasoning
- Sliding-window history compression (calls `sliding_window_compress`)
- Structured exploration decision & proposal
- Reranker probe decision & proposal
- Fallback proposal generation
- Candidate selection with SQLite dedup
- Scientist prompt construction (reads prompt from file)
- History building from state patterns
- History truncation

**Evidence of problem:**
- Lines 169-208 (`_select_unused_candidate`): Direct SQLite query inside a candidate-selection function. Opens its own connection, executes SQL, filters results — all in one function. This belongs in a repository.
- Lines 233-349 (`_build_scientist_prompt`): 116 lines for prompt construction, including re-importing `load_run_settings` and calling `list_available_index_configs` from indexer.

#### `scripts/run_overnight.py` (490 lines)

**Responsibilities (12+):**
- CLI argument parsing
- Virtual env detection/activation
- Signal handling
- Environment validation
- Banner printing
- Per-event display logging
- Config and metrics table formatting
- Elapsed time formatting
- Baseline evaluation
- Final best-config evaluation
- Run-loop orchestration with state management
- Dry-run mode

**Evidence of problem:**
- Lines 64-91: Two global dictionaries (`NODE_META`, `STATUS_STYLE`) for display logic — mixed with CLI code.
- Lines 260-356: `_evaluate_baseline()` calls `retrieve_results`, `run_single_eval`, `AggregatedMetrics.from_runs` — duplicating logic from `fetch_baseline.py` and `ragas_runner.py`.
- Lines 359-414: `_evaluate_final_best()` duplicates the same pattern.

---

## 5. Evidence for Major Claims

### Claim 1: Configuration coupling is excessive

**Evidence:**
- `load_run_settings()` is imported and called in **12 files**: `brain.py:28`, `candidates.py:60`, `validator.py:6`, `budget_guard.py:4`, `collection_manager.py:75/82/89`, `pipeline.py:37/101`, `retriever.py:157`, `smoke_tester.py:14`, `ragas_runner.py:280`, `scorer.py:3`, `reflection.py:33`, `report_writer.py:8`, `graph.py:95`, plus `run_overnight.py:112` and `fetch_baseline.py:3`.
- Each file accesses deeply nested dict keys like `settings["evaluation"]["n_questions"]`, `settings["run"]["cost_hard_ceiling_usd"]` — meaning a key rename breaks all 12+ callers.
- There is no typed config model — all callers rely on raw `dict` access with no validation.

### Claim 2: The evaluator module is the most structurally problematic

**Evidence:**
- Largest single file: `ragas_runner.py` at 388 lines — largest in `src/`.
- Mixes: LLM configuration, embedding configuration, model routing config loading, metric selection, evaluation execution, question data loading, and LangGraph node wiring.
- Imports from 5 internal modules (metrics, ir_metrics, logger, json_repair, pipeline) plus 10+ external packages.
- Contains `_contexts_to_results()` — an exact duplicate of `pipeline.py:_contexts_to_results()`.
- Contains `_load_eval_questions()` and `_load_eval_question_items()` — two almost-identical functions (differ only in return format).

### Claim 3: No dependency inversion anywhere

**Evidence:**
- No abstract base classes or protocols in the entire codebase (other than those from external libraries).
- All modules import concrete implementations directly:
  - `chromadb.PersistentClient` instantiated in both `collection_manager.py:56` and `retriever.py:200`
  - `call_openrouter()` referenced directly from 6 callers
  - `aiosqlite.connect(storage_db.DB_PATH)` opened directly in 3+ locations
- The only abstraction boundary is `LangGraph StateGraph`, which accepts callable node functions but provides no dependency injection mechanism.

### Claim 4: Global state makes the storage layer fragile

**Evidence:**
- `cost_tracker.py` has module-level mutable state with threading locks. Tests must call `initialize()` between test cases.
- `db.py` has `DB_PATH = "experiments.sqlite"` as a module constant — tests that need a different path must know to override it via `src.storage.db.DB_PATH = ":memory:"`.
- `config_loader.py` uses `@lru_cache(maxsize=1)` — tests must call `invalidate_settings_cache()` between config changes.

### Claim 5: The retriever module violates indexer encapsulation

**Evidence:**
- `src/rag_pipeline/retriever.py`, lines 27-32:
  ```python
  from src.indexer.collection_manager import (
      _collection_name,   # ✗ Private function (prefixed with _)
      CHROMA_PATH,        # ✗ Internal implementation constant
      load_bm25_nodes,    # ✗ Published as public but intended as internal
      load_bm25_engine,   # ✗ Same
  )
  ```
- The `_collection_name` function has no reason to be external — it derives a collection name from a config, a stable concern that should be part of `collection_manager`'s public API.
- `CHROMA_PATH` is a file path constant — every consumer of this becomes coupled to the local ChromaDB filesystem layout.

---

## 6. Design-Level vs Implementation-Level Comparison

| Module | Design-Level | Implementation-Level | Gap Analysis |
|--------|-------------|---------------------|--------------|
| `orchestrator/` | 8/10 — clear state machine, routing | 5/10 — graph imports everything; config_loader is coupled throughout | Conceptual design is clean; graph.py is the composition root but with no DI pattern |
| `scientist/` | 7/10 — propose + dedup + reflect is coherent | 3/10 — brain.py does too much; SQLite mixed in | Architecture says "propose configs"; code says "propose configs + query DB + render prompts + manage history" |
| `evaluator/` | 7/10 — measure + decide is clear | 2/10 — single 388-line file mixes LLM setup, data loading, eval execution | Worst gap. Should be 4-5 files (LLM builder, question loader, metric runner, node function) |
| `indexer/` | 6/10 — build + cache indexes is reasonable | 3/10 — single 317-line file with 10+ concerns | Index building, cache checking, and config enumeration should be separate |
| `rag_pipeline/` | 7/10 — retrieve + generate + rerank | 5/10 — retriever imports privates; pipeline mixes orchestration with caching | Boundary with indexer is the biggest problem |
| `models/` | 9/10 — pure data models | 9/10 — single-responsibility, pure | Little gap. Best module. |
| `storage/` | 6/10 — persistence + cost tracking | 4/10 — global singleton; no repository abstraction | Should inject dependencies, not rely on module state |
| `utils/` | 5/10 — utility catch-all | 5/10 — openrouter.py does too much | Both design and implementation see utils as a dumping ground |

---

## 7. Refactoring Priorities

### P0: Extract Duplicated Functions (2 hrs, low risk)

| What | Files | Action |
|------|-------|--------|
| Merge 3 `_logical_config()` | `deduplicator.py`, `experiment_log.py`, `scorer.py` | Move to `src/utils/config_helpers.py` |
| Merge 2 `_contexts_to_results()` | `pipeline.py`, `ragas_runner.py` | Move to `src/rag_pipeline/result_converters.py` |
| Consolidate question loading | `smoke_tester.py`, `ragas_runner.py`, `run_overnight.py` | Create `src/evaluator/question_loader.py` |

### P1: Split God Files (1-2 days, medium risk)

| File | Split Into |
|------|-----------|
| `ragas_runner.py` | `llm_builder.py`, `question_loader.py`, `eval_runner.py`, `evaluator_node.py` |
| `collection_manager.py` | `chroma_client.py`, `bm25_cache.py`, `index_builder.py`, `collection_node.py` |
| `brain.py` | `scientist_node.py`, `prompt_builder.py`, `candidate_selector.py` (move SQLite to storage) |
| `run_overnight.py` | `cli.py`, `display.py`, `baseline_eval.py`, `final_eval.py` |

### P2: Remove Global State (1 day, medium risk)

| What | How |
|------|-----|
| `cost_tracker.py` | Wrap in class, instantiate in `run_overnight.py`, pass to graph via state |
| `config_loader.py` LRU cache | Replace with explicit config object passed through state |
| `DB_PATH` | Make configurable via env var `RAG_DB_PATH` with default |

### P3: Fix Cross-Layer Violations (2-3 days, high risk)

| Violation | Fix |
|-----------|-----|
| Pipeline imports config_loader | Accept settings as parameter, not by importing |
| Collection_manager imports config_loader | Accept settings as parameter |
| Retrievers imports private symbols from indexer | Make `_collection_name` public; move `load_bm25_nodes` to public API |
| Brain reads SQLite | Move to storage repository; pass dedup check as parameter |
| RAGAS runner imports pipeline | Accept retrieval function as injected callback |

### P4: Add Interface Abstractions (3-5 days, high risk)

| Interface | Implementations |
|-----------|----------------|
| `VectorStore` | ChromaDB (existing), Pinecone (future) |
| `LLMClient` | OpenRouter (existing), Ollama (future) |
| `ConfigStore` | SQLite (existing), Postgres (future) |
| `Evaluator` | RAGAS (existing), custom evaluator (future) |

### Risk Assessment

| Risk | Likelihood | Impact | Current Exposure |
|------|-----------|--------|-----------------|
| RAGAS version upgrade breaks monkey-patch | HIGH | Critical — evaluation stops | `json_repair.py` monkey-patches `RagasOutputParser.parse_output_string` |
| Global cost state causes production bug | MEDIUM | High — billing runaway | `cost_tracker.py` module-level state could be corrupted |
| New contributor introduces circular dependency | MEDIUM | High — runtime crash | No enforced layer boundaries; `ragas_runner` imports `pipeline` and vice versa |
| Config key rename silently drops setting | HIGH | Medium — incorrect behavior | `settings["evaluation"]["n_questions"]` accessed as raw dict in 6+ files |
| ChromaDB storage format change | LOW | Very High — data loss | Directly coupled in both `collection_manager.py` and `retriever.py` |

---

## 8. Final Assessment

### Design-Level Modularity Score

| Component | Score | Rubric |
|-----------|-------|--------|
| Folder structure & naming | 8/10 | Clear, conventional, sensible |
| Conceptual layer boundaries | 7/10 | Scientist → Validator → Evaluator → Scorer is clean |
| Extensibility (paper) | 6/10 | Adding new node type is straightforward |
| Config architecture | 6/10 | Centralized but untyped |
| Interface design | 4/10 | No interfaces, no DI, no repository pattern |

**Weighted Average: 6.2/10 → MODERATE**
**Confidence: HIGH** (direct inspection of all 52 files)

### Implementation-Level Modularity Score

| Component | Score | Rubric |
|-----------|-------|--------|
| Single-responsibility per file | 3/10 | 4 god files account for 42% of all source lines |
| Code duplication | 4/10 | 3 copies of `_logical_config`, 2 of `_contexts_to_results` |
| Cross-layer discipline | 3/10 | 8 documented violations; 10+ files importing config_loader |
| Encapsulation | 3/10 | Private symbols leaked; direct SQLite in domain code |
| Hardcoded dependencies | 3/10 | 10+ hardcoded paths, 4+ locations with hardcoded API URL |
| Test isolation | 4/10 | Global state prevents hermetic tests |
| Replaceability | 3/10 | No abstractions; all infra is concrete |

**Weighted Average: 3.3/10 → POOR**
**Confidence: HIGH** (every claim backed by evidence above)

### Overall Assessment

This repository has **a well-conceived architecture** (LangGraph state machine, config-driven experiments, clear node progression) but **poor implementation-level modularity**. The gap between design (6.2/10) and implementation (3.3/10) is 2.9 points — a strong signal that the code does not reflect the intended architecture.

**The "Big Four" problems:**
1. **4 god files** (ragas_runner, collection_manager, brain, run_overnight) = 1,498 lines = 42% of `src/` code
2. **Code duplication** in 8 locations across 10+ files
3. **Cross-layer coupling** via `load_run_settings()` called in 12 files across all layers
4. **No dependency inversion** — every component is hardcoded to its implementation

**Positive signs:**
- The `models/` module is excellent (clean, pure, testable)
- Small files like `generator.py` (40 lines), `budget_guard.py` (9 lines), `hashing.py` (7 lines) show the team knows good modularity
- The caching strategy is thoughtful and avoids redundant computation
- Config-driven design reduces the need for re-compilation

**Bottom line:** The system works correctly and the macro-architecture is sound, but the micro-architecture at the file-function level will become a significant maintenance burden as the project grows. The recommended P0/P1 refactoring addresses the most critical issues with minimal disruption.
