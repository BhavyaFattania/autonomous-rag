# Graph Report - .  (2026-07-24)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1586 nodes · 3098 edges · 120 communities (79 shown, 41 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 195 edges (avg confidence: 0.6)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `98387d10`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- __init__.py
- pipeline.py
- openrouter.py
- retriever.py
- DashboardState
- Model Routing Configuration
- Database
- Evaluator (module)
- NodeEventRepository
- OpenAIClient
- devDependencies
- Provider
- scorer.py
- CONTRIBUTING.md
- run_overnight.py
- EventBus
- adapt
- logger.py
- build_graph
- test_ragas_runner_parser.py
- compilerOptions
- RunRepository
- OpenRouterEmbedding
- ExperimentRepository
- types.ts
- history.ts
- App.tsx
- ICostTracker
- settings.py
- ILLMClient
- compilerOptions
- report_writer.py
- deduplicator.py
- cost_tracker.py
- test_openai_client.py
- RAGConfig
- validator_node
- provider_factory.py
- ir_metrics.py
- proposal.py
- reflection.py
- function_trace.py
- test_run_overnight_validate.py
- test_budget_enforcement.py
- create_app
- MockCostTracker
- Overnight Execution Guide
- prompt_builder.py
- ConfigHashRepository
- test_run_overnight_web_wiring.py
- test_brain.py
- test_scorer.py
- model_catalog.py
- test_event_log.py
- json_repair.py
- compute_config_diff
- test_indexer_node_progress.py
- Autonomous RAG Project Architecture Breakdown
- react
- test_ragas_runner.py
- history.py
- Path
- split_graph_html.py
- Claude Code Configuration Rules
- scientist_node
- _FakeCostTracker
- RecentEventsCard.tsx
- setup_logging
- ExperimentTimelineDrawer.tsx
- test_dependencies_installed.py
- Ruflo Codex Configuration (AGENTS.md)
- enrich_hotpotqa_questions.py
- _resolve_api_key
- index_builder.py
- configDiff.ts
- tsconfig.json
- Constructor-Injected Dependencies over Module Singletons Principle
- Manual Pricing Update Rationale
- reflection_node (architecture breakdown)
- RerankingRetriever
- Frontend HTML Entry Point (#root / main.tsx)
- Dependency Review Job
- setup_environment.sh
- test_loop.py
- __init__.py
- __init__.py
- Build & Test Check Set
- Contributor Covenant Code of Conduct
- Docker Compose Config (empty services)
- budget_guard_node (architecture breakdown)
- ConfigHashRepository (Class)
- generator.py
- RunRepository (Class)
- Favicon (Purple Abstract Mark)
- Icon Sprite Sheet (Bluesky, Discord, Documentation, GitHub, Social, X)
- Hero Banner Image
- React Logo (Vite scaffold asset)
- Feature Request Issue Template
- PR Checklist (no hardcoding, file placement, black, ruff/pytest)
- NodeWithScore
- PersistentClient
- autonomous-rag-optimizer
- pre-commit black (format) hook
- pre-commit-hooks bundle (trailing-whitespace, end-of-file-fixer, check-yaml, check-toml, check-merge-conflict, check-added-large-files)
- pre-commit ruff (lint) hook
- QueryBundle
- Path
- ValueError
- PersistentClient
- PersistentClient
- ExperimentEvent
- Exception
- Path
- Exception

## God Nodes (most connected - your core abstractions)
1. `EventBus` - 54 edges
2. `OpenAIClient` - 40 edges
3. `Database` - 36 edges
4. `Provider` - 34 edges
5. `DashboardState` - 32 edges
6. `ICostTracker` - 30 edges
7. `RAGConfig` - 29 edges
8. `NodeEventRepository` - 29 edges
9. `ILLMClient` - 28 edges
10. `Overnight Execution Guide` - 28 edges

## Surprising Connections (you probably didn't know these)
- `DashboardState.apply()` --conceptually_related_to--> `EventBus`  [INFERRED]
  docs/developer_guide.md → src/core/events.py
- `Overnight Execution Guide` --references--> `acceptance_node()`  [EXTRACTED]
  docs/overnight_execution_guide.md → src/evaluator/scorer.py
- `Evaluator Node` --shares_data_with--> `acceptance_node()`  [EXTRACTED]
  docs/overnight_execution_guide.md → src/evaluator/scorer.py
- `Overnight Execution Guide` --references--> `WorkflowState`  [EXTRACTED]
  docs/overnight_execution_guide.md → src/orchestrator/state.py
- `Overnight Execution Guide` --references--> `deduplicator_node()`  [EXTRACTED]
  docs/overnight_execution_guide.md → src/scientist/deduplicator.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **LangGraph Overnight Optimization Pipeline** — src_scientist_brain_scientist_node, src_orchestrator_validator_validator_node, src_scientist_deduplicator_deduplicator_node, src_orchestrator_budget_guard_budget_guard_node, src_indexer_collection_manager_indexer_node, src_rag_pipeline_smoke_tester_smoke_test_node, src_evaluator_ragas_runner_evaluator_node, src_evaluator_scorer_acceptance_node, src_storage_experiment_log_recorder_node, src_scientist_reflection_reflection_node, src_reporter_report_writer_report_writer_node, src_orchestrator_state_workflowstate [EXTRACTED 1.00]
- **CI Code Quality Gate** — _github_workflows_ci, concept_ruff_linter, concept_black_formatter, concept_mypy_typechecker, concept_pytest_testrunner [EXTRACTED 1.00]
- **Knowledge Graph God Nodes** — readme_godnode_ragconfig, readme_godnode_provider, readme_godnode_openaiclient, readme_godnode_icosttracker, readme_godnode_illmclient [EXTRACTED 1.00]
- **System Initialization and Baseline Setup** — docs_mermaid_diagram_2_start_run_overnight_py, docs_mermaid_diagram_2_initialize_sqlite_db_wal_mode, docs_mermaid_diagram_2_initialize_cost_tracker, docs_mermaid_diagram_2_load_config_baseline_settings, docs_mermaid_diagram_2_baseline_cached, docs_mermaid_diagram_2_run_baseline_evaluation, docs_mermaid_diagram_2_store_baseline_score_in_db, docs_mermaid_diagram_2_initialize_graph_state [EXTRACTED 1.00]
- **Autonomous LangGraph Execution Loop** — docs_mermaid_diagram_2_scientist_propose_rag_config, docs_mermaid_diagram_2_validator_schema_bounds_check, docs_mermaid_diagram_2_deduplicator_config_hash_check, docs_mermaid_diagram_2_budget_guard_api_cost_check, docs_mermaid_diagram_2_index_builder_chromadb, docs_mermaid_diagram_2_smoke_tests_basic_queries, docs_mermaid_diagram_2_evaluator_node, docs_mermaid_diagram_2_failhandler, docs_mermaid_diagram_2_acceptance_score_comparison, docs_mermaid_diagram_2_recorder_persist_results, docs_mermaid_diagram_2_reflection_pattern_analysis, docs_mermaid_diagram_2_max_experiments_reached, docs_mermaid_diagram_2_report, docs_mermaid_diagram_2_end_run [EXTRACTED 1.00]
- **Evaluator Execution Pipeline** — docs_mermaid_diagram_2_evaluator_entry, docs_mermaid_diagram_2_select_evaluation_questions, docs_mermaid_diagram_2_run_evaluations, docs_mermaid_diagram_2_aggregate_results_median_stddev, docs_mermaid_diagram_2_return_final_score, docs_mermaid_diagram_2_async_retrieval_aiohttp, docs_mermaid_diagram_2_single_run_evaluation, docs_mermaid_diagram_2_thread_pool_execution, docs_mermaid_diagram_2_ragas_metrics_computation, docs_mermaid_diagram_2_llm_scoring_faithfulness_recall, docs_mermaid_diagram_2_compute_run_metrics [EXTRACTED 1.00]
- **Protocol-Based DI Container Pattern** — docs_project_architecture_breakdown_provider, docs_project_architecture_breakdown_icosttracker, docs_project_architecture_breakdown_illmclient, docs_project_architecture_breakdown_iembeddingservice, docs_project_architecture_breakdown_idatabase [EXTRACTED 0.90]

## Communities (120 total, 41 thin omitted)

### Community 0 - "__init__.py"
Cohesion: 0.05
Nodes (70): bm25_node_count(), build_embed_model(), cache_is_complete(), effective_corpus_limit(), expensive_parser_builds_allowed(), load_bm25_engine(), load_bm25_nodes(), load_corpus_as_documents() (+62 more)

### Community 1 - "pipeline.py"
Cohesion: 0.05
Nodes (52): invalidate_all(), load_all(), load_baseline_config(), load_env(), load_model_routing(), load_settings(), Settings, Load configuration from YAML files with caching.  Provides functions to load and (+44 more)

### Community 2 - "openrouter.py"
Cohesion: 0.07
Nodes (32): BaseException, BaseNodePostprocessor, Exception, ICostTracker, is_openrouter_rate_limit_error(), OpenRouterRerank, NodeWithScore, QueryBundle (+24 more)

### Community 3 - "retriever.py"
Cohesion: 0.09
Nodes (38): BaseRetriever, _build_auto_merging_mode(), _build_bm25_mode(), _build_components(), _build_dense_mode(), _build_query_fusion(), _build_query_fusion_headers(), _build_query_fusion_llm() (+30 more)

### Community 4 - "DashboardState"
Cohesion: 0.10
Nodes (37): DashboardState, FastAPI, DashboardState, ExperimentRow, FailureInfo, Plain-Python state derived from ExperimentEvents -- no Textual or web framework, consume_events(), WebSocket endpoint for the live event stream. On app startup, subscribes to the (+29 more)

### Community 5 - "Model Routing Configuration"
Cohesion: 0.05
Nodes (43): Immutable Baseline Config, coder model route (deepseek/deepseek-v4-flash), conversation_summary model route, Model Routing Configuration, rag_generator_fallback route, rag_generator_primary route, ragas_embedding_model route (openai/text-embedding-3-small), ragas_judge route (qwen/qwen3.5-flash-02-23) (+35 more)

### Community 6 - "Database"
Cohesion: 0.08
Nodes (21): Database, SQLite connection manager and schema initialisation. WAL mode is MANDATORY for s, Manages SQLite connection with WAL mode for safe async access., Initialize database with optional custom path., Create tables, set pragma settings, and backfill config_hashes from existing exp, Context manager for async database connection., init_db(), _instance() (+13 more)

### Community 7 - "Evaluator (module)"
Cohesion: 0.07
Nodes (34): Acceptance: Score Comparison, Aggregate Results (Median, StdDev), Async Retrieval (aiohttp), Baseline Cached? (decision), Budget Guard: API Cost Check, Compute Run Metrics, Deduplicator: Config Hash Check, End Run (+26 more)

### Community 8 - "NodeEventRepository"
Cohesion: 0.11
Nodes (25): _insert_with_lock_retry(), Durable node-level event log: an independent EventBus subscriber that persists, recorder_node() and this consumer each open their own ad-hoc SQLite     connect, _to_node_event(), ConfigHash, HistoricalRecord, NodeEvent, Domain models for the experiment tracking database. (+17 more)

### Community 9 - "OpenAIClient"
Cohesion: 0.11
Nodes (20): load_openai_pricing(), Load openai_pricing.yaml: model_id -> (usd_per_million_input, usd_per_million_ou, call_openai(), OpenAIClient, OpenAIError, OpenAINonRetryableError, OpenAIRateLimitError, Exception (+12 more)

### Community 10 - "devDependencies"
Cohesion: 0.07
Nodes (29): dependencies, react, react-dom, devDependencies, oxlint, @types/node, @types/react, @types/react-dom (+21 more)

### Community 11 - "Provider"
Cohesion: 0.14
Nodes (12): Protocol, Core DI interfaces and container. Exposes all service abstractions and the Provi, IChromaClientFactory, IDatabase, IModelRoutingProvider, IRagasFactory, Any, Interface definitions for all external dependencies. Enables DI: module → interf (+4 more)

### Community 12 - "scorer.py"
Cohesion: 0.11
Nodes (21): _accept_best_config(), acceptance_node(), Scoring and acceptance logic for RAG configuration experiments.  Evaluates propo, Determines if the proposed config should be accepted as the new best.     Uses m, Log acceptance and return updated state with new best config and metrics., ExperimentRecord, BaseModel, Experiment tracking and results models for RAG configuration experiments. (+13 more)

### Community 13 - "CONTRIBUTING.md"
Cohesion: 0.13
Nodes (25): Dependabot Configuration, CI Workflow (GitHub Actions), AggregatedMetrics, Black (code formatter), ExperimentRecord, Vite+React+TypeScript Dashboard Frontend, Graphify Codebase Knowledge Graph, HandleFail Node (+17 more)

### Community 14 - "run_overnight.py"
Cohesion: 0.11
Nodes (15): datetime, main(), _run(), Normalized event model and publish-subscribe bus for broadcasting experiment pr, Translates one raw LangGraph astream() tick (`{node_name: output_dict}`) into n, Experiment recording and state tracking for RAG optimization runs.  Logs experim, ConnectionManager, FastAPI app factory for the local web dashboard. Owns the WebSocket ConnectionMa (+7 more)

### Community 15 - "EventBus"
Cohesion: 0.14
Nodes (22): EventBus, ExperimentEvent, BaseModel, One normalized tick: either a LangGraph node transition, or a     sub-progress, Publish-subscribe broker. Each subscriber gets its own queue so a slow     cons, _event(), Tests for the ExperimentEvent model and EventBus pub-sub broker., test_experiment_event_defaults() (+14 more)

### Community 16 - "adapt"
Cohesion: 0.15
Nodes (22): adapt(), Mutates ctx["exp_num"] on a new scientist tick, mirroring the counting     beha, End-to-end proof that DashboardState.apply() picks up a score from     the real, test_apply_integrates_with_real_adapt_output_for_acceptance_and_recorder(), _FakeCostTracker, _FakeProvider, Tests for translating a raw LangGraph astream() tick into ExperimentEvents., Reproduces the real LangGraph tick shapes for a full experiment cycle:     scie (+14 more)

### Community 17 - "logger.py"
Cohesion: 0.15
Nodes (20): LLMResult, OpenAIEmbeddings, SingleRunMetrics, evaluator_node(), RAGAS evaluation orchestration and IR metric computation.  Runs full evaluatio, Run IR metrics immediately, then conditionally run RAGAS metrics with retry logi, run_single_eval(), build_ragas_embeddings() (+12 more)

### Community 18 - "build_graph"
Cohesion: 0.16
Nodes (22): BaseCheckpointSaver, CompiledStateGraph, indexer_node(), Provider, Graph node: resolve or build collection, return status and updated config with _, _after_budget_guard(), _after_deduplicator(), _after_evaluator() (+14 more)

### Community 19 - "test_ragas_runner_parser.py"
Cohesion: 0.18
Nodes (23): ModelConfig, LLM configuration: model_id, reasoning effort, tokens, temperature, format optio, _build_openrouter_extra_body(), _build_openrouter_model_kwargs(), _no_extra_body(), OpenRouter-specific request body options (e.g. reasoning exclusion)., Default extra_body for providers with no OpenRouter-style quirks., Extract model kwargs (e.g. response format) from judge config. This is     plai (+15 more)

### Community 20 - "compilerOptions"
Cohesion: 0.08
Nodes (23): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+15 more)

### Community 21 - "RunRepository"
Cohesion: 0.11
Nodes (17): Run, Connection, DAO for runs table — minimal interface for run metadata., Initialize with optional connection; if None, creates connections on-demand., Insert a new run row. Idempotent: a resumed run reuses the same         run_id,, Update a run row's terminal fields once the run has stopped., Return the most recent run_id, or None if no runs exist., Return runs newest-first, for the web dashboard's history view. (+9 more)

### Community 22 - "OpenRouterEmbedding"
Cohesion: 0.12
Nodes (13): AsyncOpenAI, BaseEmbedding, OpenRouterEmbedding, Custom LlamaIndex BaseEmbedding that calls /embeddings on OpenRouter. Refactored, Sync wrapper: embed multiple texts (creates event loop if needed)., LlamaIndex embedding provider wrapping OpenRouter /embeddings endpoint., Initialize with model_name and optional API credentials (fallback to env vars)., Create AsyncOpenAI client with OpenRouter base URL. (+5 more)

### Community 23 - "ExperimentRepository"
Cohesion: 0.15
Nodes (12): Experiment, HistoricalRecord, ExperimentRepository, Connection, _row_to_experiment(), Database repository/DAO layer for storage module.  Exports three repositories:, Tests for ExperimentRepository's historical-browsing queries, added for the web, _seed() (+4 more)

### Community 24 - "types.ts"
Cohesion: 0.15
Nodes (14): ConfigDiffCard(), Props, ExperimentSidebar(), Props, TILES, PipelineStrip(), Props, Props (+6 more)

### Community 25 - "history.ts"
Cohesion: 0.17
Nodes (18): ExperimentDetail, ExperimentSummary, fetchExperiment(), fetchRunEvents(), fetchRunExperiments(), fetchRuns(), getJson(), NodeEventRecord (+10 more)

### Community 26 - "App.tsx"
Cohesion: 0.13
Nodes (14): App(), DrawerTarget, View, viewToTab(), BestConfigPanel(), BudgetOverviewPanel(), CurrentConfigPanel(), HypothesisCard() (+6 more)

### Community 27 - "ICostTracker"
Cohesion: 0.13
Nodes (6): ICostTracker, MockChromaFactory, MockDatabase, MockModelRoutingProvider, MockRagasFactory, Tests demonstrating dependency injection with mock providers.

### Community 28 - "settings.py"
Cohesion: 0.15
Nodes (19): AcceptanceSettings, EvalSettings, ExploreExploitSettings, BaseModel, Configuration schemas for overnight experiment runs, evaluation, acceptance, and, Budget and concurrency limits: max_experiments, max_hours, cost ceiling, failure, Evaluation setup: question counts, RAGAS metrics, timeouts, smoke testing, audit, Acceptance criteria: score improvement thresholds, variance tolerance, regressio (+11 more)

### Community 29 - "ILLMClient"
Cohesion: 0.19
Nodes (17): Top-level settings container: aggregates all run, eval, acceptance, and explorat, Settings, ILLMClient, Send a chat-completion-style request and return the response.          `reasonin, build_provider(), Construct the `Provider` for `settings.run.llm_provider`.      Raises `ValueErro, Tests for provider selection via src.core.provider_factory.build_provider., The bug the audit flagged: without this, the client could silently     report co (+9 more)

### Community 30 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+11 more)

### Community 31 - "report_writer.py"
Cohesion: 0.13
Nodes (16): Report generation for RAG optimization runs.  Generates markdown summaries of ex, _build_report_prompt(), _fallback_report(), Provider, Generate markdown report summarizing RAG optimization run results., Generate final markdown report for overnight run with metrics and recommendation, Build LLM prompt with run state payload for report generation., Generate plain-text report fallback when LLM is skipped or fails. (+8 more)

### Community 32 - "deduplicator.py"
Cohesion: 0.16
Nodes (16): deduplicator_node(), _fetch_best_historical_record(), Experiment deduplication and config hash tracking.  Detects repeated configurati, Retrieve best experiment result for a config hash., Check if config was already tried; block duplicate or mark success; clean stale, logical_config(), Configuration utilities for filtering and processing config dicts., Filter out private (underscore-prefixed) keys from a config dict. (+8 more)

### Community 33 - "cost_tracker.py"
Cohesion: 0.17
Nodes (17): add_cost(), BudgetExceededError, get_total(), initialize(), Exception, All API calls MUST go through src/utils/openrouter.py, which calls add_cost() af, Add cost and return new total. Raises BudgetExceededError if ceiling exceeded., Tests for the global cost tracker: accumulation, hard ceiling, and warning thres (+9 more)

### Community 34 - "test_openai_client.py"
Cohesion: 0.17
Nodes (13): _build_payload(), _FakeAsyncClient, _FakeResponse, A reasoning model with no reasoning_effort hint gets neither field —     OpenAI', Stands in for httpx.AsyncClient — no mocking library is installed in     this pr, test_build_payload_json_response_format(), test_build_payload_non_reasoning_model_uses_temperature(), test_build_payload_reasoning_model_ignores_reasoning_effort_when_unset() (+5 more)

### Community 35 - "RAGConfig"
Cohesion: 0.11
Nodes (4): BaseModel, RAGConfig, Complete RAG pipeline configuration with validated hyperparameters for chunking,, Validate node_parser is in allowed set.

### Community 36 - "validator_node"
Cohesion: 0.16
Nodes (15): Overnight search orchestration: graph construction, state schema, validation, an, Defines WorkflowState schema for overnight RAG config search orchestration., State dictionary for graph-based config search workflow., WorkflowState, Validates proposed RAG configs against developer-defined search space constraint, Check proposed config against allowed values, parser/retriever availability, and, validator_node(), _make_test_settings() (+7 more)

### Community 37 - "provider_factory.py"
Cohesion: 0.14
Nodes (14): _build_openai_provider(), _build_openrouter_provider(), Any, ValueError, Resolves `settings.run.llm_provider` to a fully-wired Provider.  Single seam for, Return the environment variable name `provider_name`'s builder reads.      Raise, required_env_var(), _unknown_provider_error() (+6 more)

### Community 38 - "ir_metrics.py"
Cohesion: 0.16
Nodes (16): _build_qrels_and_run(), _evaluate_ir_fallback(), evaluate_ir_metrics(), _mean(), _mrr(), _ndcg(), Information Retrieval metrics evaluation (recall, precision, NDCG, MRR).  Comp, Compute Normalized Discounted Cumulative Gain. (+8 more)

### Community 39 - "proposal.py"
Cohesion: 0.25
Nodes (15): _available_index_configs(), _combine_candidates(), get_fallback_candidates(), get_reranker_probe_candidates(), get_structured_exploration_candidates(), Autonomous scientist module for RAG configuration optimization.  Drives an exper, fallback_proposal(), Proposal generation strategies for experiment candidates.  Implements fallback l (+7 more)

### Community 40 - "reflection.py"
Cohesion: 0.13
Nodes (15): _build_reflection_prompt(), Periodic experiment reflection and pattern extraction.  Summarizes recent succes, Construct LLM prompt with recent patterns for extraction of actionable rules., count_tokens(), Count tokens in text using the shared tokenizer., Trim text to fit within max_tokens, cutting at a sentence boundary when     poss, truncate_to_token_budget(), observe() (+7 more)

### Community 41 - "function_trace.py"
Cohesion: 0.18
Nodes (17): close_trace(), _emit_trace_entry(), _format_call_args(), init_trace(), Function-level trace logging for deep debugging of the scientist pipeline.  Prov, Bind actual args to parameter names and repr each value., Async trace implementation., Sync trace implementation. (+9 more)

### Community 42 - "test_run_overnight_validate.py"
Cohesion: 0.25
Nodes (16): Provider-aware --dry-run checks: required key present, and for     "openai" spe, _validate_environment(), _assume_hotpotqa_data_present(), _fake_missing(), Tests for scripts/run_overnight.py's provider-aware --dry-run validation., data/hotpotqa/questions.jsonl is gitignored and only ever present     locally af, run, _Settings (+8 more)

### Community 43 - "test_budget_enforcement.py"
Cohesion: 0.14
Nodes (15): budget_guard_node(), Cost-based execution guard that halts the workflow if budget ceiling is exceeded, Decides whether to continue running based on total cost.      Evaluates `total_c, Regression tests for the cost-tracker split-brain bug: budget_guard_node (and ev, The deprecated module singleton is intentionally left untouched by     the fix (, budget_guard_node must halt based on the tracker real API calls     report to (p, scientist_node's BUDGET_EXCEEDED tick still carries the PREVIOUS     tick's prop, _reset_singleton_tracker() (+7 more)

### Community 44 - "create_app"
Cohesion: 0.30
Nodes (15): Experiment, Single RAG configuration trial with metrics and cost tracking., create_app(), Tests for the REST history API: GET /api/runs, GET /api/runs/{id}/experiments,, _run(), _seed_node_events(), _seed_run_and_experiment(), test_get_experiment_endpoint_404s_for_unknown_id() (+7 more)

### Community 45 - "MockCostTracker"
Cohesion: 0.18
Nodes (6): MockCostTracker, MockLLMClient, scientist_node produces a proposal when LLM returns valid JSON., Verify MockCostTracker satisfies ICostTracker protocol., Verify MockLLMClient satisfies ILLMClient protocol., TestProvider

### Community 46 - "Overnight Execution Guide"
Cohesion: 0.16
Nodes (16): Bug Report Issue Template, AsyncSqliteSaver LangGraph checkpointer, deepseek/deepseek-v4-pro reasoning model, experiments.sqlite database, IR Metrics (Recall@K, Precision@K, NDCG, MRR), LangGraph Orchestration State Machine, qwen/qwen3.5-flash-02-23 RAGAS judge model, RAGAS Evaluation (faithfulness, context recall) (+8 more)

### Community 47 - "prompt_builder.py"
Cohesion: 0.14
Nodes (15): build_history_lines(), build_scientist_prompt(), Scientist LLM prompt construction for RAG config generation.  Builds context-awa, Extract accepted and rejected patterns from state into formatted log lines., Trim recent experiments to fit token budget, prioritizing newest whole lines., Construct full scientist prompt with mode, history, constraints, and indexed con, _truncate_history(), Decorator that traces function entry/exit to the trace JSONL file.      Can be u (+7 more)

### Community 48 - "ConfigHashRepository"
Cohesion: 0.13
Nodes (9): ConfigHashRepository, Connection, Repository for managing config hashes and their lifecycle.  Tracks configurati, DAO for config_hashes table — tracks seen configurations and their scores., Initialize with optional connection; if None, creates connections on-demand., Insert a new config hash with optional first_seen timestamp (defaults to now)., Update score to the max of current and new value (prevents score decrease)., Return set of all tracked config hashes. (+1 more)

### Community 49 - "test_run_overnight_web_wiring.py"
Cohesion: 0.16
Nodes (8): _FakeGraph, _FakeUvicornServer, Confirms _run() starts the FastAPI web dashboard (via create_app + uvicorn) and, The visibility-gap fix: evaluate_final_best() must run while the     dashboard s, Stands in for uvicorn.Server: never actually binds a port. serve()     just wait, test_dashboard_stays_up_through_final_best_eval(), test_run_creates_and_finishes_run_row(), test_run_starts_web_dashboard_and_publishes_every_tick()

### Community 50 - "test_brain.py"
Cohesion: 0.26
Nodes (13): _make_prompt(), No search-space restrictions configured -> no constraints block is injected into, test_prompt_contains_best_config(), test_prompt_contains_system_instructions(), test_prompt_ends_with_json_instruction(), test_prompt_history_appended(), test_prompt_injects_chunk_size_constraint(), test_prompt_injects_node_parser_constraint() (+5 more)

### Community 51 - "test_scorer.py"
Cohesion: 0.14
Nodes (10): recall_at_k regressing past max_metric_regression rejects even though     ndcg/, No current_best_metrics yet (first-ever acceptance) must skip the     per-metri, relative_improvement below the threshold, and too far below baseline     to cou, Below the improvement threshold but within competitive_score_tolerance     of b, Improvement clears the threshold, but std_dev across runs exceeds     max_varia, test_acceptance_bootstraps_without_prior_best_metrics(), test_acceptance_marks_competitive_near_miss(), test_acceptance_rejects_high_variance_between_runs() (+2 more)

### Community 52 - "model_catalog.py"
Cohesion: 0.21
Nodes (10): build_embedding_model(), build_reranker(), embedding_dimensions(), Registry mapping RAGConfig model identifiers to the provider that serves them., Instantiate the concrete embedding model for `model_id` via its catalog provider, Instantiate the concrete reranker for `reranker_name` via its catalog provider., Return the vector dimensionality for `model_id`., _unknown_embedding_model_error() (+2 more)

### Community 53 - "test_event_log.py"
Cohesion: 0.28
Nodes (11): persist_events(), Runs for the lifetime of the run: pulls every ExperimentEvent off its     own E, _event(), Tests for the durable node-event log: an independent EventBus subscriber that m, Reproduces the exact failure observed in a real overnight run: the     acceptan, A permanently locked/unwritable database must not retry forever --     the tick, test_persist_events_gives_up_after_max_lock_retries(), test_persist_events_retries_and_recovers_from_database_locked() (+3 more)

### Community 54 - "json_repair.py"
Cohesion: 0.32
Nodes (12): _extract_binary_field(), _extract_quoted_field(), _extract_reason(), _fallback_ragas_output(), _json_repair_candidates(), _looks_like_recall_item(), _normalize_ragas_json(), _parse_ragas_output_string_compat() (+4 more)

### Community 55 - "compute_config_diff"
Cohesion: 0.27
Nodes (10): compute_config_diff(), Pure display-formatting helper for showing a live config against the best-known, Returns one (field, value, note) triple per field in `current`, so the     UI ca, Tests for compute_config_diff(), which powers the hero panel's 'Live Configurati, test_field_missing_from_best_is_marked_changed(), test_non_numeric_change_is_marked_changed(), test_numeric_decrease_shows_down_arrow_with_previous_value(), test_numeric_increase_shows_up_arrow_with_previous_value() (+2 more)

### Community 56 - "test_indexer_node_progress.py"
Cohesion: 0.20
Nodes (6): _FakeBus, _FakeCostTracker, _FakeProvider, ExperimentEvent, Tests that indexer_node publishes real progress events to the EventBus, without, test_indexer_node_publishes_progress_events()

### Community 57 - "Autonomous RAG Project Architecture Breakdown"
Cohesion: 0.24
Nodes (11): Database (Class), ExperimentRepository (Class), IChromaClientFactory Protocol, ICostTracker Protocol, IDatabase Protocol, IEmbeddingService Protocol, ILLMClient Protocol, IModelRoutingProvider Protocol (+3 more)

### Community 58 - "react"
Cohesion: 0.18
Nodes (9): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema, oxc, react, typescript (+1 more)

### Community 59 - "test_ragas_runner.py"
Cohesion: 0.27
Nodes (10): _all_rows_failed(), Extract mean of column from pandas DataFrame, returning 0.0 if missing or NaN., True when every row for this metric is NaN (the judge never produced a     sing, _safe_mean(), The bug: _safe_mean alone makes a genuine 0.0000 score indistinguishable     fro, test_all_rows_failed_distinguishes_real_zero_from_all_nan(), test_all_rows_failed_false_when_column_missing(), test_all_rows_failed_false_when_only_some_rows_nan() (+2 more)

### Community 60 - "history.py"
Cohesion: 0.18
Nodes (6): Repository for managing experiment runs.  Simple accessor for the most recent, get_experiment_events(), list_run_events(), REST endpoints for browsing past runs, backed by experiments.sqlite via the exi, Filterable, cursor-paginated node-tick log feed for one run -- the     logger-s, Full ordered node timeline for one experiment attempt -- works     identically

### Community 61 - "Path"
Cohesion: 0.25
Nodes (7): Path, export_data(), main(), Export experiment history from SQLite to CSV or JSON., Query experiments database and write out the result to the designated format., Regression test: config.loader.load_settings()'s key validation must     never, test_load_settings_accepts_every_search_space_field()

### Community 62 - "split_graph_html.py"
Cohesion: 0.31
Nodes (8): _extract_json_value(), _find_assignment(), main(), Shrink graph.html by moving its embedded node/edge/legend data to a sidecar .js, Parse one JSON array/object starting at `start`, honoring string/escape state., Locate `const {name} = <value>;` and return (stmt_start, stmt_end, value)., Return (patched_html, extracted_data) with all four arrays pulled out into JSON., split_graph_html()

### Community 63 - "Claude Code Configuration Rules"
Cohesion: 0.25
Nodes (8): Knowledge Graph Navigation Guidance, No Hardcoded OpenRouter Provider Assumptions Principle, Registry-Dict over If/Elif Principle, Repository Pattern for Persistence Principle, Claude Code Configuration Rules, Derive Validation Allowlists From Pydantic Model Fields Principle, Deploy graphify-out to Pages Job, GitHub Pages Static Deploy Workflow

### Community 64 - "scientist_node"
Cohesion: 0.38
Nodes (6): Provider, scientist_node(), _should_force_reranker_probe(), _should_run_structured_exploration(), A BudgetExceededError from the real LLM call must produce     status=BUDGET_EXCE, test_scientist_node_reports_budget_exceeded_not_a_fallback_proposal()

### Community 65 - "_FakeCostTracker"
Cohesion: 0.33
Nodes (3): _FakeCostTracker, test_report_cost_falls_back_to_module_singleton_when_no_tracker_injected(), test_report_cost_uses_injected_tracker_not_module_singleton()

### Community 66 - "RecentEventsCard.tsx"
Cohesion: 0.40
Nodes (4): Props, RecentEventsCard(), Props, Sparkline()

### Community 67 - "setup_logging"
Cohesion: 0.40
Nodes (5): Configure structlog with stdlib integration and suppress noisy third-party libs., setup_logging(), Global test fixtures: logging setup and teardown., Initializes logging before each test., _setup_logging()

### Community 68 - "ExperimentTimelineDrawer.tsx"
Cohesion: 0.60
Nodes (4): fetchExperimentEvents(), ExperimentTimelineDrawer(), parseJson(), Props

### Community 70 - "Ruflo Codex Configuration (AGENTS.md)"
Cohesion: 0.50
Nodes (4): 3-Tier Model Routing (Agent Booster / Haiku / Sonnet-Opus), SendMessage-First Agent Comms Pattern, Ruflo Codex Configuration (AGENTS.md), Swarm & Routing Configuration

### Community 71 - "enrich_hotpotqa_questions.py"
Cohesion: 0.50
Nodes (3): main(), Backfill supporting_titles into data/hotpotqa/questions.jsonl.  Fetches metadata, Load existing questions, fetch HotpotQA metadata, and enrich with supporting_tit

### Community 72 - "_resolve_api_key"
Cohesion: 0.50
Nodes (4): Resolve the API key for `provider`, preferring an explicit override.      Rais, _resolve_api_key(), test_resolve_api_key_rejects_unknown_provider(), test_resolve_api_key_uses_provider_specific_env_var()

### Community 73 - "index_builder.py"
Cohesion: 0.67
Nodes (3): index_builder.py, indexer_node (architecture breakdown), parser_registry.py

## Knowledge Gaps
- **139 isolated node(s):** `setup_environment.sh script`, `Start run_overnight.py`, `End Run`, `Return Final Score`, `Feature Request Issue Template` (+134 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **41 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Overnight Execution Guide` connect `Overnight Execution Guide` to `scientist_node`, `deduplicator.py`, `validator_node`, `DashboardState`, `test_budget_enforcement.py`, `scorer.py`, `CONTRIBUTING.md`, `run_overnight.py`, `EventBus`, `adapt`, `create_app`, `build_graph`, `history.py`, `report_writer.py`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Why does `Database` connect `Database` to `deduplicator.py`, `proposal.py`, `NodeEventRepository`, `create_app`, `run_overnight.py`, `test_run_overnight_web_wiring.py`, `test_event_log.py`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Why does `ExperimentRepository` connect `ExperimentRepository` to `deduplicator.py`, `proposal.py`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `EventBus` (e.g. with `DashboardState.apply()` and `ConnectionManager`) actually correct?**
  _`EventBus` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `OpenAIClient` (e.g. with `ICostTracker` and `_FakeAsyncClient`) actually correct?**
  _`OpenAIClient` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `Database` (e.g. with `_AutoCommitContext` and `_NoopContext`) actually correct?**
  _`Database` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `Provider` (e.g. with `IChromaClientFactory` and `ICostTracker`) actually correct?**
  _`Provider` has 13 INFERRED edges - model-reasoned connections that need verification._