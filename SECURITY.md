# Security Policy

## Supported Versions

| Version | Supported          |
| ---------| --------------------|
| 0.1.x   | :white_check_mark: |

> As the project matures past `1.0`, older minor versions will be phased out of active security support. This table will be updated accordingly.

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Instead, please report them privately:

1. **Email:** Send a detailed report to **bhavyajfattania@gmail.com** with the subject line `[SECURITY] autonomous-rag`.
2. **GitHub Private Advisory:** Alternatively, use [GitHub's private vulnerability reporting](https://github.com/BhavyaFattania/autonomous-rag/security/advisories/new) to file a confidential advisory directly on this repository.

### What to Include

- A clear description of the vulnerability and its potential impact.
- Steps to reproduce (commands, configs, input data).
- Affected component(s) (e.g., `src/evaluator/`, `config/`, API integration layer).
- Any suggested fix or mitigation, if you have one.

### Response Timeline

| Action                          | Target      |
|---------------------------------|-------------|
| Acknowledgement of your report  | 48 hours    |
| Initial triage and assessment   | 5 days      |
| Patch release (if confirmed)    | 14 days     |

You will be kept informed throughout the process. If a vulnerability is confirmed, we will credit you in the release notes (unless you prefer to remain anonymous).

If a report is declined, we will provide a written explanation of why.

## Security Considerations for This Project

The Autonomous RAG Optimizer has a specific threat surface that contributors and operators should be aware of:

### API Keys & Secrets

- **Never** commit `.env` files, API keys, or credentials. They are gitignored by default.
- All secrets (`OPENAI_API_KEY`, `OPENROUTER_API_KEY`) must be loaded from environment variables via `pydantic-settings`, not hardcoded.
- Review PRs carefully for accidental secret exposure in logs, error messages, or test fixtures.

### Cost & Budget Guardrails

- The system makes real, billable API calls to OpenRouter/OpenAI during overnight runs.
- The `budget_guard_node` enforces hard cost ceilings. Any changes to budget logic in `src/orchestrator/` should be reviewed with extra scrutiny — a bug here can cause runaway billing.
- The `ICostTracker` protocol in `src/core/` tracks cumulative spend. Bypassing or weakening this interface is considered a security-sensitive change.

### LLM Prompt Injection

- The `Scientist` node feeds historical experiment data into LLM prompts. Ensure that user-supplied corpus data or config values cannot inject malicious instructions into prompt templates under `prompts/`.
- Evaluation questions and ground truths loaded from `data/` are passed through to LLM calls — treat them as untrusted input.

### Database Integrity

- Experiment data is stored in a local SQLite database (`aiosqlite`).
- SQL queries in `src/storage/` must use parameterized statements. Never interpolate user-controlled values into raw SQL strings.

### Dependency Supply Chain

- Pin critical dependencies in `pyproject.toml` to exact versions where possible.
- Regularly audit dependencies for known vulnerabilities:
  ```bash
  pip audit
  ```
- Be cautious when updating `ragas`, `llama-index-*`, or `langchain-*` — these are fast-moving ecosystems with frequent breaking changes.

## Scope

The following are **in scope** for security reports:

- Secret leakage (API keys in logs, error output, or committed files)
- Budget guard bypasses that could cause uncontrolled API spend
- SQL injection in storage repositories
- Prompt injection vectors in scientist/evaluator prompts
- Dependency vulnerabilities in direct dependencies
- Authentication or authorization issues in any future web UI

The following are **out of scope**:

- Vulnerabilities in upstream services (OpenRouter, OpenAI, Cohere) — report those to the respective providers.
- Issues requiring physical access to the machine running the optimizer.
- Denial-of-service via intentionally malformed corpus data (the system is designed for trusted local use).
