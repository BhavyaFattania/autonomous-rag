Fixes #<!-- Add issue number here. This will automatically close the issue. If you do not solve the issue entirely, please change the message to e.g. "First steps for issue #IssueNumber". -->

## Changes
<!-- Add here what changes were made in this pull request and, if possible, provide links. -->

## How was this tested?
<!-- Describe how you verified the change: e.g. `pytest`, a `--dry-run`, or a bounded overnight run. Fill "> N/A" if not applicable. -->

**Checklist**: <!-- Please tick the following check boxes with `[x]` if the respective task is completed. -->
- [ ] **No hard coding / no secrets**: I have used `config/*.yaml` + Pydantic settings instead of hard-coded values, and committed no credentials or `.env` files.
- [ ] **File placement**: No working files or tests added to the repo root — code lives under `src/`, `tests/`, `config/`, `docs/`, or `scripts/`.
- [ ] **Code reformatting**: I have formatted the code with `black` and it passes `black --check .`.
- [ ] **Code analysis**: My code passes `ruff check .` and the tests pass with `pytest`.
