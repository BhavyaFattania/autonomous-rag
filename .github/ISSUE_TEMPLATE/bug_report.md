---
name: Bug report
about: Report a problem with the optimizer, dashboard, or evaluation pipeline
title: ''
labels: bug
assignees: ''

---

**Describe the bug**
A clear and concise description of what went wrong.

**Steps to reproduce**
Commands you ran and the config you used, e.g.:
1. `poetry run python scripts/run_overnight.py --max-exp 5 --max-hours 1`
2. Config used: `config/run_settings.yaml` (paste relevant fields, or attach the file)
3. See error

**Expected vs. actual behaviour**
What you expected to happen, and what actually happened.

**Environment**
- OS: [e.g. Windows 11, Ubuntu 22.04]
- Python version: `python --version`
- `llm_provider` in use (`openrouter` / `openai`):
- Relevant dependency versions (from `poetry show`, if suspected version-related):

**Run/experiment ID (if applicable)**
If the bug happened during an overnight run, the `run_id` or `experiment_id` from the dashboard or `experiments.sqlite` helps a lot.

**Logs or tracebacks**
Paste the relevant log output or traceback. **Redact any API keys first.**

**Additional context**
Anything else that seems relevant (corpus used, recent config changes, etc.).
