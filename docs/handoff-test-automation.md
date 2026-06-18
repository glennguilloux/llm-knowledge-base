# Handoff: Test Automation for `/mnt/apps/ForLLm/`

**Created for:** next session continuation  
**Project:** `llm-knowledge-base`  
**Project root:** `/mnt/apps/ForLLm/`  
**Date:** 2026-06-18  
**Purpose:** Continue implementing Flowmanner-style test automation concepts in this project.

---

## 1. What this project is

`/mnt/apps/ForLLm/` is a Python knowledge-base/retrieval project, not a web service.

Key facts:

- Package name: `llm-knowledge-base`
- CLI: `llm-kb`
- Retrieval layer: `llm_kb/retrieve.py`
- MCP server: `llm_kb/mcp_server.py`
- Knowledge entries: Markdown files under language/category folders
- Existing test style: root-level `test_*.py` files
- Existing CI: GitHub Actions workflows in `.github/workflows/`

Important implication:

> Do **not** copy Flowmanner's web-service health-probe model directly. This project has no `/healthz` or `/readyz`. Smoke tests should be CLI/package/MCP smoke tests, not HTTP endpoint tests.

---

## 2. What already exists

### Top-level structure

Relevant files already present:

- `pyproject.toml`
- `requirements.txt`
- `README.md`
- `CONTRIBUTING.md`
- `RELEASE_CHECKLIST.md`
- `CHANGELOG.md`
- `llm_kb/`
- `scripts/`
- `docs/`
- `.github/workflows/`
- `test_*.py`

### Existing workflows

Found 3 workflows:

- `.github/workflows/validate.yml`
- `.github/workflows/release.yml`
- `.github/workflows/freshness.yml`

`validate.yml` currently runs on push and pull request:

```bash
pip install -e ".[vector]"
pip install pytest
python -m llm_kb validate
python scripts/quality_auditor.py
python -m pytest test_retrieval.py test_entries_quality.py test_retrieval_comprehensive.py test_e2e.py test_retrieval_edge_cases.py test_phase14_profiles.py test_quality_audit.py -v --tb=short
```

This is a good base, but it does not separate smoke, sanity, regression, or slow tests.

### Existing tests

Found 12 top-level `test_*.py` files, including:

- `test_cli_commands.py`
- `test_e2e.py`
- `test_entries_quality.py`
- `test_mcp_server.py`
- `test_phase14_profiles.py`
- `test_prompt_format.py`
- `test_quality_audit.py`
- `test_retrieval.py`
- `test_retrieval_adversarial.py`
- `test_retrieval_comprehensive.py`
- `test_retrieval_edge_cases.py`
- `test_retrieval_stress.py`

### Existing quality gates

Already implemented:

- `python -m llm_kb validate`
- `python scripts/quality_auditor.py`
- `python -m pytest ...`
- GitHub Actions validation/release/freshness workflows
- `RELEASE_CHECKLIST.md`
- PR checklist in `CONTRIBUTING.md`

### Existing gaps

Missing or incomplete:

- No pytest marker taxonomy
- No dedicated smoke suite
- No dedicated sanity suite
- No formal test-case catalog
- No exploratory testing docs
- No structured test failure reports
- No pre-commit config
- No explicit environment matrix
- Logging is mostly `print()` / `sys.stderr`, with limited `logging` usage in `llm_kb/vector.py`

---

## 3. Mapping Flowmanner concepts to this project

| Flowmanner concept | Adapted meaning for `/mnt/apps/ForLLm/` |
|---|---|
| Smoke test | CLI/package/MCP smoke: `llm-kb --help`, `llm-kb search sha256`, `llm-kb prompt hash --profile medium`, `llm-kb stats` |
| Sanity test | Fast PR sanity subset: schema validation + small retrieval sanity + MCP discovery smoke |
| Regression test | Existing quality + retrieval recall suites: `test_entries_quality.py`, `test_retrieval_comprehensive.py`, `test_quality_audit.py` |
| Test cases | Extract retrieval queries from `test_retrieval_comprehensive.py` into `docs/test-cases/retrieval.md` |
| Checklists | Expand `CONTRIBUTING.md` PR checklist and `RELEASE_CHECKLIST.md` |
| Exploratory testing | Add `docs/exploratory/` charters for prompt/retrieval investigations |
| Debug logs | Add structured CLI debug output and optional test failure reports |
| Guardrails | GitHub Actions + validation + quality auditor + optional pre-commit |
| Assertions | Pytest helpers for CLI output, retrieval recall, MCP tool discovery |
| Environment matrix | Document local / CI / release / optional vector environments |

---

## 4. Recommended implementation order

### Phase 1 — Docs and organization

Create:

```text
docs/test-automation-strategy.md
docs/test-automation-policy.md
docs/test-cases/retrieval.md
docs/exploratory/README.md
docs/checklists/pr.md
docs/environment-matrix.md
```

Update:

```text
CONTRIBUTING.md
RELEASE_CHECKLIST.md
```

Goal: define the strategy before changing test behavior.

### Phase 2 — Pytest markers

Add to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = [
    "smoke: fast CLI/package smoke tests",
    "sanity: fast PR sanity checks",
    "regression: quality and retrieval regression tests",
    "mcp: MCP server tests",
    "slow: benchmark/stress tests",
]
```

Then mark tests:

- New CLI smoke tests: `@pytest.mark.smoke`
- Fast retrieval sanity tests: `@pytest.mark.sanity`
- `test_entries_quality.py`: `@pytest.mark.regression`
- `test_retrieval_comprehensive.py`: `@pytest.mark.regression`
- `test_quality_audit.py`: `@pytest.mark.regression`
- `test_mcp_server.py`: `@pytest.mark.mcp`
- `test_retrieval_stress.py`: `@pytest.mark.slow`

### Phase 3 — Add smoke and sanity tests

Recommended new files:

```text
test_smoke_cli.py
test_sanity_retrieval.py
```

Smoke examples:

```python
def test_cli_help():
    ...

def test_cli_search_sha256():
    ...

def test_cli_prompt_hash_medium():
    ...

def test_cli_stats():
    ...
```

Sanity examples:

```python
def test_retrieval_sha256_recall():
    ...

def test_retrieval_fastapi_jwt_recall():
    ...

def test_retrieval_type_script_async_recall():
    ...
```

Avoid external LLM calls in smoke/sanity tests. Keep them offline and deterministic.

### Phase 4 — CI separation

Update `.github/workflows/validate.yml` so PRs run a fast layer first:

```bash
python -m llm_kb validate
python -m pytest -m "smoke or sanity" -q
```

Keep full regression on merge/main or scheduled runs:

```bash
python -m pytest test_entries_quality.py test_retrieval_comprehensive.py test_e2e.py test_retrieval_edge_cases.py test_phase14_profiles.py test_quality_audit.py -v --tb=short
```

Consider moving heavy retrieval/stress tests to a scheduled workflow if PRs become too slow.

### Phase 5 — Debug/repro artifacts

Create a shared helper:

```text
tests/helpers.py
```

or:

```text
tests/conftest.py
```

with helpers for:

- Running CLI commands
- Asserting JSON output
- Asserting retrieval recall
- Writing failed-query reports
- Optional `run_id` / timestamped report artifacts

Example output path:

```text
reports/test-run-<timestamp>.json
reports/retrieval-misses.md
```

### Phase 6 — Guardrails

Add:

```text
.pre-commit-config.yaml
```

Suggested hooks:

- trailing-whitespace
- end-of-file-fixer
- check-yaml
- check-added-large-files
- ruff

Optional later:

- mypy
- ruff format

Also consider adding a dev extra to `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21.0",
    "ruff>=0.6.0",
    "mypy>=1.10",
]
```

---

## 5. Concrete next-session starting checklist

Start with these commands:

```bash
cd /mnt/apps/ForLLm
python -m pytest --collect-only -q
python -m llm_kb validate
llm-kb --help
llm-kb search "sha256"
llm-kb prompt "hash a file" --profile medium
llm-kb stats
```

Then implement in this order:

1. Add pytest markers to `pyproject.toml`
2. Add `test_smoke_cli.py`
3. Add `test_sanity_retrieval.py`
4. Add `docs/test-automation-strategy.md`
5. Add `docs/test-cases/retrieval.md`
6. Add `docs/exploratory/README.md`
7. Add `docs/checklists/pr.md`
8. Add `docs/environment-matrix.md`
9. Update `CONTRIBUTING.md`
10. Update `RELEASE_CHECKLIST.md`
11. Update `.github/workflows/validate.yml`

After edits, run:

```bash
python -m pytest -m "smoke or sanity" -q
python -m llm_kb validate
python -m pytest --collect-only -q
```

If time allows, run the full existing CI command from `.github/workflows/validate.yml`.

---

## 6. Important constraints

- This project is not a web service. Do not add `/healthz` or `/readyz` unless a real HTTP server is added later.
- Do not call external LLM providers in smoke/sanity tests.
- Keep smoke tests fast and deterministic.
- Keep retrieval sanity small enough for PRs.
- Keep full retrieval regression for merge/release/schedule.
- Prefer root-level test files for now because the project already uses root-level `test_*.py`.
- Do not over-engineer logging. Start with structured CLI output and optional test reports.
- Existing CI matrix is broad; separate smoke/sanity from full regression before expanding it.

---

## 7. Suggested minimal first PR

A good first PR would be:

```text
feat(test): add smoke and sanity pytest markers
```

Files:

```text
pyproject.toml
test_smoke_cli.py
test_sanity_retrieval.py
docs/test-automation-strategy.md
docs/test-cases/retrieval.md
CONTRIBUTING.md
RELEASE_CHECKLIST.md
```

Success criteria:

- `python -m pytest --collect-only -q` passes
- `python -m pytest -m "smoke or sanity" -q` passes
- `python -m llm_kb validate` passes
- `llm-kb search "sha256"` still returns results
- `llm-kb prompt "hash a file" --profile medium` still works
- `llm-kb stats` still works
