# Environment Matrix

## Local development

Use this for normal entry edits and small test additions.

| Need | Command |
| --- | --- |
| Install package | `pip install -e .` |
| Validate entries | `python -m llm_kb validate` |
| Fast PR checks | `python -m pytest -m "smoke or sanity" -q` |
| Full regression | `python -m pytest test_retrieval.py test_entries_quality.py test_retrieval_comprehensive.py test_e2e.py test_retrieval_edge_cases.py test_phase14_profiles.py test_quality_audit.py -v --tb=short` |

Local tests should be offline and deterministic. Do not call external LLM providers in smoke or sanity tests.

## CI matrix

Current `validate.yml` coverage is split into two layers:

| Layer | Install | Commands |
| --- | --- | --- |
| Fast PR gate | `pip install -e .` | `python -m llm_kb validate`; `python -m pytest -m "smoke or sanity" -q` |
| Full regression | `pip install -e ".[vector]"` | `python -m llm_kb validate`; `python scripts/quality_auditor.py`; `python -m pytest test_retrieval.py test_entries_quality.py test_retrieval_comprehensive.py test_e2e.py test_retrieval_edge_cases.py test_phase14_profiles.py test_quality_audit.py -v --tb=short` |

Both layers still run on `ubuntu-latest`, `macos-latest`, and `windows-latest` with Python `3.10`, `3.11`, `3.12`, and `3.13`.

Do not add new CI commands unless `.github/workflows/validate.yml` is updated too.

## Optional vector extra

Use the vector extra when testing ChromaDB or vector-backed retrieval:

```bash
pip install -e ".[vector]"
```

Basic CLI, schema validation, and grep-based retrieval do not require the vector extra.

## Optional MCP extra

Use the MCP extra when testing `llm_kb.mcp_server`:

```bash
pip install -e ".[mcp]"
```

MCP smoke tests should verify startup and tool discovery without calling external LLMs.

## External LLM/manual environment

Use this only for manual or explicitly enabled external tests.

| Need | Guidance |
| --- | --- |
| External LLM provider | Mark tests `external` and skip by default. |
| Credentials | Use environment variables. Do not commit secrets. |
| Ollama/local model | Use the `ollama` extra only when the test needs model calls. |
| PR gate | Do not include external LLM calls in `smoke` or `sanity`. |
| Release gate | Prefer deterministic CLI, retrieval, quality, and MCP checks before optional external checks. |

External LLM/manual tests are useful for prompt quality experiments, but they are not the source of truth for PR merges.
