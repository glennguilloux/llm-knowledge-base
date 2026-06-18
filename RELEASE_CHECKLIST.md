# Release Checklist for v1.0.0

## Pre-Release

### Fast test gates

- [ ] Validation passes: `python -m llm_kb validate` (278/278)
- [ ] Smoke and sanity pass: `python -m pytest -m "smoke or sanity" -q`
- [ ] Fast tests do not call external LLM providers.
- [ ] No `/healthz` or `/readyz` checks were added. This project is not a web service.

### Full regression

- [ ] Full regression passes: `python -m pytest test_retrieval.py test_entries_quality.py test_retrieval_comprehensive.py test_e2e.py test_retrieval_edge_cases.py test_phase14_profiles.py test_quality_audit.py -v --tb=short`

### Release prep

- [ ] Quality scorecard: `python -m llm_kb scorecard` (92/100)
- [ ] No pre-existing failures
- [ ] CHANGELOG.md updated
- [ ] pyproject.toml version is 1.0.0
- [ ] README.md links are valid
- [ ] CONTRIBUTING.md is accurate
- [ ] .gitignore is comprehensive

See `docs/test-automation-strategy.md`, `docs/checklists/pr.md`, and `docs/environment-matrix.md` before release.

## Build
- [ ] `pip install -e .` works on fresh Python 3.10
- [ ] `pip install -e ".[vector]"` works with chromadb
- [ ] `python -m build` produces wheel and sdist
- [ ] `twine check dist/*` passes

## CLI Smoke Test
- [ ] `llm-kb --help` works
- [ ] `llm-kb search "sha256"` returns results
- [ ] `llm-kb prompt "hash a file" --profile medium` works
- [ ] `llm-kb stats` shows 278 entries
- [ ] `llm-kb validate` passes
- [ ] `llm-kb scorecard` shows 92/100
- [ ] `llm-kb profile --list` shows 38 models
- [ ] `llm-kb benchmark --export-prompts` works

## Python API
- [ ] `from llm_kb import retrieve, build_prompt, get_stats` works
- [ ] `retrieve("sha256")` returns results
- [ ] `build_prompt("test", model="qwen2.5-coder:32b")` works
- [ ] `get_stats()["total_entries"] >= 278`

## MCP Server
- [ ] `python -m llm_kb.mcp_server` starts
- [ ] Tools are discoverable

## IDE Configs
- [ ] `.cursorrules` exists and is valid
- [ ] `.vscode/tasks.json` exists and is valid JSON
- [ ] `docs/claude-desktop-config.json` exists

## Release
- [ ] `git tag v1.0.0`
- [ ] `git push origin v1.0.0`
- [ ] CI triggers
- [ ] PyPI publish succeeds
- [ ] GitHub Release is created
- [ ] `pip install llm-knowledge-base` works
