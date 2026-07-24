# Autonomous RAG Optimizer

An intelligent, autonomous system designed to iteratively hyper-optimize Retrieval-Augmented Generation (RAG) pipelines over an extended period (such as overnight). Powered by LangGraph, LlamaIndex, ChromaDB, and evaluated with Ragas.

## 🚀 Features

- **Autonomous Experimentation Loop:** Proposes, tests, and evaluates different RAG configurations (chunk size, overlap, retrieval strategies) entirely unattended.
- **LangGraph Orchestration:** Utilizes a highly robust state machine to handle validation, deduplication, budget guarding, smoke testing, and deep evaluations.
- **Live Web Dashboard:** A local FastAPI + WebSocket + React dashboard (`http://127.0.0.1:8000`, started automatically alongside every run) shows the pipeline live — current node, hypothesis, config diff vs. best, budget spent, and experiment history — plus a historical view for browsing past runs from `experiments.sqlite`.
- **Strict Budget Guarding:** Intercepts and monitors LLM (OpenRouter) API costs to prevent runaway billing during long-running optimization sessions.
- **Resilient Evaluation Threading:** Offloads blocking, synchronous evaluation frameworks (like RAGAS) to background threads using `nest_asyncio` and `ThreadPoolExecutors` for non-blocking I/O operations.
- **Comprehensive SQLite Storage:** Retains every experiment, caching failures and baseline scores to continuously track progress and avoid redundant executions.

## 🛠️ Tech Stack

- **Python:** `^3.11`
- **Orchestration:** `langgraph`, `langchain-core`
- **RAG & Vector Stores:** `llama-index` (modular), `chromadb`
- **Evaluation:** `ragas`, `datasets`
- **Database:** SQLite (`aiosqlite`)
- **Dashboard:** `fastapi`, `uvicorn[standard]` (backend), Vite + React + TypeScript (frontend, built once and served as static files — no Node process needed at runtime)
- **Dependency Management:** Poetry (backend), npm (frontend build only)

## 📦 Getting Started

### Prerequisites
- Python 3.11+
- Poetry installed (`pip install poetry`)
- OpenRouter/OpenAI API Keys

### Installation

1. Clone the repository and install dependencies using Poetry:
   ```bash
   poetry install
   ```

2. Set up your environment variables by copying the example file and filling in real keys:
   ```bash
   cp .env.example .env
   ```
   See `.env.example` for which keys are required vs. optional (depends on `settings.run.llm_provider`).

3. Download the HotpotQA evaluation corpus (one-time; `data/` is gitignored so this doesn't ship with the repo):
   ```bash
   poetry run python data/hotpotqa/setup_hotpotqa.py
   ```
   Without this step, the first real run fails deep inside baseline evaluation with an unclear error. `scripts/run_overnight.py --dry-run` will also point this out if skipped.

4. Build the dashboard frontend once (only needed after cloning or after a frontend change — the built files are served as static assets, no Node process runs at runtime):
   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```

5. Run the overnight optimization script:
   ```bash
   poetry run python scripts/run_overnight.py
   ```
   This starts a local web dashboard at **http://127.0.0.1:8000** — open it in a browser to watch the run live (pipeline status, hypothesis, config diff, budget, experiment history) and to browse past runs.

## 🗺️ Codebase Knowledge Graph

This repo is mapped as an interactive knowledge graph — 1,000+ nodes (functions, classes, config values, docs, and design-rationale notes) connected by 2,200+ relationships (calls, imports, references, and inferred conceptual links), clustered into ~50 communities.

**➡️ [Explore the live graph](https://bhavyafattania.github.io/autonomous-rag/)** — click a node to see its neighbors, search by name, or filter by community.

Use it to get oriented before contributing:

- **New to the repo?** Start from a community hub (e.g. *LangGraph Budget Guard & State*, *Evaluator Node & RAGAS Runner*, *DI Interfaces & Protocols*) and walk outward from there instead of grepping blind.
- **Picking up an issue?** Search the node for the function/class you're touching to see everything that calls it, imports it, or conceptually relates to it — including design-rationale notes pulled from `CONTRIBUTING.md`, `docs/developer_guide.md`, and the architecture docs.
- **Reviewing a PR?** Cross-check whether a change touches a "god node" (a highly-connected core abstraction) — those changes have wider blast radius and deserve extra scrutiny. The current top god nodes are `RAGConfig`, `Provider`, `OpenAIClient`, `ICostTracker`, and `ILLMClient`.
- **Curious why something was built a certain way?** Rationale nodes (e.g. *ThreadPool Isolation for RAGAS*, *Cost Tracker Constructor Injection Decision*, *Multi-Provider Handoff*) capture the "why," not just the "what."

The graph is generated locally with [graphify](https://github.com/safishamsi/graphify) (`/graphify .` as a Claude Code skill) from the full source tree plus `docs/`, `README.md`, `CONTRIBUTING.md`, and architecture diagrams — no server, no external DB. Outputs live under `graphify-out/` (`graph.html`, `graph.json`, `GRAPH_REPORT.md`) and are regenerated whenever the codebase changes significantly; see `GRAPH_REPORT.md` for the full audit trail (god nodes, cross-community "surprising connections," and open questions worth investigating).

## 📖 Documentation

For detailed insights into the system, please refer to the following documentation:
- [Project Architecture Breakdown](docs/project_architecture_breakdown.md): Deep dive into the LangGraph loop, nodes, and system design.
- [Evaluator Code Breakdown](docs/evaluator_code_breakdown.md): How the RAGAS-based evaluation pipeline works internally.
- [Developer Guide](docs/developer_guide.md): Information on setting up the dev environment, testing, and extending the orchestration graph.
- [Overnight Execution Guide](docs/overnight_execution_guide.md): Running and monitoring long unattended optimization sessions.
- [Contributing](CONTRIBUTING.md): How to propose changes, coding conventions, and PR expectations.
