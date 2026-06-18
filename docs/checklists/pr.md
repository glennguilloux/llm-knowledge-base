# PR Checklist

## Required before review

- [ ] Entry uses the correct language and category path.
- [ ] Frontmatter is complete and `confidence` is `high` or `medium`.
- [ ] Standard pattern includes runnable code, imports, and type hints where useful.
- [ ] Mistakes section has at least 3 `WRONG` / `CORRECT` pairs.
- [ ] Gotchas section has at least 3 useful gotchas.
- [ ] Related section links to at least 2 existing Markdown files.
- [ ] `python -m llm_kb validate` passes.
- [ ] `python -m pytest -m "smoke or sanity" -q` passes.
- [ ] Fast tests do not call external LLM providers.
- [ ] No `/healthz` or `/readyz` checks were added. This project is not a web service.
- [ ] New tests use the right pytest marker: `smoke`, `sanity`, `regression`, `mcp`, `slow`, or `external`.

## Maintainer checks

Run these for larger changes, releases, or when reviewers ask for full coverage:

```bash
python -m llm_kb validate
python scripts/quality_auditor.py
python -m pytest test_retrieval.py test_entries_quality.py test_retrieval_comprehensive.py test_e2e.py test_retrieval_edge_cases.py test_phase14_profiles.py test_quality_audit.py -v --tb=short
```

Optional extras:

```bash
pip install -e ".[vector]"
pip install -e ".[mcp]"
```

See `docs/test-automation-strategy.md` for marker definitions and `docs/environment-matrix.md` for environment choices.
