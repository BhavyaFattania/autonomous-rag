# Developer Guide

Welcome to the **Autonomous RAG Optimizer** project! This guide contains everything you need to set up your development environment, understand the testing framework, and extend the system.

## 🛠️ Development Setup

The project uses `poetry` for dependency management. To set up the development environment, make sure you install the `dev` dependencies.

```bash
poetry install --with dev
```

### Dev Dependencies Used
- **Testing:** `pytest`, `pytest-asyncio`, `pytest-mock`
- **Linting & Formatting:** `black`, `ruff`
- **Type Checking:** `mypy`

## 🧪 Testing

The test suite leverages `pytest-asyncio` for asynchronous execution. The configuration is already defined in `pyproject.toml`.

To run all tests:
```bash
poetry run pytest
```

To run linting and formatting:
```bash
poetry run black .
poetry run ruff check .
```

## 🧠 Evaluation Mechanism (Deep Dive)

The system relies heavily on `ragas` for evaluating RAG hypotheses. Since `ragas` executes blocking synchronous evaluations, it presents a challenge within a heavily asynchronous `LangGraph` flow.

### The ThreadPool Solution
To prevent `ragas` from blocking the main asyncio event loop, the `Evaluator` node offloads evaluation calls to a ThreadPool Executor (`loop.run_in_executor`).

Because `ragas` makes its own internal async calls, we apply `nest_asyncio` within the background thread. This allows the background thread to safely spin up a new event loop and run nested asynchronous API calls to OpenRouter without causing `RuntimeError: This event loop is already running`.

## 🖥️ Frontend Dashboard

Every run starts a local FastAPI + WebSocket server (`src/web/`) alongside the LangGraph loop, serving a React/TypeScript dashboard at `http://127.0.0.1:8000`. It shows the run live (current node, hypothesis, config diff vs. best, budget, experiment history) and lets you browse past runs from `experiments.sqlite`.

**Backend** (`src/web/`):
- `server.py` — FastAPI app factory (`create_app()`), owns the `ConnectionManager` that fans out broadcasts to every connected WebSocket client.
- `live.py` — `/ws/live` WebSocket endpoint. On app startup, subscribes to the run's `EventBus` (`src/core/events.py`) and streams every `ExperimentEvent` to connected clients as it's published.
- `history.py` — REST endpoints (`/api/runs`, `/api/runs/{run_id}/experiments`, etc.) for browsing historical runs, backed by `src/storage/repositories/`.

**Data flow**: `src/orchestrator/event_adapter.py`'s `adapt()` translates each raw LangGraph `astream()` tick into normalized `ExperimentEvent`s, which get published onto the `EventBus` and broadcast over the WebSocket. `src/core/dashboard_state.py`'s `DashboardState.apply()` is the pure, framework-free function that turns a stream of `ExperimentEvent`s into the plain-Python state the frontend renders — test it directly rather than through the WebSocket when adding new dashboard fields.

**Frontend** (`frontend/`, Vite + React + TypeScript): built once via `npm install && npm run build` and served as static files — no Node process runs at runtime. Re-run the build after any frontend change; CI (`.github/workflows/ci.yml`'s `frontend` job) lints (`oxlint`) and builds it on every PR.

If you add a new field to `ExperimentEvent` or `DashboardState`, update the corresponding Pydantic schema in `src/web/schemas.py` (or equivalent) so it round-trips over the WebSocket, and the matching TypeScript type on the frontend.

## 📈 Extending the LangGraph

The orchestration loop is designed to be highly modular.

### 1. Adding a New Guardrail Node
If you want to add a new check (e.g., verifying vector index density before evaluating):
1. Create a new function node.
2. Add it to the LangGraph flow in `run_overnight.py`.
3. Update the conditional edge from `BudgetGuard` (or another node) to point to your new guardrail.
4. Ensure failures correctly route to the `HandleFail` node so the failure is logged and the `Reflection` node can analyze it.

### 2. Modifying the Hypothesis Generator
The `Scientist` node is responsible for generating new configurations. You can tweak its prompts or allow it to mutate new `LlamaIndex` parameters (e.g., experimenting with different embedding models) by updating its internal Pydantic schema generation logic.
