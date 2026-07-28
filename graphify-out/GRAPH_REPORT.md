# Graph Report - .  (2026-07-27)

## Corpus Check
- 47 files · ~111,661 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1661 nodes · 3141 edges · 132 communities (77 shown, 55 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 164 edges (avg confidence: 0.62)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- DashboardState
- py
- py
- EventBus
- py
- Model Routing Configuration
- OpenAIClient
- build_graph()
- db_or_connect()
- Evaluator (module)
- py
- ExperimentRepository
- Provider
- py
- md
- Overnight Execution Guide
- devDependencies
- build_provider()
- py
- NodeEventRepository
- py
- py
- compilerOptions
- RunRepository
- OpenRouterEmbedding
- py
- ts
- py
- ts
- tsx
- py
- Database
- py
- py
- compilerOptions
- py
- CostTrackingCallback
- RAGConfig
- py
- py
- py
- py
- py
- py
- py
- py
- py
- py
- py
- WeightedHybridRetriever
- py
- compute_config_diff()
- py
- build_chat_model()
- Autonomous RAG Project Architecture Brea
- react
- validator_node()
- Path
- py
- py
- Claude Code Configuration Rules
- load_env()
- py
- ModelRoutingProvider
- py
- tsx
- tsx
- py
- py
- md)
- py
- py
- ts
- json
- Constructor-Injected Dependencies over M
- Manual Pricing Update Rationale
- reflection_node (architecture breakdown)
- RerankingRetriever
- tsx)
- Dependency Review Job
- sh
- py
- py
- py
- Build & Test Check Set
- Contributor Covenant Code of Conduct
- Settings
- Docker Compose Config (empty services)
- budget_guard_node (architecture breakdow
- ConfigHashRepository (Class)
- py
- RunRepository (Class)
- Exception
- Favicon (Purple Abstract Mark)
- Icon Sprite Sheet (Bluesky, Discord, Doc
- Hero Banner Image
- React Logo (Vite scaffold asset)
- Feature Request Issue Template
- PR Checklist (no hardcoding, file placem
- HistoricalRecord
- ICostTracker
- LLMResult
- NodeWithScore
- PersistentClient
- autonomous-rag-optimizer
- pre-commit black (format) hook
- pre-commit-hooks bundle (trailing-whites
- pre-commit ruff (lint) hook
- QueryBundle
- Path
- ValueError
- ValueError
- LangchainLLMWrapper
- PersistentClient
- PersistentClient
- ExperimentEvent
- Provider
- Provider
- Exception
- Path
- Provider
- Provider
- Connection
- Provider
- Exception
- WorkflowState

## God Nodes (most connected - your core abstractions)
1. `Provider` - 49 edges
2. `EventBus` - 38 edges
3. `RAGConfig` - 29 edges
4. `DashboardState` - 29 edges
5. `NodeEventRepository` - 29 edges
6. `Overnight Execution Guide` - 28 edges
7. `create_app()` - 27 edges
8. `Database` - 26 edges
9. `build_graph()` - 26 edges
10. `build_provider()` - 22 edges

## Surprising Connections (you probably didn't know these)
- `DashboardState.apply()` --conceptually_related_to--> `EventBus`  [INFERRED]
  docs/developer_guide.md → src/core/events.py
- `Config Field Pairing Rules` --semantically_similar_to--> `Config Field Pairing Rules (prompt)`  [INFERRED] [semantically similar]
  docs/scientist_io.md → prompts/scientist_v1.txt
- `Overnight Execution Guide` --references--> `indexer_node()`  [EXTRACTED]
  docs/overnight_execution_guide.md → src/indexer/collection_manager.py
- `Developer Guide` --references--> `budget_guard_node()`  [EXTRACTED]
  docs/developer_guide.md → src/orchestrator/budget_guard.py
- `Overnight Execution Guide` --references--> `validator_node()`  [EXTRACTED]
  docs/overnight_execution_guide.md → src/orchestrator/validator.py

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

## Communities (132 total, 55 thin omitted)

### Community 0 - "DashboardState"
Cohesion: 0.07
Nodes (59): DashboardState, datetime, DashboardState, ExperimentRow, FailureInfo, Plain-Python state derived from ExperimentEvents -- no Textual or web framework, ExperimentEvent, BaseModel (+51 more)

### Community 1 - "py"
Cohesion: 0.06
Nodes (61): bm25_node_count(), build_embed_model(), cache_is_complete(), effective_corpus_limit(), expensive_parser_builds_allowed(), load_bm25_engine(), load_bm25_nodes(), load_corpus_as_documents() (+53 more)

### Community 2 - "py"
Cohesion: 0.05
Nodes (58): Scoring and acceptance logic for RAG configuration experiments.  Evaluates pro, collection_is_cached(), _config_from_collection_stem(), indexer_node(), list_available_index_configs(), Provider, RAGConfig, Collection lifecycle management: building, caching, and retrieving vector collec (+50 more)

### Community 3 - "EventBus"
Cohesion: 0.07
Nodes (49): EventBus, ExperimentEvent, FastAPI, EventBus, Publish-subscribe broker. Each subscriber gets its own queue so a slow     cons, consume_events(), WebSocket endpoint for the live event stream. On app startup, subscribes to the, Runs for the lifetime of the app: pulls every ExperimentEvent off the     app's (+41 more)

### Community 4 - "py"
Cohesion: 0.06
Nodes (55): AcceptanceSettings, EvalSettings, ExploreExploitSettings, BaseModel, Configuration schemas for overnight experiment runs, evaluation, acceptance, and, Top-level settings container: aggregates all run, eval, acceptance, and explorat, Budget and concurrency limits: max_experiments, max_hours, cost ceiling, failure, Evaluation setup: question counts, RAGAS metrics, timeouts, smoke testing, audit (+47 more)

### Community 5 - "Model Routing Configuration"
Cohesion: 0.05
Nodes (43): Immutable Baseline Config, coder model route (deepseek/deepseek-v4-flash), conversation_summary model route, Model Routing Configuration, rag_generator_fallback route, rag_generator_primary route, ragas_embedding_model route (openai/text-embedding-3-small), ragas_judge route (qwen/qwen3.5-flash-02-23) (+35 more)

### Community 6 - "OpenAIClient"
Cohesion: 0.09
Nodes (30): Provider-aware --dry-run checks: required key present, and for     "openai" spe, _validate_environment(), OpenAIClient, OpenAIError, Exception, OpenAI catalog-validation client.  The hand-rolled chat-completions call machi, Thin client used only to validate configured OpenAI models against     OpenAI's, Live model IDs from OpenAI's catalog (GET /v1/models). Used to         validate (+22 more)

### Community 7 - "build_graph()"
Cohesion: 0.10
Nodes (31): BaseCheckpointSaver, CompiledStateGraph, Cost-based execution guard that halts the workflow if budget ceiling is exceeded, _after_budget_guard(), _after_deduplicator(), _after_evaluator(), _after_indexer(), _after_recorder() (+23 more)

### Community 8 - "db_or_connect()"
Cohesion: 0.07
Nodes (18): ConfigHashRepository, Connection, Repository for managing config hashes and their lifecycle.  Tracks configurati, DAO for config_hashes table — tracks seen configurations and their scores., Initialize with optional connection; if None, creates connections on-demand., Insert a new config hash with optional first_seen timestamp (defaults to now)., Update score to the max of current and new value (prevents score decrease)., Return set of all tracked config hashes. (+10 more)

### Community 9 - "Evaluator (module)"
Cohesion: 0.07
Nodes (34): Acceptance: Score Comparison, Aggregate Results (Median, StdDev), Async Retrieval (aiohttp), Baseline Cached? (decision), Budget Guard: API Cost Check, Compute Run Metrics, Deduplicator: Config Hash Check, End Run (+26 more)

### Community 10 - "py"
Cohesion: 0.09
Nodes (11): MockChromaFactory, MockCostTracker, MockDatabase, MockLLMClient, MockModelRoutingProvider, MockRagasFactory, Tests demonstrating dependency injection with mock providers., scientist_node produces a proposal when LLM returns valid JSON. (+3 more)

### Community 11 - "ExperimentRepository"
Cohesion: 0.11
Nodes (19): Connection, Experiment, ConfigHash, Experiment, HistoricalRecord, Domain models for the experiment tracking database., Deduplication record mapping config hash to first seen timestamp and best score., Best result retrieved for a given config hash from experiment history. (+11 more)

### Community 12 - "Provider"
Cohesion: 0.09
Nodes (17): IChromaClientFactory, IDatabase, ILLMClient, IModelRoutingProvider, IRagasFactory, Provider, Any, ICostTracker (+9 more)

### Community 13 - "py"
Cohesion: 0.11
Nodes (28): ModelConfig, BaseModel, Model configuration schemas for LLM providers and agent role assignments.  Def, LLM configuration: model_id, reasoning effort, tokens, temperature, format optio, _build_openrouter_extra_body(), _build_openrouter_model_kwargs(), _no_extra_body(), Extract model kwargs (e.g. response format) from judge config. This is     plai (+20 more)

### Community 14 - "md"
Cohesion: 0.11
Nodes (28): Dependabot Configuration, CI Workflow (GitHub Actions), AggregatedMetrics, Black (code formatter), ExperimentRecord, Vite+React+TypeScript Dashboard Frontend, Graphify Codebase Knowledge Graph, HandleFail Node (+20 more)

### Community 15 - "Overnight Execution Guide"
Cohesion: 0.09
Nodes (28): Bug Report Issue Template, AggregatedMetrics, AsyncSqliteSaver LangGraph checkpointer, deepseek/deepseek-v4-pro reasoning model, experiments.sqlite database, qwen/qwen3.5-flash-02-23 RAGAS judge model, run_settings.yaml config, Overnight Execution Guide (+20 more)

### Community 16 - "devDependencies"
Cohesion: 0.07
Nodes (29): dependencies, react, react-dom, devDependencies, oxlint, @types/node, @types/react, @types/react-dom (+21 more)

### Community 17 - "build_provider()"
Cohesion: 0.13
Nodes (26): LangChainLLMClient, ICostTracker, ILLMClient implementation backed by langchain-openai ChatOpenAI., build_provider(), ProviderSpec, Resolves `settings.run.llm_provider` to a fully-wired Provider.  Single seam f, Return the environment variable name `provider_name`'s client reads.      Rais, Everything `build_provider` needs to wire one provider's     `LangChainLLMClien (+18 more)

### Community 18 - "py"
Cohesion: 0.11
Nodes (23): add_cost(), BudgetExceededError, CostTracker, get_total(), initialize(), Exception, All API calls MUST go through src/utils/openrouter.py, which calls add_cost() af, Thread-safe cost tracker with budget enforcement via ceiling and warning thresho (+15 more)

### Community 19 - "NodeEventRepository"
Cohesion: 0.14
Nodes (20): _insert_with_lock_retry(), Durable node-level event log: an independent EventBus subscriber that persists, recorder_node() and this consumer each open their own ad-hoc SQLite     connect, _to_node_event(), NodeEvent, One durably-logged pipeline node tick, keyed by the experiment_uuid     minted, NodeEventRepository, Connection (+12 more)

### Community 20 - "py"
Cohesion: 0.10
Nodes (20): DI container — wires all external dependencies. Substitute implementations in te, _fresh_experiment_state(), Clear result fields that belong to the previous experiment attempt., scientist_node(), _should_force_reranker_probe(), _should_run_structured_exploration(), _build_reflection_prompt(), Periodic experiment reflection and pattern extraction.  Summarizes recent succ (+12 more)

### Community 21 - "py"
Cohesion: 0.13
Nodes (11): Protocol, Core DI interfaces and container. Exposes all service abstractions and the Provi, IChromaClientFactory, ICostTracker, IDatabase, ILLMClient, IModelRoutingProvider, IRagasFactory (+3 more)

### Community 22 - "compilerOptions"
Cohesion: 0.08
Nodes (23): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+15 more)

### Community 23 - "RunRepository"
Cohesion: 0.11
Nodes (17): Run, Connection, DAO for runs table — minimal interface for run metadata., Initialize with optional connection; if None, creates connections on-demand., Insert a new run row. Idempotent: a resumed run reuses the same         run_id,, Update a run row's terminal fields once the run has stopped., Return the most recent run_id, or None if no runs exist., Return runs newest-first, for the web dashboard's history view. (+9 more)

### Community 24 - "OpenRouterEmbedding"
Cohesion: 0.12
Nodes (13): AsyncOpenAI, BaseEmbedding, OpenRouterEmbedding, Custom LlamaIndex BaseEmbedding that calls /embeddings on OpenRouter. Refactored, Sync wrapper: embed multiple texts (creates event loop if needed)., LlamaIndex embedding provider wrapping OpenRouter /embeddings endpoint., Initialize with model_name and optional API credentials (fallback to env vars)., Create AsyncOpenAI client with OpenRouter base URL. (+5 more)

### Community 25 - "py"
Cohesion: 0.13
Nodes (19): invalidate_all(), load_all(), load_model_routing(), load_settings(), Load configuration from YAML files with caching.  Provides functions to load a, Clear all cached configuration loaders (for testing/reloading)., Load and return all config: (settings, model_routing, baseline_config, env_vars), Load run_settings.yaml and return validated Settings with optional search_space (+11 more)

### Community 26 - "ts"
Cohesion: 0.15
Nodes (14): ConfigDiffCard(), Props, ExperimentSidebar(), Props, TILES, PipelineStrip(), Props, Props (+6 more)

### Community 27 - "py"
Cohesion: 0.12
Nodes (20): _openrouter_default_headers(), OpenRouter branding headers only. ChatOpenAI derives Authorization from     the, _build_default_headers(), _judge_branding_headers(), _no_headers(), LLMResult, _ragas_generation_finished(), Setup and configuration for RAGAS evaluation framework.  Provides utilities fo (+12 more)

### Community 28 - "ts"
Cohesion: 0.17
Nodes (18): ExperimentDetail, ExperimentSummary, fetchExperiment(), fetchRunEvents(), fetchRunExperiments(), fetchRuns(), getJson(), NodeEventRecord (+10 more)

### Community 29 - "tsx"
Cohesion: 0.13
Nodes (14): App(), DrawerTarget, View, viewToTab(), BestConfigPanel(), BudgetOverviewPanel(), CurrentConfigPanel(), HypothesisCard() (+6 more)

### Community 30 - "py"
Cohesion: 0.17
Nodes (18): LangchainLLMWrapper, OpenAIEmbeddings, _dump(), main(), One-shot diagnostic for the ragas-judge "API connection error".  Run:  poetry ru, SingleRunMetrics, evaluator_node(), RAGAS evaluation orchestration and IR metric computation.  Runs full evaluatio (+10 more)

### Community 31 - "Database"
Cohesion: 0.16
Nodes (18): Database, Manages SQLite connection with WAL mode for safe async access., Initialize database with optional custom path., Create tables, set pragma settings, and backfill config_hashes from existing exp, Context manager for async database connection., persist_events(), Runs for the lifetime of the run: pulls every ExperimentEvent off its     own E, _event() (+10 more)

### Community 32 - "py"
Cohesion: 0.15
Nodes (15): _is_openai_reasoning_model(), _is_rate_limit(), LLMClientError, _model_kwargs_for(), Any, Exception, LangChain-backed ILLMClient adapter + ChatOpenAI factory.  Replaces the hand-rol, Build the ChatOpenAI model_kwargs that reproduce the current payloads.      - Op (+7 more)

### Community 33 - "py"
Cohesion: 0.15
Nodes (11): load_baseline_config(), main(), _run(), Rich terminal UI utilities for live workflow event display and experiment metric, empty_metrics(), evaluate_baseline(), evaluate_final_best(), Evaluates RAG configs via multi-run baseline and final-best protocols with cachi (+3 more)

### Community 34 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+11 more)

### Community 35 - "py"
Cohesion: 0.13
Nodes (15): _fetch_best_historical_record(), Experiment deduplication and config hash tracking.  Detects repeated configura, Retrieve best experiment result for a config hash., Turn a completed duplicate into a zero-cost observation for acceptance., _reuse_historical_result(), SQLite connection manager and schema initialisation. WAL mode is MANDATORY for s, logical_config(), Configuration utilities for filtering and processing config dicts. (+7 more)

### Community 36 - "CostTrackingCallback"
Cohesion: 0.16
Nodes (13): CostTrackingCallback, Any, BaseCallbackHandler, ICostTracker, LLMResult, LangChain callback that records per-call USD into the injected cost tracker.  At, Extract (model_id, prompt_tokens, completion_tokens) from an LLMResult., _usage_from_result() (+5 more)

### Community 37 - "RAGConfig"
Cohesion: 0.11
Nodes (4): BaseModel, RAGConfig, Complete RAG pipeline configuration with validated hyperparameters for chunking,, Validate node_parser is in allowed set.

### Community 38 - "py"
Cohesion: 0.16
Nodes (16): _build_qrels_and_run(), _evaluate_ir_fallback(), evaluate_ir_metrics(), _mean(), _mrr(), _ndcg(), Information Retrieval metrics evaluation (recall, precision, NDCG, MRR).  Comp, Compute Normalized Discounted Cumulative Gain. (+8 more)

### Community 39 - "py"
Cohesion: 0.24
Nodes (17): get_or_build_collection(), Retrieve cached collection or build from scratch if missing/incomplete; returns, _contexts_to_results(), _get_or_build_contexts(), _get_or_build_results(), _node_to_result(), Provider, RAGConfig (+9 more)

### Community 40 - "py"
Cohesion: 0.22
Nodes (17): _build_auto_merging_mode(), _build_bm25_mode(), _build_components(), _build_dense_mode(), _build_query_fusion(), _build_query_fusion_rrf_mode(), _build_query_fusion_simple_mode(), _build_recursive_mode() (+9 more)

### Community 41 - "py"
Cohesion: 0.19
Nodes (10): BaseException, BaseNodePostprocessor, RAG pipeline components: retriever construction, answer generation, and smoke te, is_openrouter_rate_limit_error(), OpenRouterRerank, NodeWithScore, QueryBundle, Smoke test validates that retrieval pipeline runs and returns non-empty results. (+2 more)

### Community 42 - "py"
Cohesion: 0.22
Nodes (16): _build_query_fusion_headers(), _build_query_fusion_llm(), OpenRouter needs branding headers; other providers need none., _base(), _blocking_settings(), Settings, Regression test: _build_query_fusion_llm() previously always read     OPENROUTE, test_auto_merging_requires_hierarchical_parser() (+8 more)

### Community 43 - "py"
Cohesion: 0.27
Nodes (14): _extract_binary_field(), _extract_quoted_field(), _extract_reason(), _fallback_ragas_output(), install_ragas_output_parser_compat_patch(), _json_repair_candidates(), _looks_like_recall_item(), _normalize_ragas_json() (+6 more)

### Community 44 - "py"
Cohesion: 0.16
Nodes (8): _FakeGraph, _FakeUvicornServer, Confirms _run() starts the FastAPI web dashboard (via create_app + uvicorn) and, The visibility-gap fix: evaluate_final_best() must run while the     dashboard, Stands in for uvicorn.Server: never actually binds a port. serve()     just wai, test_dashboard_stays_up_through_final_best_eval(), test_run_creates_and_finishes_run_row(), test_run_starts_web_dashboard_and_publishes_every_tick()

### Community 45 - "py"
Cohesion: 0.22
Nodes (13): _all_rows_failed(), _metric_availability_warning(), Extract mean of column from pandas DataFrame, returning 0.0 if missing or NaN., True when every row for this metric is NaN (the judge never produced a     sing, Describe judge metrics that RAGAS could not score without failing the run., _safe_mean(), The bug: _safe_mean alone makes a genuine 0.0000 score indistinguishable     fro, test_all_rows_failed_distinguishes_real_zero_from_all_nan() (+5 more)

### Community 46 - "py"
Cohesion: 0.14
Nodes (10): recall_at_k regressing past max_metric_regression rejects even though     ndcg/, No current_best_metrics yet (first-ever acceptance) must skip the     per-metri, relative_improvement below the threshold, and too far below baseline     to cou, Below the improvement threshold but within competitive_score_tolerance     of b, Improvement clears the threshold, but std_dev across runs exceeds     max_varia, test_acceptance_bootstraps_without_prior_best_metrics(), test_acceptance_marks_competitive_near_miss(), test_acceptance_rejects_high_variance_between_runs() (+2 more)

### Community 47 - "py"
Cohesion: 0.21
Nodes (10): build_embedding_model(), build_reranker(), embedding_dimensions(), Registry mapping RAGConfig model identifiers to the provider that serves them., Instantiate the concrete embedding model for `model_id` via its catalog provider, Instantiate the concrete reranker for `reranker_name` via its catalog provider., Return the vector dimensionality for `model_id`., _unknown_embedding_model_error() (+2 more)

### Community 48 - "py"
Cohesion: 0.21
Nodes (9): AggregatedMetrics, BaseModel, RAG evaluation metrics models for single runs and aggregated results., Composite score: 35% recall_at_k + 25% ndcg + 20% mrr + 10% precision + 10% cont, Aggregated metrics across multiple runs (up to 3) with median values and varianc, Aggregate metrics from multiple runs by computing medians and std dev of weighte, Metrics from a single RAG generation run., SingleRunMetrics (+1 more)

### Community 49 - "WeightedHybridRetriever"
Cohesion: 0.32
Nodes (5): BaseRetriever, NodeWithScore, QueryBundle, RerankingRetriever, WeightedHybridRetriever

### Community 50 - "py"
Cohesion: 0.24
Nodes (9): load_openai_pricing(), Load openai_pricing.yaml: model_id -> (usd_per_million_input, usd_per_million_ou, compute_cost(), _load_openai_pricing(), _pricing_for(), Unified per-(provider, model) pricing lookup shared by the cost callback., USD cost for a call; 0.0 (with a warning) when the model has no price., test_openrouter_cost_uses_model_pricing_table() (+1 more)

### Community 51 - "compute_config_diff()"
Cohesion: 0.27
Nodes (10): compute_config_diff(), Pure display-formatting helper for showing a live config against the best-known, Returns one (field, value, note) triple per field in `current`, so the     UI ca, Tests for compute_config_diff(), which powers the hero panel's 'Live Configurati, test_field_missing_from_best_is_marked_changed(), test_non_numeric_change_is_marked_changed(), test_numeric_decrease_shows_down_arrow_with_previous_value(), test_numeric_increase_shows_up_arrow_with_previous_value() (+2 more)

### Community 52 - "py"
Cohesion: 0.20
Nodes (6): _FakeBus, _FakeCostTracker, _FakeProvider, ExperimentEvent, Tests that indexer_node publishes real progress events to the EventBus, without, test_indexer_node_publishes_progress_events()

### Community 53 - "build_chat_model()"
Cohesion: 0.29
Nodes (9): ChatOpenAI, build_chat_model(), BaseCallbackHandler, _payload(), test_build_chat_model_emits_no_langchain_model_kwargs_warning(), test_json_object_sets_response_format(), test_openai_o_series_uses_top_level_reasoning_effort(), test_openrouter_reasoning_effort_goes_to_extra_body_and_omits_temperature() (+1 more)

### Community 54 - "Autonomous RAG Project Architecture Brea"
Cohesion: 0.24
Nodes (11): Database (Class), ExperimentRepository (Class), IChromaClientFactory Protocol, ICostTracker Protocol, IDatabase Protocol, IEmbeddingService Protocol, ILLMClient Protocol, IModelRoutingProvider Protocol (+3 more)

### Community 55 - "react"
Cohesion: 0.18
Nodes (9): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema, oxc, react, typescript (+1 more)

### Community 56 - "validator_node()"
Cohesion: 0.33
Nodes (9): Check proposed config against allowed values, parser/retriever availability, and, validator_node(), _make_test_settings(), Settings, Regression test: validator_node() previously hardcoded     `if config.reranker, test_brain_prompt_incorporates_constraints(), test_candidates_filtering(), test_validator_derives_required_env_var_from_reranker_catalog_not_hardcoded() (+1 more)

### Community 57 - "Path"
Cohesion: 0.25
Nodes (7): Path, export_data(), main(), Export experiment history from SQLite to CSV or JSON., Query experiments database and write out the result to the designated format., Regression test: config.loader.load_settings()'s key validation must     never, test_load_settings_accepts_every_search_space_field()

### Community 58 - "py"
Cohesion: 0.31
Nodes (8): _extract_json_value(), _find_assignment(), main(), Shrink graph.html by moving its embedded node/edge/legend data to a sidecar .js, Parse one JSON array/object starting at `start`, honoring string/escape state., Locate `const {name} = <value>;` and return (stmt_start, stmt_end, value)., Return (patched_html, extracted_data) with all four arrays pulled out into JSON., split_graph_html()

### Community 59 - "py"
Cohesion: 0.22
Nodes (5): get_experiment_events(), list_run_events(), REST endpoints for browsing past runs, backed by experiments.sqlite via the exi, Filterable, cursor-paginated node-tick log feed for one run -- the     logger-s, Full ordered node timeline for one experiment attempt -- works     identically

### Community 60 - "Claude Code Configuration Rules"
Cohesion: 0.25
Nodes (8): Knowledge Graph Navigation Guidance, No Hardcoded OpenRouter Provider Assumptions Principle, Registry-Dict over If/Elif Principle, Repository Pattern for Persistence Principle, Claude Code Configuration Rules, Derive Validation Allowlists From Pydantic Model Fields Principle, Deploy graphify-out to Pages Job, GitHub Pages Static Deploy Workflow

### Community 61 - "load_env()"
Cohesion: 0.39
Nodes (7): load_env(), Extract API keys from environment variables.      OPENROUTER_API_KEY is requir, Boundary validation for load_env().  An empty/blank OPENROUTER_API_KEY previousl, test_load_env_rejects_blank_key(), test_load_env_rejects_empty_key(), test_load_env_rejects_missing_key(), test_load_env_returns_key_when_present()

### Community 62 - "py"
Cohesion: 0.32
Nodes (6): _config_summary(), Experiment recording and state tracking for RAG optimization runs.  Logs exper, Serialize aggregate metrics with any non-fatal evaluation warnings., Format config dict into human-readable summary for logging patterns., _serialize_metrics(), test_serialize_metrics_persists_non_fatal_evaluation_warnings()

### Community 63 - "ModelRoutingProvider"
Cohesion: 0.43
Nodes (4): ModelRoutingProvider, _provider_kwargs(), Any, Adapter exposing YAML role routing through the Provider DI boundary.

### Community 64 - "py"
Cohesion: 0.33
Nodes (5): ExperimentRecord, BaseModel, Experiment tracking and results models for RAG configuration experiments., Complete record of a single RAG configuration experiment run., Re-exports the core data models: experiment records, metrics, and RAG config.

### Community 65 - "tsx"
Cohesion: 0.40
Nodes (4): Props, RecentEventsCard(), Props, Sparkline()

### Community 66 - "tsx"
Cohesion: 0.60
Nodes (4): fetchExperimentEvents(), ExperimentTimelineDrawer(), parseJson(), Props

### Community 67 - "py"
Cohesion: 0.50
Nodes (4): init_db(), _instance(), Backward-compat re-exports from the database module.  Existing code imports from, Initialize database by creating tables and indexes.

### Community 69 - "md)"
Cohesion: 0.50
Nodes (4): 3-Tier Model Routing (Agent Booster / Haiku / Sonnet-Opus), SendMessage-First Agent Comms Pattern, Ruflo Codex Configuration (AGENTS.md), Swarm & Routing Configuration

### Community 70 - "py"
Cohesion: 0.50
Nodes (3): main(), Backfill supporting_titles into data/hotpotqa/questions.jsonl.  Fetches metadata, Load existing questions, fetch HotpotQA metadata, and enrich with supporting_tit

### Community 71 - "py"
Cohesion: 0.67
Nodes (3): index_builder.py, indexer_node (architecture breakdown), parser_registry.py

## Knowledge Gaps
- **138 isolated node(s):** `setup_environment.sh script`, `Start run_overnight.py`, `End Run`, `Return Final Score`, `Feature Request Issue Template` (+133 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **55 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Provider` connect `Provider` to `build_graph()`, `py`, `Overnight Execution Guide`, `build_provider()`, `py`, `py`, `ModelRoutingProvider`?**
  _High betweenness centrality (0.070) - this node is a cross-community bridge._
- **Why does `Overnight Execution Guide` connect `Overnight Execution Guide` to `DashboardState`, `py`, `py`, `EventBus`, `build_graph()`, `py`, `md`, `py`, `validator_node()`, `py`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Why does `RunRepository` connect `RunRepository` to `ExperimentRepository`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `Provider` (e.g. with `ModelRoutingProvider` and `ProviderSpec`) actually correct?**
  _`Provider` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `EventBus` (e.g. with `DashboardState.apply()` and `_Settings`) actually correct?**
  _`EventBus` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `DashboardState` (e.g. with `ExperimentEvent` and `DashboardStateSchema`) actually correct?**
  _`DashboardState` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `NodeEventRepository` (e.g. with `NodeEvent` and `test_persist_events_gives_up_after_max_lock_retries()`) actually correct?**
  _`NodeEventRepository` has 4 INFERRED edges - model-reasoned connections that need verification._