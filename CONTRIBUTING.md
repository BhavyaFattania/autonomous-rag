# Contributing to Autonomous RAG Optimizer

Thank you for your interest in contributing! This document covers everything you need to get started — from environment setup to submitting a pull request.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Fork & Clone](#fork--clone)
  - [Install Dependencies](#install-dependencies)
  - [Install Pre-commit Hooks](#install-pre-commit-hooks)
  - [Environment Variables](#environment-variables)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
  - [Branching Strategy](#branching-strategy)
  - [Making Changes](#making-changes)
  - [Running Locally](#running-locally)
- [Code Style & Quality](#code-style--quality)
  - [Formatting (Black)](#formatting-black)
  - [Linting (Ruff)](#linting-ruff)
  - [Type Checking (Mypy)](#type-checking-mypy)
- [Testing](#testing)
- [Architecture Overview](#architecture-overview)
- [How to Extend the System](#how-to-extend-the-system)
  - [Adding a New Guardrail Node](#adding-a-new-guardrail-node)
  - [Modifying the Hypothesis Generator](#modifying-the-hypothesis-generator)
  - [Adding New Evaluation Metrics](#adding-new-evaluation-metrics)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Reporting Issues](#reporting-issues)

---

## Code of Conduct

Be respectful and constructive. We are committed to providing a welcoming and inclusive experience for everyone. Harassment, discrimination, and disrespectful behaviour will not be tolerated.

---

## Getting Started

### Prerequisites

| Requirement     | Version     |
|-----------------|-------------|
| Python          | `^3.11`     |
| Poetry          | Latest      |
| Git             | Latest      |

You will also need API keys for **OpenRouter** and/or **OpenAI** to run the full pipeline (not required for unit tests).

### Fork & Clone

1. Fork the repository on GitHub.
2. Clone your fork locally:

   ```bash
   git clone https://github.com/<your-username>/autonomous-rag.git
   cd autonomous-rag
   ```

### Install Dependencies

Install all dependencies (including dev tools) via Poetry:

```bash
pip install poetry          # if you don't have it yet
poetry install --with dev
```

This installs the runtime stack (LlamaIndex, LangGraph, ChromaDB, Ragas, etc.) **and** the dev tools (`pytest`, `black`, `ruff`, `mypy`).

### Install Pre-commit Hooks

The repo ships a [`.pre-commit-config.yaml`](.pre-commit-config.yaml) that runs the same `ruff` and `black` checks CI enforces — so formatting/lint problems are caught locally *before* you push, not after a red CI run. Install the hooks once after cloning:

```bash
pip install pre-commit     # if you don't have it yet
pre-commit install
```

The hooks then run automatically on every `git commit` (only against staged files). To run them across the whole codebase on demand:

```bash
pre-commit run --all-files
```

> The hook versions are pinned to match the tool versions in `pyproject.toml`, so local hooks and CI never disagree.

### Environment Variables

Copy the example `.env` or create your own in the project root:

```env
OPENAI_API_KEY=your_openai_key
OPENROUTER_API_KEY=your_openrouter_key
```

> **Note:** Never commit `.env` files. They are already listed in `.gitignore`.

---

## Project Structure

```
autonomous-rag/
├── config/              # Pydantic settings & model routing configs
├── data/                # Corpus data (gitignored)
├── docs/                # Architecture docs, guides, and diagrams
├── prompts/             # LLM prompt templates
├── scripts/             # Utility & runner scripts
├── src/                 # Main application source
│   ├── core/            # Protocols (interfaces) & DI container
│   ├── data/            # Data loading utilities
│   ├── evaluator/       # IR metrics, RAGAS runner, scorer
│   ├── indexer/         # Vector index building & parser registry
│   ├── models/          # Pydantic data models (RAGConfig, metrics, etc.)
│   ├── orchestrator/    # LangGraph workflow nodes (budget guard, etc.)
│   ├── rag_pipeline/    # Retriever & generator implementations
│   ├── reporter/        # Report generation
│   ├── scientist/       # Hypothesis generation & reflection
│   ├── storage/         # SQLite repositories (experiments, config hashes)
│   └── utils/           # Shared utilities
├── tests/               # Pytest test suite
├── pyproject.toml       # Poetry config, tool settings
├── requirements.txt     # Pip-compatible dependency list
└── .github/workflows/   # CI pipeline (GitHub Actions)
```

---

## Development Workflow

### Branching Strategy

- **`main`** — stable, passing CI at all times.
- Create feature branches from `main`:

  ```bash
  git checkout -b feat/your-feature-name
  ```

- Use descriptive prefixes: `feat/`, `fix/`, `refactor/`, `docs/`, `test/`.

### Making Changes

1. **Read before you edit.** Always read a file before modifying it to understand the existing patterns.
2. **Keep files under 500 lines.** If a module is growing too large, split it.
3. **Preserve existing comments and docstrings** that are unrelated to your changes.
4. **Validate input at system boundaries** — use Pydantic validators or explicit checks at the edges of your modules.

### Running Locally

Run the overnight optimization loop:

```bash
poetry run python scripts/run_overnight.py
```

---

## Code Style & Quality

All formatting and linting rules are configured in [`pyproject.toml`](pyproject.toml). The CI pipeline enforces them automatically on every push and PR to `main`.

### Formatting (Black)

The project uses [Black](https://black.readthedocs.io/) with a line length of **100** and a target of Python 3.11.

```bash
# Format all files
poetry run black .

# Check formatting without modifying files
poetry run black --check .
```

### Linting (Ruff)

[Ruff](https://docs.astral.sh/ruff/) is configured to catch errors, import ordering issues, and common bugs.

```bash
# Lint
poetry run ruff check .

# Auto-fix what's safe
poetry run ruff check . --fix
```

**Selected rule sets:** `E` (pycodestyle), `F` (pyflakes), `I` (isort), `UP` (pyupgrade), `B` (flake8-bugbear).

### Type Checking (Mypy)

```bash
poetry run mypy src
```

> Mypy is currently **non-blocking** in CI (there are pre-existing errors under triage). New code should still aim for clean type annotations.

---

## Testing

The test suite lives in `tests/` and uses **pytest** with **pytest-asyncio** (`asyncio_mode = "auto"`).

```bash
# Run all tests
poetry run pytest

# Run a specific test file
poetry run pytest tests/test_scorer.py

# Run with verbose output
poetry run pytest -v
```

### Writing Tests

- Place test files in `tests/` with the `test_` prefix.
- Use `pytest-mock` for mocking external dependencies (LLM calls, API clients, database connections).
- Use `pytest-asyncio` for async test functions — they are auto-detected.
- All external services (OpenRouter, Chroma, etc.) should be mocked. Unit tests must **never** make real API calls.

### What CI Runs

Every push and pull request to `main` triggers the [CI workflow](.github/workflows/ci.yml):

| Step                | Command                       | Blocking? |
|---------------------|-------------------------------|-----------|
| Ruff (lint)         | `poetry run ruff check .`     | ✅ Yes    |
| Black (format)      | `poetry run black --check .`  | ✅ Yes    |
| Mypy (type check)   | `poetry run mypy src`         | ⚠️ No (for now) |
| Pytest              | `poetry run pytest`           | ✅ Yes    |

**Your PR must pass all blocking checks before it can be merged.**

---

## Architecture Overview

The system is orchestrated as a **LangGraph state machine** that loops through these nodes:

```
Scientist → Validator → Deduplicator → Budget Guard → Indexer → Smoke Test → Evaluator → Acceptance → Recorder → Reflection → (loop back to Scientist)
```

Key design principles:

- **Protocol-based DI** — All external dependencies (LLM clients, databases, cost trackers) are abstracted behind Python `Protocol` interfaces in `src/core/`. The `Provider` class acts as a DI container.
- **ThreadPool isolation for RAGAS** — Since RAGAS runs blocking sync evaluation, it is offloaded to a `ThreadPoolExecutor` with `nest_asyncio` to avoid deadlocking the main asyncio loop.
- **Pydantic everywhere** — Configs (`RAGConfig`), metrics (`SingleRunMetrics`, `AggregatedMetrics`), and experiment records (`ExperimentRecord`) are all strongly typed.

For a deep dive, see:

- [Project Architecture Breakdown](docs/project_architecture_breakdown.md)
- [Evaluator Code Breakdown](docs/evaluator_code_breakdown.md)
- [Developer Guide](docs/developer_guide.md)

---

## How to Extend the System

### Adding a New Guardrail Node

1. Create a new async function node in `src/orchestrator/`.
2. Register it in the LangGraph flow (see `scripts/run_overnight.py`).
3. Wire the conditional edge from `BudgetGuard` (or another node) to point to your guardrail.
4. Ensure failures route to the `HandleFail`/`Recorder` node so the `Reflection` node can analyze them.

### Modifying the Hypothesis Generator

The `Scientist` node in `src/scientist/` generates new `RAGConfig` proposals. To expand the search space:

1. Add new fields to `RAGConfig` in `src/models/`.
2. Update the Pydantic validators to enforce invariants on new parameters.
3. Adjust the scientist's prompt templates in `prompts/` to include the new dimensions.

### Adding New Evaluation Metrics

1. Add the metric computation logic to `src/evaluator/ir_metrics.py` (for IR metrics) or integrate a new RAGAS metric in `src/evaluator/ragas_setup.py`.
2. Extend `SingleRunMetrics` in `src/models/` with the new field.
3. Update `AggregatedMetrics.from_runs()` to aggregate the new metric across runs.
4. Add tests in `tests/` to cover the new metric.

---

## Submitting a Pull Request

1. **Ensure all checks pass locally** before pushing:

   ```bash
   poetry run black .
   poetry run ruff check .
   poetry run mypy src
   poetry run pytest
   ```

2. **Push your branch** and open a PR against `main`.
3. **Write a clear PR description** explaining:
   - What the change does and why.
   - Any new dependencies introduced.
   - How you tested it.
4. **Keep PRs focused.** One logical change per PR. Avoid bundling unrelated fixes.
5. **Respond to review feedback** promptly.

---

## Reporting Issues

When opening an issue, please include:

- **A clear title** summarising the problem.
- **Steps to reproduce** (commands you ran, config you used).
- **Expected vs. actual behaviour.**
- **Environment details** (Python version, OS, relevant dependency versions).
- **Logs or tracebacks** if applicable (redact any API keys).

---

Thank you for helping make Autonomous RAG Optimizer better! 🚀
