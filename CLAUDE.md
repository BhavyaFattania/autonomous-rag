# Claude Code Configuration

## Rules

- Do what has been asked; nothing more, nothing less
- NEVER create files unless absolutely necessary — prefer editing existing files
- NEVER create documentation files unless explicitly requested
- NEVER save working files or tests to root — use `/src`, `/tests`, `/docs`, `/config`, `/scripts`
- ALWAYS read a file before editing it
- NEVER commit secrets, credentials, or .env files
- Keep files under 500 lines
- Validate input at system boundaries

## Knowledge Graph Navigation (graphify-out/)

This repo has a graphify knowledge graph at `graphify-out/graph.json` /
`graphify-out/GRAPH_REPORT.md`, built to help Claude and other agents
navigate the codebase without reading whole files cold.

- **Consult the graph before manually reading unfamiliar files.** Before
  doing an open-ended `Grep`/`Read` sweep to orient in an area you don't
  already know, check `GRAPH_REPORT.md`'s Community Hubs and God Nodes
  sections first, or run `graphify query "<question>"` /
  `graphify explain "<NodeName>"`. Use it to answer "where do I start,"
  "what's the blast radius of touching X," and "what higher-level workflow
  does this cluster of functions belong to" — then go read the specific
  files the graph points at, rather than exploring blind. Still verify
  anything load-bearing against the live file before acting on it — the
  graph is a map, not a substitute for reading the code you're about to
  change (see the staleness caveat below).
- **After making changes that alter a node's connections — new function
  calls, new imports, new/removed classes or interfaces, a file added,
  removed, or substantially restructured — run `graphify <path> --update`**
  (incremental; only re-extracts changed files) before ending the session,
  so the graph doesn't silently drift out of sync with what it claims to
  represent. Small edits that don't change call/import relationships (e.g.
  fixing a typo, tweaking a log message) don't need this.
- **The graph can be stale — check before trusting it.** It reflects
  whatever state existed at the last `--update`. If something it describes
  (e.g. a Protocol, a function) turns out not to exist on disk, that means
  the graph is behind, not that the codebase is wrong — treat it the same
  way you'd treat any other persisted memory: verify against the live file
  before acting on a claim from it.
- **`.graphifyignore` at the repo root excludes `.remember/` and
  `pytest_temp/`.** `.remember/`'s own `.gitignore` (a bare `*`) triggers a
  known bug in graphify's directory-scoped ignore-pattern handling that
  causes `detect()`/`--update` to silently see 0 files repo-wide if not
  excluded first — don't remove that exclusion without re-verifying the
  underlying graphify bug is fixed. `pytest_temp/` is transient test output,
  not real repo content.

## Design Principles (derived from codebase audit)

This codebase has one dominant, self-invented convention for handling
"pick a concrete implementation from a config value" — a **registry dict of
`name -> builder callable`**, not an if/elif chain. It appears in
`src/core/provider_factory.py` (`_PROVIDER_BUILDERS`) and
`src/core/model_catalog.py` (`EMBEDDING_CATALOG`/`RERANKER_CATALOG` +
`_EMBEDDING_BUILDERS`/`_RERANKER_BUILDERS`). Follow this convention for any
new "config value selects a concrete class" decision point — do not write a
new if/elif chain for this kind of dispatch.

- **Registry-dict over if/elif, always, for this shape of problem.** If
  you're adding a branch to select a concrete implementation by a string/enum
  config value (a new parser type, retriever type, reranker, provider, etc.),
  add a dict entry to an existing registry or create one — do not extend an
  if/elif chain. Known if/elif chains that are legacy debt, not the model to
  copy: `src/indexer/parser_registry.py`'s `build_node_parser()`,
  `src/rag_pipeline/retriever.py`'s `build_retriever()`. Don't add branches to
  these without first considering converting them to the registry-dict shape.
- **Never hardcode `OPENROUTER_API_KEY` or OpenRouter-specific request shapes
  (headers, `extra_body`) directly in a new code path.** Every model/provider
  selection must resolve through `src.core.model_catalog` (embeddings,
  rerankers) or `src.core.provider_factory.required_env_var()` (API keys),
  never a literal `env.get("OPENROUTER_API_KEY")` or a literal
  `if x == "CohereRerank"` check. This exact bug class (a hand-maintained
  provider assumption that silently goes stale when a second provider is
  added) has recurred multiple times — `src/evaluator/ragas_setup.py` (fixed),
  `src/rag_pipeline/retriever.py`'s `_build_query_fusion_llm()` (not yet
  fixed), `src/orchestrator/validator.py`'s `CohereRerank`/`OPENROUTER_API_KEY`
  check (not yet fixed). Grep for `OPENROUTER_API_KEY` before adding any new
  provider-aware code path — if you find a new bare reference, that's a sign
  the same bug is about to recur.
- **Derive validation allowlists from the Pydantic model's own fields, never
  a hand-maintained duplicate set.** See `config/loader.py`'s
  `load_settings()` (`set(SearchSpaceSettings.model_fields)`), fixed after
  `allowed_embedding_models` silently drifted out of a hardcoded
  `valid_search_keys` set. Any future "validate these raw keys against a
  known-keys list" code must derive that list from the model, not retype it.
- **Prefer constructor-injected dependencies (`Provider`, explicit
  `cost_tracker`/`env` params) over module-level singletons for anything
  new.** `src/storage/cost_tracker.py`'s `_default_tracker` and
  `src/utils/openrouter.py`'s `_default_client` are legacy singletons kept
  only for backward compatibility with old call sites — they are not the
  pattern to extend. New code should accept dependencies as parameters and
  flow through `Provider`, matching `OpenAIClient`'s constructor-injection
  design rather than `OpenRouterClient`'s dual-mode (injected-or-global-
  fallback) design.
- **Repository pattern for persistence** (`src/storage/repositories/*.py`) —
  new SQL/persistence logic belongs in a repository class there, not inline
  in orchestrator/scientist nodes.
- **Before writing a second near-duplicate implementation of an existing
  Protocol** (e.g. a third `ILLMClient` for a new provider), check whether
  `src/utils/openrouter.py`'s `OpenRouterClient` and
  `src/utils/openai_client.py`'s `OpenAIClient` have converged enough to be
  worth factoring into a shared base (retry/backoff shape,
  `RETRYABLE_STATUS_CODES` split, fallback-model-on-rate-limit logic, and
  injected-cost-tracker-with-singleton-fallback are duplicated between them
  today). Don't copy-paste a third ~250-line client without first pulling out
  that shared skeleton.

## Build & Test

- ALWAYS run tests after code changes
- ALWAYS verify the full check set passes before considering work done

```bash
poetry run pytest -q
poetry run ruff check .
poetry run black --check .
poetry run mypy src
```
