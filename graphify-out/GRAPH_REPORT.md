# Graph Report - .  (2026-07-15)

## Corpus Check
- 122 files · ~92,125 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1018 nodes · 2248 edges · 50 communities (38 shown, 12 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 154 edges (avg confidence: 0.64)
- Token cost: 0 input · 211,267 output

## Community Hubs (Navigation)
- Embedding & Collection Cache
- Scientist Config Exploration
- OpenAI Client Adapter
- Config Loader & Settings
- Baseline Retrieval & Data Loading
- Model Routing Config
- Model Catalog & Builders
- Run/Eval/Acceptance Settings Schemas
- DI Interfaces & Protocols
- Overnight Run Pipeline Flowchart
- LangGraph Budget Guard & State
- Evaluator Node & RAGAS Runner
- SQLite Database & Deduplicator
- Acceptance Scoring Logic
- Config Hash Repository
- LLM Model Config Schemas
- OpenRouter Client Adapter
- Cost Tracker Protocol & DI Tests
- Provider Factory
- LLM Client Interface & Tests
- IR Metrics Evaluation
- Deduplicator Node & Config Helpers
- Cost Tracker Core
- Mock Test Doubles
- Experiment Recorder
- OpenRouter Client Tests
- RAGAS JSON Repair Utilities
- DI Protocol Interfaces Overview
- Ruflo/Claude-Flow Agent Config Docs
- Multi-Provider Handoff Rationale
- Evaluator Architecture Docs
- Acceptance Criteria & Explore/Exploit Docs
- Developer Guide & Contributing Docs
- CI Workflow (Lint/Test)
- No-op DB Context Manager
- HotpotQA Data Enrichment Script
- Reranking & Hybrid Retrievers
- GitHub Issue Templates
- Environment Setup Script
- Async Test Loop Setup
- Storage Layer Init
- Utils Package Init
- Docker Compose Config
- Budget Guard Node Docs
- Config Hash Repository Class
- Generator Module
- Run Repository Class
- Project Root Marker

## God Nodes (most connected - your core abstractions)
1. `RAGConfig` - 76 edges
2. `Provider` - 53 edges
3. `OpenAIClient` - 42 edges
4. `ICostTracker` - 36 edges
5. `ILLMClient` - 28 edges
6. `build_graph()` - 26 edges
7. `get_logger()` - 25 edges
8. `Database` - 21 edges
9. `get_total()` - 19 edges
10. `run_single_eval()` - 18 edges

## Surprising Connections (you probably didn't know these)
- `Ruflo Claude Code Configuration (CLAUDE.md)` --semantically_similar_to--> `Ruflo Codex Configuration (AGENTS.md)`  [INFERRED] [semantically similar]
  CLAUDE.md → AGENTS.md
- `SendMessage-First Agent Comms Pattern (Claude)` --semantically_similar_to--> `SendMessage-First Agent Comms Pattern`  [INFERRED] [semantically similar]
  CLAUDE.md → AGENTS.md
- `Swarm & Routing Configuration` --semantically_similar_to--> `Self-Learning Router (hooks route)`  [INFERRED] [semantically similar]
  AGENTS.md → docs/ruflo_features.md
- `ThreadPool Isolation for RAGAS` --semantically_similar_to--> `ThreadPool Solution for RAGAS/asyncio Deadlock`  [INFERRED] [semantically similar]
  CONTRIBUTING.md → docs/developer_guide.md
- `Strict Budget Guarding Feature` --semantically_similar_to--> `Budget Guard Security Scrutiny Requirement`  [INFERRED] [semantically similar]
  README.md → SECURITY.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **System Initialization and Baseline Setup** — docs_mermaid_diagram_2_start_run_overnight_py, docs_mermaid_diagram_2_initialize_sqlite_db_wal_mode, docs_mermaid_diagram_2_initialize_cost_tracker, docs_mermaid_diagram_2_load_config_baseline_settings, docs_mermaid_diagram_2_baseline_cached, docs_mermaid_diagram_2_run_baseline_evaluation, docs_mermaid_diagram_2_store_baseline_score_in_db, docs_mermaid_diagram_2_initialize_graph_state [EXTRACTED 1.00]
- **Autonomous LangGraph Execution Loop** — docs_mermaid_diagram_2_scientist_propose_rag_config, docs_mermaid_diagram_2_validator_schema_bounds_check, docs_mermaid_diagram_2_deduplicator_config_hash_check, docs_mermaid_diagram_2_budget_guard_api_cost_check, docs_mermaid_diagram_2_index_builder_chromadb, docs_mermaid_diagram_2_smoke_tests_basic_queries, docs_mermaid_diagram_2_evaluator_node, docs_mermaid_diagram_2_failhandler, docs_mermaid_diagram_2_acceptance_score_comparison, docs_mermaid_diagram_2_recorder_persist_results, docs_mermaid_diagram_2_reflection_pattern_analysis, docs_mermaid_diagram_2_max_experiments_reached, docs_mermaid_diagram_2_report, docs_mermaid_diagram_2_end_run [EXTRACTED 1.00]
- **Evaluator Execution Pipeline** — docs_mermaid_diagram_2_evaluator_entry, docs_mermaid_diagram_2_select_evaluation_questions, docs_mermaid_diagram_2_run_evaluations, docs_mermaid_diagram_2_aggregate_results_median_stddev, docs_mermaid_diagram_2_return_final_score, docs_mermaid_diagram_2_async_retrieval_aiohttp, docs_mermaid_diagram_2_single_run_evaluation, docs_mermaid_diagram_2_thread_pool_execution, docs_mermaid_diagram_2_ragas_metrics_computation, docs_mermaid_diagram_2_llm_scoring_faithfulness_recall, docs_mermaid_diagram_2_compute_run_metrics [EXTRACTED 1.00]
- **LangGraph Autonomous Optimization Loop** — docs_overnight_execution_guide_scientist_node, docs_overnight_execution_guide_validator_node, docs_overnight_execution_guide_deduplicator_node, docs_overnight_execution_guide_budget_guard_node, docs_overnight_execution_guide_indexer_node, docs_overnight_execution_guide_smoke_test_node, docs_overnight_execution_guide_recorder_node, docs_overnight_execution_guide_acceptance_node, docs_overnight_execution_guide_reflection_node, docs_overnight_execution_guide_report_writer_node [EXTRACTED 1.00]
- **Protocol-Based DI Container Pattern** — docs_project_architecture_breakdown_provider, docs_project_architecture_breakdown_icosttracker, docs_project_architecture_breakdown_illmclient, docs_project_architecture_breakdown_iembeddingservice, docs_project_architecture_breakdown_idatabase [EXTRACTED 0.90]
- **Multi-Provider Embedding/Reranker Factory Design Decision** — docs_multi_provider_handoff_reranker_singleton_mismatch, docs_multi_provider_handoff_embedding_model_per_experiment_problem, docs_multi_provider_handoff_factory_style_wiring_option, docs_project_architecture_breakdown_ragconfig [INFERRED 0.85]

## Communities (50 total, 12 thin omitted)

### Community 0 - "Embedding & Collection Cache"
Cohesion: 0.06
Nodes (61): build_embedding_model(), Instantiate the concrete embedding model for `model_id` via its catalog provider, bm25_node_count(), build_embed_model(), cache_is_complete(), effective_corpus_limit(), expensive_parser_builds_allowed(), load_bm25_engine() (+53 more)

### Community 1 - "Scientist Config Exploration"
Cohesion: 0.06
Nodes (64): scientist_node(), _should_force_reranker_probe(), _should_run_structured_exploration(), _available_index_configs(), _combine_candidates(), get_fallback_candidates(), get_reranker_probe_candidates(), get_structured_exploration_candidates() (+56 more)

### Community 2 - "OpenAI Client Adapter"
Cohesion: 0.06
Nodes (50): Provider-aware --dry-run checks: required key present, and for     "openai" spe, _validate_environment(), _build_payload(), call_openai(), OpenAIClient, OpenAIError, OpenAINonRetryableError, OpenAIRateLimitError (+42 more)

### Community 3 - "Config Loader & Settings"
Cohesion: 0.05
Nodes (59): invalidate_all(), load_all(), load_baseline_config(), load_model_routing(), load_openai_pricing(), load_settings(), Settings, Load configuration from YAML files with caching.  Provides functions to load and (+51 more)

### Community 4 - "Baseline Retrieval & Data Loading"
Cohesion: 0.08
Nodes (33): BaseRetriever, main(), Data loading utilities. Exposes functions for loading evaluation datasets from H, load_eval_question_items(), load_eval_questions(), Load evaluation questions from HotpotQA dataset in JSONL format., Load first n question items from JSONL, extracting id, question, answer, support, Load first n questions and answers separately. Returns (questions, answers) tupl (+25 more)

### Community 5 - "Model Routing Config"
Cohesion: 0.05
Nodes (48): Immutable Baseline Config, coder model route (deepseek/deepseek-v4-flash), conversation_summary model route, Model Routing Configuration, rag_generator_fallback route, rag_generator_primary route, ragas_embedding_model route (openai/text-embedding-3-small), ragas_judge route (qwen/qwen3.5-flash-02-23) (+40 more)

### Community 6 - "Model Catalog & Builders"
Cohesion: 0.06
Nodes (31): AsyncOpenAI, BaseEmbedding, BaseNodePostprocessor, _build_openrouter_embedding(), _build_openrouter_reranker(), build_reranker(), embedding_dimensions(), ValueError (+23 more)

### Community 7 - "Run/Eval/Acceptance Settings Schemas"
Cohesion: 0.09
Nodes (42): AcceptanceSettings, EvalSettings, ExploreExploitSettings, BaseModel, Configuration schemas for overnight experiment runs, evaluation, acceptance, and, Top-level settings container: aggregates all run, eval, acceptance, and explorat, Budget and concurrency limits: max_experiments, max_hours, cost ceiling, failure, Evaluation setup: question counts, RAGAS metrics, timeouts, smoke testing, audit (+34 more)

### Community 8 - "DI Interfaces & Protocols"
Cohesion: 0.09
Nodes (20): Protocol, Core DI interfaces and container. Exposes all service abstractions and the Provi, IChromaClientFactory, IDatabase, IEmbeddingService, ILlamaIndexEmbeddingAdapter, IModelRoutingProvider, IRagasFactory (+12 more)

### Community 9 - "Overnight Run Pipeline Flowchart"
Cohesion: 0.07
Nodes (34): Acceptance: Score Comparison, Aggregate Results (Median, StdDev), Async Retrieval (aiohttp), Baseline Cached? (decision), Budget Guard: API Cost Check, Compute Run Metrics, Deduplicator: Config Hash Check, End Run (+26 more)

### Community 10 - "LangGraph Budget Guard & State"
Cohesion: 0.11
Nodes (27): BaseCheckpointSaver, CompiledStateGraph, budget_guard_node(), Cost-based execution guard that halts the workflow if budget ceiling is exceeded, Decides whether to continue running based on total cost.      Evaluates `total_c, _after_budget_guard(), _after_deduplicator(), _after_evaluator() (+19 more)

### Community 11 - "Evaluator Node & RAGAS Runner"
Cohesion: 0.13
Nodes (24): load_env(), Extract API keys from environment variables.      OPENROUTER_API_KEY is required, LLMResult, OpenAIEmbeddings, evaluator_node(), RAGAS evaluation orchestration and IR metric computation.  Runs full evaluatio, Extract mean of column from pandas DataFrame, returning 0.0 if missing or NaN., Run IR metrics immediately, then conditionally run RAGAS metrics with retry logi (+16 more)

### Community 12 - "SQLite Database & Deduplicator"
Cohesion: 0.10
Nodes (15): Experiment deduplication and config hash tracking.  Detects repeated configurati, Database, SQLite connection manager and schema initialisation. WAL mode is MANDATORY for s, Manages SQLite connection with WAL mode for safe async access., Initialize database with optional custom path., Create tables, set pragma settings, and backfill config_hashes from existing exp, Context manager for async database connection., init_db() (+7 more)

### Community 13 - "Acceptance Scoring Logic"
Cohesion: 0.14
Nodes (19): _accept_best_config(), acceptance_node(), Scoring and acceptance logic for RAG configuration experiments.  Evaluates propo, Determines if the proposed config should be accepted as the new best.     Uses m, Log acceptance and return updated state with new best config and metrics., ExperimentRecord, BaseModel, Experiment tracking and results models for RAG configuration experiments. (+11 more)

### Community 14 - "Config Hash Repository"
Cohesion: 0.10
Nodes (14): ConfigHashRepository, Connection, DAO for config_hashes table — tracks seen configurations and their scores., Initialize with optional connection; if None, creates connections on-demand., Insert a new config hash with optional first_seen timestamp (defaults to now)., Update score to the max of current and new value (prevents score decrease)., Return set of all tracked config hashes., Delete config hashes older than ttl_days with no score, unless referenced by act (+6 more)

### Community 15 - "LLM Model Config Schemas"
Cohesion: 0.19
Nodes (20): ModelConfig, Model configuration schemas for LLM providers and agent role assignments.  Defin, LLM configuration: model_id, reasoning effort, tokens, temperature, format optio, _build_openrouter_extra_body(), _build_openrouter_model_kwargs(), Extract model kwargs (e.g. response format) from judge config., Build OpenRouter-specific request body options (e.g. reasoning exclusion)., install_ragas_output_parser_compat_patch() (+12 more)

### Community 16 - "OpenRouter Client Adapter"
Cohesion: 0.15
Nodes (14): test_brain(), _build_payload(), call_openrouter(), compute_cost(), OpenRouterClient, OpenRouterError, OpenRouterNonRetryableError, OpenRouterRateLimitError (+6 more)

### Community 17 - "Cost Tracker Protocol & DI Tests"
Cohesion: 0.13
Nodes (6): ICostTracker, MockChromaFactory, MockDatabase, MockModelRoutingProvider, MockRagasFactory, Tests demonstrating dependency injection with mock providers.

### Community 18 - "Provider Factory"
Cohesion: 0.12
Nodes (15): _build_openai_provider(), _build_openrouter_provider(), Any, ValueError, Resolves `settings.run.llm_provider` to a fully-wired Provider.  Single seam for, Return the environment variable name `provider_name`'s builder reads.      Raise, required_env_var(), _unknown_provider_error() (+7 more)

### Community 19 - "LLM Client Interface & Tests"
Cohesion: 0.21
Nodes (15): ILLMClient, Send a chat-completion-style request and return the response.          `reasonin, build_provider(), Construct the `Provider` for `settings.run.llm_provider`.      Raises `ValueErro, Tests for provider selection via src.core.provider_factory.build_provider., The bug the audit flagged: without this, the client could silently     report co, run, _Settings (+7 more)

### Community 20 - "IR Metrics Evaluation"
Cohesion: 0.16
Nodes (16): _build_qrels_and_run(), _evaluate_ir_fallback(), evaluate_ir_metrics(), _mean(), _mrr(), _ndcg(), Information Retrieval metrics evaluation (recall, precision, NDCG, MRR).  Comp, Compute Normalized Discounted Cumulative Gain. (+8 more)

### Community 21 - "Deduplicator Node & Config Helpers"
Cohesion: 0.16
Nodes (15): deduplicator_node(), _fetch_best_historical_record(), Retrieve best experiment result for a config hash., Check if config was already tried; block duplicate or mark success; clean stale, logical_config(), Configuration utilities for filtering and processing config dicts., Filter out private (underscore-prefixed) keys from a config dict., get_config_hash() (+7 more)

### Community 22 - "Cost Tracker Core"
Cohesion: 0.20
Nodes (16): add_cost(), BudgetExceededError, get_total(), initialize(), Exception, All API calls MUST go through src/utils/openrouter.py, which calls add_cost() af, Tests for the global cost tracker: accumulation, hard ceiling, and warning thres, Exceeding hard_ceiling raises instead of silently continuing to spend. (+8 more)

### Community 23 - "Mock Test Doubles"
Cohesion: 0.18
Nodes (6): MockCostTracker, MockLLMClient, scientist_node produces a proposal when LLM returns valid JSON., Verify MockCostTracker satisfies ICostTracker protocol., Verify MockLLMClient satisfies ILLMClient protocol., TestProvider

### Community 24 - "Experiment Recorder"
Cohesion: 0.19
Nodes (12): _config_summary(), Experiment recording and state tracking for RAG optimization runs.  Logs experim, Format config dict into human-readable summary for logging patterns., Persist experiment result to database and update run statistics., recorder_node(), ConfigHash, Experiment, HistoricalRecord (+4 more)

### Community 25 - "OpenRouter Client Tests"
Cohesion: 0.22
Nodes (8): _extract_reasoning_text(), _FakeCostTracker, The real bug the audit flagged: cost must go to the tracker the client     was, Backward compat: constructing without a tracker (e.g. the module-level     _def, test_extract_reasoning_text_from_reasoning_details(), test_extract_reasoning_text_from_reasoning_field(), test_report_cost_falls_back_to_module_singleton_when_no_tracker_injected(), test_report_cost_uses_injected_tracker_not_module_singleton()

### Community 26 - "RAGAS JSON Repair Utilities"
Cohesion: 0.35
Nodes (11): _extract_binary_field(), _extract_quoted_field(), _extract_reason(), _fallback_ragas_output(), _json_repair_candidates(), _looks_like_recall_item(), _normalize_ragas_json(), _parse_ragas_output_string_compat() (+3 more)

### Community 27 - "DI Protocol Interfaces Overview"
Cohesion: 0.24
Nodes (11): Database (Class), ExperimentRepository (Class), IChromaClientFactory Protocol, ICostTracker Protocol, IDatabase Protocol, IEmbeddingService Protocol, ILLMClient Protocol, IModelRoutingProvider Protocol (+3 more)

### Community 28 - "Ruflo/Claude-Flow Agent Config Docs"
Cohesion: 0.22
Nodes (10): 3-Tier Model Routing (Agent Booster / Haiku / Sonnet-Opus), SendMessage-First Agent Comms Pattern, Ruflo Codex Configuration (AGENTS.md), Swarm & Routing Configuration, SendMessage-First Agent Comms Pattern (Claude), Ruflo Claude Code Configuration (CLAUDE.md), AgentDB (HNSW indexing memory layer), AIDefence Safety Scanner (+2 more)

### Community 29 - "Multi-Provider Handoff Rationale"
Cohesion: 0.24
Nodes (10): Manual Pricing Update Rationale, OpenAI Pricing Table (USD per million tokens), Cost Tracker Constructor Injection Decision, ILlamaIndexEmbeddingAdapter Protocol, IReranker Protocol, Multi-Provider Architecture Work Session Handoff, OpenAIClient (ILLMClient impl), OpenRouterClient (ILLMClient impl) (+2 more)

### Community 30 - "Evaluator Architecture Docs"
Cohesion: 0.31
Nodes (10): _build_qrels_and_run, build_ragas_embeddings, build_ragas_llm, build_ragas_metrics, _evaluate_ir_fallback, evaluate_ir_metrics, Evaluator Component Architecture & Code Breakdown, evaluator_node (+2 more)

### Community 31 - "Acceptance Criteria & Explore/Exploit Docs"
Cohesion: 0.22
Nodes (9): Acceptance Criteria (min_weighted_score_improvement, variance, regression), Explore/Exploit Parameters, run.llm_provider setting, ragas_audit_policy: competitive, Overnight Run Settings Configuration, _accept_best_config, acceptance_node, acceptance_node (architecture breakdown) (+1 more)

### Community 32 - "Developer Guide & Contributing Docs"
Cohesion: 0.29
Nodes (8): Contributor Covenant Code of Conduct, LangGraph Orchestration Architecture Overview, Contributing to Autonomous RAG Optimizer Guide, Project Structure (src layout), Protocol-based Dependency Injection, ThreadPool Isolation for RAGAS, Developer Guide, ThreadPool Solution for RAGAS/asyncio Deadlock

### Community 33 - "CI Workflow (Lint/Test)"
Cohesion: 0.33
Nodes (6): Black Format Check Step, CI GitHub Actions Workflow, lint-and-test Job, Mypy Type Check Step (non-blocking), Pytest Step, Ruff Lint Step

### Community 34 - "No-op DB Context Manager"
Cohesion: 0.33
Nodes (3): _NoopContext, Connection, Context manager that returns a provided connection without closing it.

### Community 35 - "HotpotQA Data Enrichment Script"
Cohesion: 0.50
Nodes (3): main(), Backfill supporting_titles into data/hotpotqa/questions.jsonl.  Fetches metadata, Load existing questions, fetch HotpotQA metadata, and enrich with supporting_tit

## Knowledge Gaps
- **44 isolated node(s):** `autonomous-rag-optimizer`, `setup_environment.sh script`, `Start run_overnight.py`, `End Run`, `Return Final Score` (+39 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `RAGConfig` connect `Embedding & Collection Cache` to `Scientist Config Exploration`, `Config Loader & Settings`, `Baseline Retrieval & Data Loading`, `Model Catalog & Builders`, `Run/Eval/Acceptance Settings Schemas`, `Evaluator Node & RAGAS Runner`, `Acceptance Scoring Logic`?**
  _High betweenness centrality (0.114) - this node is a cross-community bridge._
- **Why does `Provider` connect `DI Interfaces & Protocols` to `Embedding & Collection Cache`, `Scientist Config Exploration`, `Baseline Retrieval & Data Loading`, `LangGraph Budget Guard & State`, `Cost Tracker Protocol & DI Tests`, `Provider Factory`, `LLM Client Interface & Tests`, `Mock Test Doubles`?**
  _High betweenness centrality (0.104) - this node is a cross-community bridge._
- **Why does `OpenAIClient` connect `OpenAI Client Adapter` to `LLM Client Interface & Tests`, `Cost Tracker Protocol & DI Tests`, `Provider Factory`, `Config Loader & Settings`?**
  _High betweenness centrality (0.059) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `RAGConfig` (e.g. with `ExperimentRecord` and `RerankingRetriever`) actually correct?**
  _`RAGConfig` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `Provider` (e.g. with `IChromaClientFactory` and `ICostTracker`) actually correct?**
  _`Provider` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `OpenAIClient` (e.g. with `ICostTracker` and `_FakeAsyncClient`) actually correct?**
  _`OpenAIClient` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 21 inferred relationships involving `ICostTracker` (e.g. with `Provider` and `OpenAIClient`) actually correct?**
  _`ICostTracker` has 21 INFERRED edges - model-reasoned connections that need verification._