# Graph Report - .  (2026-07-17)

## Corpus Check
- 17 files · ~91,697 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1046 nodes · 2239 edges · 76 communities (55 shown, 21 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 161 edges (avg confidence: 0.64)
- Token cost: 0 input · 101,945 output

## Community Hubs (Navigation)
- DI Interfaces & Protocols
- Embedding & Collection Cache
- Provider Factory & Budget Guard
- LLM Model Config Schemas
- Overnight Run Pipeline Flowchart
- LangGraph Budget Guard & State
- Run/Eval/Acceptance Settings Schemas
- Experiment Storage Models
- Scientist Config Exploration
- SQLite Database Connection
- Deduplicator & Experiment Log
- OpenAI Client Adapter
- OpenRouter Embedding Adapter
- Config Loader & Validation Allowlists
- RAG Generator & Pipeline
- OpenAI Client Tests
- Model Catalog Reranker Builders
- Experiment & Metrics Models
- Context Budget & Brain Prompt Tests
- IR Metrics Evaluation
- Evaluator Node & RAGAS Runner
- run_overnight Environment Validation
- Validator & Query Fusion (OpenRouter debt)
- Smoke Tester & Reflection
- Function Trace Utility
- Overnight Display & Eval Loop
- Scientist Prompt Builder
- Registry-Dict Pattern (Model Catalog)
- Config Hash Repository
- Reranking & Hybrid Retrievers
- DI Protocol Interfaces (Docs)
- Evaluator Architecture Docs
- Baseline Fetch & Question Loader
- God Nodes & Constructor Injection Principle
- Model Routing Config
- Reflection Node Docs
- Acceptance/Indexer/Reporter Node Docs
- CI/Pre-commit/PR Checklist
- Export Experiments Script
- OpenRouter Hardcoding Bug Class
- run_overnight Entry & Pricing Loader
- Run Settings & Budget Guard Docs
- Contributing Architecture Overview
- Scientist Prompt I/O Pairing
- Cost Tracker Injection Tests
- Baseline Config & Architecture Docs
- CI Workflow Steps
- No-op DB Context Manager
- Logger Setup & Test Fixtures
- Search Space Constraint Tests
- Acceptance Criteria Docs
- Ruflo/Claude-Flow Agent Config (AGENTS.md)
- HotpotQA Data Enrichment Script
- Repository Pattern Principle
- OpenAI Pricing Table
- Developer Guide ThreadPool Solution
- Retriever Docs (Reranking/Hybrid)
- GitHub Issue Templates
- README Overview & Tech Stack
- Environment Setup Script
- Async Test Loop Setup
- Storage Package Init
- Utils Package Init
- Code of Conduct
- Contributing Branching Strategy
- Contributing Project Structure
- Docker Compose Config
- Budget Guard Node Docs
- Config Hash Repository Docs
- Generator Module Docs
- Run Repository Docs
- Project Root Marker
- Pre-commit Hooks Config
- Chroma Client Factory Path

## God Nodes (most connected - your core abstractions)
1. `RAGConfig` - 76 edges
2. `Provider` - 49 edges
3. `OpenAIClient` - 45 edges
4. `ICostTracker` - 36 edges
5. `ILLMClient` - 28 edges
6. `build_graph()` - 26 edges
7. `get_logger()` - 23 edges
8. `Database` - 21 edges
9. `get_total()` - 19 edges
10. `run_single_eval()` - 18 edges

## Surprising Connections (you probably didn't know these)
- `Key features (Autonomous Experimentation Loop, LangGraph Orchestration, Strict Budget Guarding, Resilient Evaluation Threading, SQLite Storage)` --semantically_similar_to--> `LangGraph state machine loop: Scientist -> Validator -> Deduplicator -> Budget Guard -> Indexer -> Smoke Test -> Evaluator -> Acceptance -> Recorder -> Reflection`  [INFERRED] [semantically similar]
  README.md → CONTRIBUTING.md
- `Registry-dict-over-if/elif dispatch convention` --references--> `build_node_parser()`  [EXTRACTED]
  CLAUDE.md → src/indexer/parser_registry.py
- `Prefer constructor-injected dependencies over module-level singletons` --references--> `OpenAIClient`  [EXTRACTED]
  CLAUDE.md → src/utils/openai_client.py
- `Avoid third near-duplicate ILLMClient Protocol implementation` --references--> `OpenAIClient`  [EXTRACTED]
  CLAUDE.md → src/utils/openai_client.py
- `Codebase knowledge graph (graphify-generated, graph.html, GRAPH_REPORT.md)` --references--> `OpenAIClient`  [EXTRACTED]
  README.md → src/utils/openai_client.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **OpenRouter-Specific Hardcoding Bug Recurrence Across Modules** — claude_openrouter_hardcoding_bug_class, src_evaluator_ragas_setup_module, src_rag_pipeline_retriever__build_query_fusion_llm, src_orchestrator_validator_cohererrerank_check [INFERRED 0.85]
- **Config-Driven Dispatch and Pydantic-Derived Validation Conventions** — claude_registry_dict_pattern, claude_validation_allowlist_derivation, src_core_model_catalog_embedding_catalog, config_loader_load_settings [INFERRED 0.75]
- **LangGraph Orchestration Loop and RAGAS Threading Design** — contributing_architecture_overview, contributing_extend_guardrail_node, contributing_threadpool_isolation_ragas, src_evaluator_ragas_setup_module [INFERRED 0.75]
- **System Initialization and Baseline Setup** — docs_mermaid_diagram_2_start_run_overnight_py, docs_mermaid_diagram_2_initialize_sqlite_db_wal_mode, docs_mermaid_diagram_2_initialize_cost_tracker, docs_mermaid_diagram_2_load_config_baseline_settings, docs_mermaid_diagram_2_baseline_cached, docs_mermaid_diagram_2_run_baseline_evaluation, docs_mermaid_diagram_2_store_baseline_score_in_db, docs_mermaid_diagram_2_initialize_graph_state [EXTRACTED 1.00]
- **Autonomous LangGraph Execution Loop** — docs_mermaid_diagram_2_scientist_propose_rag_config, docs_mermaid_diagram_2_validator_schema_bounds_check, docs_mermaid_diagram_2_deduplicator_config_hash_check, docs_mermaid_diagram_2_budget_guard_api_cost_check, docs_mermaid_diagram_2_index_builder_chromadb, docs_mermaid_diagram_2_smoke_tests_basic_queries, docs_mermaid_diagram_2_evaluator_node, docs_mermaid_diagram_2_failhandler, docs_mermaid_diagram_2_acceptance_score_comparison, docs_mermaid_diagram_2_recorder_persist_results, docs_mermaid_diagram_2_reflection_pattern_analysis, docs_mermaid_diagram_2_max_experiments_reached, docs_mermaid_diagram_2_report, docs_mermaid_diagram_2_end_run [EXTRACTED 1.00]
- **Evaluator Execution Pipeline** — docs_mermaid_diagram_2_evaluator_entry, docs_mermaid_diagram_2_select_evaluation_questions, docs_mermaid_diagram_2_run_evaluations, docs_mermaid_diagram_2_aggregate_results_median_stddev, docs_mermaid_diagram_2_return_final_score, docs_mermaid_diagram_2_async_retrieval_aiohttp, docs_mermaid_diagram_2_single_run_evaluation, docs_mermaid_diagram_2_thread_pool_execution, docs_mermaid_diagram_2_ragas_metrics_computation, docs_mermaid_diagram_2_llm_scoring_faithfulness_recall, docs_mermaid_diagram_2_compute_run_metrics [EXTRACTED 1.00]
- **LangGraph Autonomous Optimization Loop** — docs_overnight_execution_guide_scientist_node, docs_overnight_execution_guide_validator_node, docs_overnight_execution_guide_deduplicator_node, docs_overnight_execution_guide_budget_guard_node, docs_overnight_execution_guide_indexer_node, docs_overnight_execution_guide_smoke_test_node, docs_overnight_execution_guide_recorder_node, docs_overnight_execution_guide_acceptance_node, docs_overnight_execution_guide_reflection_node, docs_overnight_execution_guide_report_writer_node [EXTRACTED 1.00]
- **Protocol-Based DI Container Pattern** — docs_project_architecture_breakdown_provider, docs_project_architecture_breakdown_icosttracker, docs_project_architecture_breakdown_illmclient, docs_project_architecture_breakdown_iembeddingservice, docs_project_architecture_breakdown_idatabase [EXTRACTED 0.90]

## Communities (76 total, 21 thin omitted)

### Community 0 - "DI Interfaces & Protocols"
Cohesion: 0.05
Nodes (40): Protocol, Core DI interfaces and container. Exposes all service abstractions and the Provi, IChromaClientFactory, ICostTracker, IDatabase, ILLMClient, IModelRoutingProvider, IRagasFactory (+32 more)

### Community 1 - "Embedding & Collection Cache"
Cohesion: 0.06
Nodes (57): bm25_node_count(), build_embed_model(), cache_is_complete(), effective_corpus_limit(), expensive_parser_builds_allowed(), load_bm25_engine(), load_bm25_nodes(), load_corpus_as_documents() (+49 more)

### Community 2 - "Provider Factory & Budget Guard"
Cohesion: 0.05
Nodes (50): _build_openai_provider(), _build_openrouter_provider(), Any, ValueError, Resolves `settings.run.llm_provider` to a fully-wired Provider.  Single seam for, _unknown_provider_error(), Cost-based execution guard that halts the workflow if budget ceiling is exceeded, add_cost() (+42 more)

### Community 3 - "LLM Model Config Schemas"
Cohesion: 0.08
Nodes (48): ModelConfig, Model configuration schemas for LLM providers and agent role assignments.  Def, LLM configuration: model_id, reasoning effort, tokens, temperature, format optio, LLMResult, _build_openrouter_extra_body(), _build_openrouter_model_kwargs(), build_ragas_llm(), _no_extra_body() (+40 more)

### Community 4 - "Overnight Run Pipeline Flowchart"
Cohesion: 0.07
Nodes (34): Acceptance: Score Comparison, Aggregate Results (Median, StdDev), Async Retrieval (aiohttp), Baseline Cached? (decision), Budget Guard: API Cost Check, Compute Run Metrics, Deduplicator: Config Hash Check, End Run (+26 more)

### Community 5 - "LangGraph Budget Guard & State"
Cohesion: 0.11
Nodes (28): BaseCheckpointSaver, CompiledStateGraph, budget_guard_node(), Decides whether to continue running based on total cost.      Evaluates `total_c, _after_budget_guard(), _after_deduplicator(), _after_evaluator(), _after_indexer() (+20 more)

### Community 6 - "Run/Eval/Acceptance Settings Schemas"
Cohesion: 0.11
Nodes (27): AcceptanceSettings, EvalSettings, ExploreExploitSettings, BaseModel, Configuration schemas for overnight experiment runs, evaluation, acceptance, and, Top-level settings container: aggregates all run, eval, acceptance, and explorat, Budget and concurrency limits: max_experiments, max_hours, cost ceiling, failure, Evaluation setup: question counts, RAGAS metrics, timeouts, smoke testing, audit (+19 more)

### Community 7 - "Experiment Storage Models"
Cohesion: 0.10
Nodes (18): ConfigHash, Experiment, HistoricalRecord, Domain models for the experiment tracking database., Deduplication record mapping config hash to first seen timestamp and best score., Best result retrieved for a given config hash from experiment history., Single RAG configuration trial with metrics and cost tracking., ExperimentRepository (+10 more)

### Community 8 - "Scientist Config Exploration"
Cohesion: 0.17
Nodes (24): scientist_node(), _should_force_reranker_probe(), _should_run_structured_exploration(), _available_index_configs(), _combine_candidates(), get_fallback_candidates(), get_reranker_probe_candidates(), get_structured_exploration_candidates() (+16 more)

### Community 9 - "SQLite Database Connection"
Cohesion: 0.10
Nodes (15): datetime, Database, SQLite connection manager and schema initialisation. WAL mode is MANDATORY for s, Manages SQLite connection with WAL mode for safe async access., Initialize database with optional custom path., Create tables, set pragma settings, and backfill config_hashes from existing exp, Context manager for async database connection., init_db() (+7 more)

### Community 10 - "Deduplicator & Experiment Log"
Cohesion: 0.13
Nodes (21): deduplicator_node(), _fetch_best_historical_record(), Experiment deduplication and config hash tracking.  Detects repeated configurati, Retrieve best experiment result for a config hash., Check if config was already tried; block duplicate or mark success; clean stale, _config_summary(), Experiment recording and state tracking for RAG optimization runs.  Logs experim, Format config dict into human-readable summary for logging patterns. (+13 more)

### Community 11 - "OpenAI Client Adapter"
Cohesion: 0.12
Nodes (16): call_openai(), OpenAIClient, OpenAIError, OpenAINonRetryableError, OpenAIRateLimitError, Exception, Check only the models this project actually references (not         OpenAI's ful, Thin traced wrapper. Unlike `call_openrouter`, takes an explicit client     rath (+8 more)

### Community 12 - "OpenRouter Embedding Adapter"
Cohesion: 0.11
Nodes (14): AsyncOpenAI, BaseEmbedding, _build_openrouter_embedding(), OpenRouterEmbedding, Custom LlamaIndex BaseEmbedding that calls /embeddings on OpenRouter. Refactored, Sync wrapper: embed multiple texts (creates event loop if needed)., LlamaIndex embedding provider wrapping OpenRouter /embeddings endpoint., Initialize with model_name and optional API credentials (fallback to env vars). (+6 more)

### Community 13 - "Config Loader & Validation Allowlists"
Cohesion: 0.13
Nodes (21): Derive validation allowlists from Pydantic model fields, invalidate_all(), load_all(), load_baseline_config(), load_env(), load_model_routing(), load_settings(), Settings (+13 more)

### Community 14 - "RAG Generator & Pipeline"
Cohesion: 0.16
Nodes (18): generate_answer(), RAG pipeline components: retriever construction, answer generation, and smoke te, _contexts_to_results(), _get_or_build_contexts(), _get_or_build_results(), Path, Orchestrate retrieval and generation phases of the RAG pipeline.  Retrieval resu, _results_to_contexts() (+10 more)

### Community 15 - "OpenAI Client Tests"
Cohesion: 0.16
Nodes (14): _build_payload(), _FakeAsyncClient, _FakeResponse, A reasoning model with no reasoning_effort hint gets neither field —     OpenAI', Stands in for httpx.AsyncClient — no mocking library is installed in     this pr, test_build_payload_json_response_format(), test_build_payload_non_reasoning_model_uses_temperature(), test_build_payload_reasoning_model_ignores_reasoning_effort_when_unset() (+6 more)

### Community 16 - "Model Catalog Reranker Builders"
Cohesion: 0.16
Nodes (14): BaseNodePostprocessor, _build_openrouter_reranker(), embedding_dimensions(), ValueError, Registry mapping RAGConfig model identifiers to the provider that serves them., Return the vector dimensionality for `model_id`., _unknown_embedding_model_error(), _unknown_reranker_error() (+6 more)

### Community 17 - "Experiment & Metrics Models"
Cohesion: 0.15
Nodes (14): ExperimentRecord, BaseModel, Experiment tracking and results models for RAG configuration experiments., Complete record of a single RAG configuration experiment run., Re-exports the core data models: experiment records, metrics, and RAG config., AggregatedMetrics, BaseModel, RAG evaluation metrics models for single runs and aggregated results. (+6 more)

### Community 18 - "Context Budget & Brain Prompt Tests"
Cohesion: 0.17
Nodes (19): Trim text to fit within max_tokens, cutting at a sentence boundary when     poss, truncate_to_token_budget(), _make_prompt(), Text already under max_tokens passes through unchanged., No search-space restrictions configured -> no constraints block is injected into, test_prompt_contains_best_config(), test_prompt_contains_system_instructions(), test_prompt_ends_with_json_instruction() (+11 more)

### Community 19 - "IR Metrics Evaluation"
Cohesion: 0.16
Nodes (16): _build_qrels_and_run(), _evaluate_ir_fallback(), evaluate_ir_metrics(), _mean(), _mrr(), _ndcg(), Information Retrieval metrics evaluation (recall, precision, NDCG, MRR).  Comp, Compute Normalized Discounted Cumulative Gain. (+8 more)

### Community 20 - "Evaluator Node & RAGAS Runner"
Cohesion: 0.21
Nodes (14): OpenAIEmbeddings, evaluator_node(), RAGAS evaluation orchestration and IR metric computation.  Runs full evaluatio, Extract mean of column from pandas DataFrame, returning 0.0 if missing or NaN., Run IR metrics immediately, then conditionally run RAGAS metrics with retry logi, run_single_eval(), _safe_mean(), build_ragas_embeddings() (+6 more)

### Community 21 - "run_overnight Environment Validation"
Cohesion: 0.25
Nodes (16): Provider-aware --dry-run checks: required key present, and for     "openai" spe, _validate_environment(), _assume_hotpotqa_data_present(), _fake_missing(), Tests for scripts/run_overnight.py's provider-aware --dry-run validation., data/hotpotqa/questions.jsonl is gitignored and only ever present     locally af, run, _Settings (+8 more)

### Community 22 - "Validator & Query Fusion (OpenRouter debt)"
Cohesion: 0.22
Nodes (15): Validates proposed RAG configs against developer-defined search space constraint, Check proposed config against allowed values, parser/retriever availability, and, validator_node(), _build_query_fusion_llm(), _base(), _blocking_settings(), Settings, test_auto_merging_requires_hierarchical_parser() (+7 more)

### Community 23 - "Smoke Tester & Reflection"
Cohesion: 0.18
Nodes (10): Smoke test validates that retrieval pipeline runs and returns non-empty results., Periodic experiment reflection and pattern extraction.  Summarizes recent succes, _call_summary_llm_sync_fallback(), Apply sliding-window compression to an OpenAI-style messages list.      Keeps th, Graceful fallback when the LLM call fails: concatenate + truncate at a sentence, sliding_window_compress_messages(), get_logger(), Structured logging configuration using structlog with stdlib integration.  Sets (+2 more)

### Community 24 - "Function Trace Utility"
Cohesion: 0.21
Nodes (15): close_trace(), _emit_trace_entry(), _format_call_args(), Function-level trace logging for deep debugging of the scientist pipeline.  Prov, Bind actual args to parameter names and repr each value., Async trace implementation., Sync trace implementation., Write a single trace line. (+7 more)

### Community 25 - "Overnight Display & Eval Loop"
Cohesion: 0.20
Nodes (13): _run(), fmt_elapsed(), log_event(), print_config_table(), print_metrics(), Rich terminal UI utilities for live workflow event display and experiment metric, empty_metrics(), evaluate_final_best() (+5 more)

### Community 26 - "Scientist Prompt Builder"
Cohesion: 0.15
Nodes (14): build_scientist_prompt(), Scientist LLM prompt construction for RAG config generation.  Builds context-awa, Trim recent experiments to fit token budget, prioritizing newest whole lines., Construct full scientist prompt with mode, history, constraints, and indexed con, _truncate_history(), count_tokens(), Count tokens in text using the shared tokenizer., Empty history truncates to an empty string, not an error. (+6 more)

### Community 27 - "Registry-Dict Pattern (Model Catalog)"
Cohesion: 0.20
Nodes (13): Registry-dict-over-if/elif dispatch convention, build_embedding_model(), build_reranker(), EMBEDDING_CATALOG (src/core/model_catalog.py), Instantiate the concrete embedding model for `model_id` via its catalog provider, Instantiate the concrete reranker for `reranker_name` via its catalog provider., RERANKER_CATALOG (src/core/model_catalog.py), _PROVIDER_BUILDERS (src/core/provider_factory.py) (+5 more)

### Community 28 - "Config Hash Repository"
Cohesion: 0.15
Nodes (8): ConfigHashRepository, Connection, DAO for config_hashes table — tracks seen configurations and their scores., Initialize with optional connection; if None, creates connections on-demand., Insert a new config hash with optional first_seen timestamp (defaults to now)., Update score to the max of current and new value (prevents score decrease)., Return set of all tracked config hashes., Delete config hashes older than ttl_days with no score, unless referenced by act

### Community 29 - "Reranking & Hybrid Retrievers"
Cohesion: 0.32
Nodes (5): BaseRetriever, NodeWithScore, QueryBundle, RerankingRetriever, WeightedHybridRetriever

### Community 30 - "DI Protocol Interfaces (Docs)"
Cohesion: 0.24
Nodes (11): Database (Class), ExperimentRepository (Class), IChromaClientFactory Protocol, ICostTracker Protocol, IDatabase Protocol, IEmbeddingService Protocol, ILLMClient Protocol, IModelRoutingProvider Protocol (+3 more)

### Community 31 - "Evaluator Architecture Docs"
Cohesion: 0.31
Nodes (10): _build_qrels_and_run, build_ragas_embeddings, build_ragas_llm, build_ragas_metrics, _evaluate_ir_fallback, evaluate_ir_metrics, Evaluator Component Architecture & Code Breakdown, evaluator_node (+2 more)

### Community 32 - "Baseline Fetch & Question Loader"
Cohesion: 0.31
Nodes (7): main(), Data loading utilities. Exposes functions for loading evaluation datasets from H, load_eval_question_items(), load_eval_questions(), Load evaluation questions from HotpotQA dataset in JSONL format., Load first n question items from JSONL, extracting id, question, answer, support, Load first n questions and answers separately. Returns (questions, answers) tupl

### Community 33 - "God Nodes & Constructor Injection Principle"
Cohesion: 0.22
Nodes (9): Prefer constructor-injected dependencies over module-level singletons, Avoid third near-duplicate ILLMClient Protocol implementation, ICostTracker (god node), ILLMClient (god node), Provider (god node), RAGConfig (god node), Codebase knowledge graph (graphify-generated, graph.html, GRAPH_REPORT.md), _default_tracker singleton (src/storage/cost_tracker.py) (+1 more)

### Community 34 - "Model Routing Config"
Cohesion: 0.22
Nodes (9): coder model route (deepseek/deepseek-v4-flash), conversation_summary model route, Model Routing Configuration, rag_generator_fallback route, rag_generator_primary route, ragas_embedding_model route (openai/text-embedding-3-small), ragas_judge route (qwen/qwen3.5-flash-02-23), smoke_tester route (qwen/qwen3.5-flash-02-23) (+1 more)

### Community 35 - "Reflection Node Docs"
Cohesion: 0.25
Nodes (9): reflection model route (deepseek/deepseek-v4-pro), Crash Resilience via SQLite Checkpointer, Autonomous RAG Optimizer Step-by-Step Overnight Run Guide, reflection_node (overnight guide), scientist_node, State Isolation Architecture Rationale, validator_node, reflection_node (architecture breakdown) (+1 more)

### Community 36 - "Acceptance/Indexer/Reporter Node Docs"
Cohesion: 0.22
Nodes (9): report_writer model route, acceptance_node (overnight guide), indexer_node, recorder_node, report_writer_node, smoke_test_node, index_builder.py, indexer_node (architecture breakdown) (+1 more)

### Community 37 - "CI/Pre-commit/PR Checklist"
Cohesion: 0.28
Nodes (9): CI workflow (.github/workflows/ci.yml): ruff, black, mypy, pytest, Formatting with Black (line length 100, py3.11), Type checking with Mypy (non-blocking in CI), Linting with Ruff (E, F, I, UP, B rule sets), Install Pre-commit Hooks section, Testing guidelines (pytest, pytest-asyncio, pytest-mock, mocked external services), PR Checklist (no hardcoding, file placement, black, ruff/pytest), pre-commit black (format) hook (+1 more)

### Community 38 - "Export Experiments Script"
Cohesion: 0.25
Nodes (7): Path, export_data(), main(), Export experiment history from SQLite to CSV or JSON., Query experiments database and write out the result to the designated format., Regression test: config.loader.load_settings()'s key validation must     never, test_load_settings_accepts_every_search_space_field()

### Community 39 - "OpenRouter Hardcoding Bug Class"
Cohesion: 0.25
Nodes (8): OPENROUTER_API_KEY / provider-hardcoding recurring bug class, How to add new evaluation metrics, ThreadPool isolation for RAGAS (ThreadPoolExecutor + nest_asyncio), Resilient Evaluation Threading (RAGAS offloaded via nest_asyncio + ThreadPoolExecutors), src/evaluator/ir_metrics.py (IR metrics computation), src/evaluator/ragas_setup.py (fixed OpenRouter hardcoding), CohereRerank/OPENROUTER_API_KEY check (src/orchestrator/validator.py, unfixed), _build_query_fusion_llm() (src/rag_pipeline/retriever.py, unfixed OpenRouter hardcoding)

### Community 40 - "run_overnight Entry & Pricing Loader"
Cohesion: 0.29
Nodes (4): load_openai_pricing(), Load openai_pricing.yaml: model_id -> (usd_per_million_input, usd_per_million_ou, Return the environment variable name `provider_name`'s builder reads.      Raise, required_env_var()

### Community 41 - "Run Settings & Budget Guard Docs"
Cohesion: 0.29
Nodes (7): cost_hard_ceiling_usd (10.00, HARD STOP), Explore/Exploit Parameters, run.llm_provider setting, ragas_audit_policy: competitive, Overnight Run Settings Configuration, budget_guard_node, deduplicator_node

### Community 42 - "Contributing Architecture Overview"
Cohesion: 0.29
Nodes (7): LangGraph state machine loop: Scientist -> Validator -> Deduplicator -> Budget Guard -> Indexer -> Smoke Test -> Evaluator -> Acceptance -> Recorder -> Reflection, How to add a new guardrail node, How to modify the Hypothesis Generator (Scientist node), Protocol-based DI via Provider container (src/core/), Pydantic everywhere (RAGConfig, SingleRunMetrics, AggregatedMetrics, ExperimentRecord), Documentation links (project_architecture_breakdown.md, evaluator_code_breakdown.md, developer_guide.md, overnight_execution_guide.md, CONTRIBUTING.md), Key features (Autonomous Experimentation Loop, LangGraph Orchestration, Strict Budget Guarding, Resilient Evaluation Threading, SQLite Storage)

### Community 43 - "Scientist Prompt I/O Pairing"
Cohesion: 0.33
Nodes (7): Config Field Pairing Rules, Scientist Brain: Input and Output, Config Field Pairing Rules (prompt), Scientist v1 System Prompt, Budget Guard Security Scrutiny Requirement, LLM Prompt Injection Concern, Security Policy (SECURITY.md)

### Community 44 - "Cost Tracker Injection Tests"
Cohesion: 0.33
Nodes (3): _FakeCostTracker, test_report_cost_falls_back_to_module_singleton_when_no_tracker_injected(), test_report_cost_uses_injected_tracker_not_module_singleton()

### Community 45 - "Baseline Config & Architecture Docs"
Cohesion: 0.33
Nodes (6): Immutable Baseline Config, scientist model route (deepseek/deepseek-v4-pro), AggregatedMetrics (BaseModel), ExperimentRecord (BaseModel), RAGConfig (BaseModel), SingleRunMetrics (BaseModel)

### Community 46 - "CI Workflow Steps"
Cohesion: 0.33
Nodes (6): Black Format Check Step, CI GitHub Actions Workflow, lint-and-test Job, Mypy Type Check Step (non-blocking), Pytest Step, Ruff Lint Step

### Community 47 - "No-op DB Context Manager"
Cohesion: 0.33
Nodes (3): _NoopContext, Connection, Context manager that returns a provided connection without closing it.

### Community 48 - "Logger Setup & Test Fixtures"
Cohesion: 0.40
Nodes (5): Configure structlog with stdlib integration and suppress noisy third-party libs., setup_logging(), Global test fixtures: logging setup and teardown., Initializes logging before each test., _setup_logging()

### Community 49 - "Search Space Constraint Tests"
Cohesion: 0.53
Nodes (5): _make_test_settings(), Settings, test_brain_prompt_incorporates_constraints(), test_candidates_filtering(), test_validator_enforces_search_space()

### Community 50 - "Acceptance Criteria Docs"
Cohesion: 0.40
Nodes (5): Acceptance Criteria (min_weighted_score_improvement, variance, regression), _accept_best_config, acceptance_node, acceptance_node (architecture breakdown), evaluator_node (architecture breakdown)

### Community 51 - "Ruflo/Claude-Flow Agent Config (AGENTS.md)"
Cohesion: 0.50
Nodes (4): 3-Tier Model Routing (Agent Booster / Haiku / Sonnet-Opus), SendMessage-First Agent Comms Pattern, Ruflo Codex Configuration (AGENTS.md), Swarm & Routing Configuration

### Community 52 - "HotpotQA Data Enrichment Script"
Cohesion: 0.50
Nodes (3): main(), Backfill supporting_titles into data/hotpotqa/questions.jsonl.  Fetches metadata, Load existing questions, fetch HotpotQA metadata, and enrich with supporting_tit

## Knowledge Gaps
- **67 isolated node(s):** `autonomous-rag-optimizer`, `setup_environment.sh script`, `Start run_overnight.py`, `End Run`, `Return Final Score` (+62 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **21 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `RAGConfig` connect `Embedding & Collection Cache` to `Baseline Fetch & Question Loader`, `Scientist Config Exploration`, `RAG Generator & Pipeline`, `Experiment & Metrics Models`, `Evaluator Node & RAGAS Runner`, `Validator & Query Fusion (OpenRouter debt)`, `Smoke Tester & Reflection`, `Overnight Display & Eval Loop`, `Registry-Dict Pattern (Model Catalog)`, `Reranking & Hybrid Retrievers`?**
  _High betweenness centrality (0.106) - this node is a cross-community bridge._
- **Why does `Provider` connect `DI Interfaces & Protocols` to `Embedding & Collection Cache`, `Provider Factory & Budget Guard`, `LangGraph Budget Guard & State`, `Scientist Config Exploration`, `RAG Generator & Pipeline`, `Smoke Tester & Reflection`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Why does `OpenAIClient` connect `OpenAI Client Adapter` to `DI Interfaces & Protocols`, `God Nodes & Constructor Injection Principle`, `Provider Factory & Budget Guard`, `run_overnight Entry & Pricing Loader`, `Cost Tracker Injection Tests`, `OpenAI Client Tests`, `run_overnight Environment Validation`, `Smoke Tester & Reflection`?**
  _High betweenness centrality (0.074) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `RAGConfig` (e.g. with `ExperimentRecord` and `RerankingRetriever`) actually correct?**
  _`RAGConfig` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `Provider` (e.g. with `IChromaClientFactory` and `ICostTracker`) actually correct?**
  _`Provider` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `OpenAIClient` (e.g. with `ICostTracker` and `_FakeAsyncClient`) actually correct?**
  _`OpenAIClient` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 21 inferred relationships involving `ICostTracker` (e.g. with `Provider` and `OpenAIClient`) actually correct?**
  _`ICostTracker` has 21 INFERRED edges - model-reasoned connections that need verification._