# Test Automation Strategy

## Scope

`llm-knowledge-base` is a Python package, CLI, retrieval layer, and MCP server. It is not a web service.

Do not add or require `/healthz` or `/readyz` checks. Use CLI, package, retrieval, quality, and MCP checks instead.

## Marker taxonomy

| Marker | Purpose | Fast PR gate? | External LLM allowed? |
| --- | --- | --- | --- |
| `smoke` | Fast confidence checks for install, CLI help, basic search, prompt formatting, stats, and package imports. | Yes | No |
| `sanity` | Small deterministic checks for schema, quality, retrieval recall, and MCP discovery. | Yes | No |
| `regression` | Full quality and retrieval coverage that protects existing behavior. | No | No by default |
| `mcp` | MCP server startup, tool discovery, and protocol behavior. | Optional | No by default |
| `slow` | Stress, benchmark, large retrieval, or expensive tests. | No | No by default |
| `external` | Tests that need an external LLM provider, cloud service, or networked dependency. | No | Yes, only when explicitly enabled |

## Fast PR gate

Use this before opening a PR:

```bash
python -m llm_kb validate
python -m pytest -m "smoke or sanity" -q
```

Rules:

- Smoke and sanity tests must be deterministic.
- Smoke and sanity tests must not call external LLM providers.
- Smoke and sanity tests must not require `/healthz` or `/readyz`.
- Tests that need external LLMs must use the `external` marker and be skipped by default.

## Full regression

Maintainers run the full regression command when preparing a release or reviewing broad changes:

```bash
python -m llm_kb validate
python scripts/quality_auditor.py
python -m pytest test_retrieval.py test_entries_quality.py test_retrieval_comprehensive.py test_e2e.py test_retrieval_edge_cases.py test_phase14_profiles.py test_quality_audit.py -v --tb=short
```

This matches the full-regression portion of `validate.yml`. Do not invent a different CI regression command unless the workflow is updated.

## Retrieval expectations

Retrieval tests use representative queries from `test_retrieval_comprehensive.py`.

- `recall@1` is tracked but not used as a hard fail for every case.
- `recall@3` must return at least one expected entry ID.
- `recall@5` must return at least one expected entry ID.
- Overall `recall@3` must stay at or above 80 percent.

See `docs/test-cases/retrieval.md` for representative cases.

## Optional environments

Use extras only when the test needs them:

```bash
pip install -e ".[vector]"
pip install -e ".[mcp]"
```

External LLM/manual tests belong in the `external` marker and are not part of the PR gate. See `docs/environment-matrix.md`.

## Exploratory testing

Use `docs/exploratory/README.md` for time-boxed investigations into prompt behavior, retrieval failures, edge cases, and manual model comparisons. Exploratory sessions are useful for finding new regression cases, but only deterministic findings should become automated tests.
