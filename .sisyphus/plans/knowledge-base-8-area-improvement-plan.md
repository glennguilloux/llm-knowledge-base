# LLM Knowledge Base — 8-Area Improvement Plan

> **Goal:** Take the knowledge base from 92/100 → 98+/100 by addressing structural gaps, retrieval IQ, testing depth, and integration with real model workflows.
> **Current state:** 385 entries, 16 language categories, keyword-only retrieval, 51 anti-pattern files, 6 test files, 38 mapped models.

---

## Phase 1: Semantic / Vector Search (Highest ROI — 1-2 days)

### Problem
Retrieval is purely keyword-based (`search_by_keywords` in `retrieve.py`). `chromadb` + `sentence-transformers` are declared as optional dependencies and standalone scripts exist (`embed_and_index.py`, `hybrid_retrieval.py`), but **nothing is wired into the actual retrieval pipeline**.

### Implementation Steps

**1.1 — Refactor vector search into the `llm_kb` package (not standalone)**
- Move `hybrid_retrieval.py` logic into `llm_kb/vector.py`
- Keep `sentence_transformers` + `chromadb` as optional deps (already configured)
- Expose `vector_search(query, language, top_k)` that mirrors `search()` interface

**1.2 — Add hybrid search to `retrieve.py`**
- New function: `hybrid_search(query, language, top_k, vector_weight=0.6, keyword_weight=0.4)`
- Fallback logic: if chromadb import fails or no index exists → pure keyword
- Cache the embedding model and chroma client as module-level singletons (lazy init)

**1.3 — Add index build command to CLI**
- `llm-kb index` — runs `embed_and_index.py` logic but integrated, not standalone
- Should optionally run in CI after entry changes

**1.4 — Wire into `search()` and `build_prompt()`**
- Add `use_vector=True` parameter to `search()` and `build_prompt()`
- Profile-aware: small models get more vector weight (catch loose matches), large models less (they prefer precision)

**Files to modify:**
- `pyproject.toml` — keep `vector` extra
- `llm_kb/retrieve.py` — add hybrid search
- `llm_kb/__init__.py` — expose new API
- `llm_kb/cli.py` — add `cmd_index`
- `llm_kb/prompt.py` — propagate `use_vector` param
- `llm_kb/mcp_server.py` — expose vector search toggle
- `embed_and_index.py` — deprecate or remove (logic moves into llm_kb/)

---

## Phase 2: Better Prompt Builder & Model Invocation (2-3 days)

### Problem
The prompt builder (`llm_kb/prompt.py`) just concatenates entries into a static template. No Jinja2-style templating, no direct model invocation. The `llm-kb prompt ... | ollama run ...` shell pipeline is the only way to use it.

### Implementation Steps

**2.1 — Add Jinja2 templating for system prompts (optional dep)**
- `prompts/` directory already has `small.md`, `medium.md`, `large.md` — extend these with template variables
- Support conditionals: `{% if include_mistakes %}...{% endif %}`
- Support formatting blocks per model: `{% if entry_mode == "reference" %}...{% endif %}`
- Fall back to f-string templates if Jinja2 not installed

**2.2 — Implement `llm-kb ask` command**
- New CLI command: `llm-kb ask "query"` that:
  1. Retrieves relevant entries
  2. Builds a prompt with knowledge injection
  3. Calls an LLM endpoint directly and returns the response
- Support Ollama (default), OpenAI-compatible APIs, custom endpoints
- Configuration via `~/.config/llm-kb/config.toml` or env vars

**2.3 — Add template customization**
- Allow users to override system prompts via `~/.config/llm-kb/prompts/`
- Add `--system-prompt` flag to `llm-kb prompt` for custom templates
- Add `--format-template` flags: `openai-chat`, `claude-xml`, `raw-text`

**Files to modify/create:**
- `pyproject.toml` — add `jinja2` optional dep, `llm-kb ask` entry point or script
- `llm_kb/prompt.py` — add Jinja2 rendering, template resolution
- `llm_kb/cli.py` — add `cmd_ask`
- `llm_kb/prompts/*.md` — upgrade to Jinja2 templates
- `llm_kb/model_client.py` (new) — abstraction for Ollama/OpenAI/local endpoints

---

## Phase 3: Coverage Gaps (3-4 days — content work)

### Problem
Detailed per-language gaps identified. Python at 101 entries has the most but misses Pydantic v2, FastAPI WebSockets, SQLModel, asyncio.TaskGroup, match/case. TypeScript missing tRPC, TanStack Query, Bun runtime. Go/Rust/Java/SQL all have documented gaps.

### Implementation Steps

**3.1 — Create entry generator script**
- Use `scripts/entry_generator.py` (already exists) to scaffold missing entries from templates
- Generate from `scripts/gap_detector.py` output (already 813 lines, produces `gap_report.md`)

**3.2 — New entries per language (prioritized by gap report)**

| Language | Priority Gaps | New Entries |
|---|---|---|
| Python | Pydantic v2 deep, FastAPI WebSockets, SQLModel, Alembic deep, pytest parametrize deep, asyncio.TaskGroup, match/case | 7 |
| TypeScript | tRPC deep, Zod vs Joi, TanStack Query deep, Bun runtime, Next.js App Router deep | 5 |
| Go | slog deep, Wire DI, embed package, modern mux (net/http 1.22+), context deep | 5 |
| Rust | thiserror vs anyhow deep, async traits, tokio::select!, workspace management | 4 |
| Java | Virtual threads deep, Records pattern matching, sealed classes, Spring Boot 3 + GraalVM | 4 |
| SQL | Window functions deep, recursive CTEs, JSON path queries, keyset pagination, RETURNING clause | 5 |

**3.3 — Exploit `references/` repos as entry source material**
The 6 cloned repos in `references/` contain GoF design patterns, PHP patterns, Go patterns, Java patterns, and Python patterns — directly usable as entry content:
- `references/python-patterns/` → Python entry skeletons
- `references/java-design-patterns/` → Java entry skeletons
- `references/go-patterns/` → Go entry skeletons
- `references/DesignPatternsPHP/` → PHP entry skeletons

Write `scripts/crawl_references.py` that:
1. Scans each reference repo for documented patterns (look for README.md, docstrings, or directory names)
2. Cross-references against existing entry IDs/titles
3. Auto-generates markdown skeletons with frontmatter (id, title, language, category, tags) + Standard Pattern section scaffolded from the reference code + a `# Autogenerated from: references/$REPO` comment
4. Outputs to `references/candidate_entries/` — ready for human review to fill in mistakes/gotchas

This cuts Phase 3 from 3-4 days to ~2 days. The skeletons handle the mechanical part; you only write the gotchas and mistakes.

**3.4 — Run `scripts/gap_detector.py` and address top-20 gaps**
- Regenerate `gap_report.md`
- Assign action items per gap
- Track progress in scorecard

**Files to modify/create:**
- `python/data/`, `typescript/`, `go/`, `rust/`, `java/`, `sql/` — new entry files
- `scripts/gap_detector.py` — ensure it covers all identified gaps
- `scripts/crawl_references.py` (new) — harvest entry skeletons from references/
- `test_retrieval_comprehensive.py` — add test cases for new entries

---

## Phase 4: Anti-Pattern Coverage (1-2 days)

### Problem
Scorecard shows 80/100 for anti-pattern coverage — weakest metric. 51 files exist but they're mostly language-level overviews (e.g., `python-antipatterns.md`), not deep entries with individual WRONG/CORRECT patterns.

### Implementation Steps

**4.1 — Deep anti-pattern entries per language**
Convert the single-file language summaries into structured entries in `anti-patterns/`:

| Missing | Target Entry |
|---|---|
| Python: orjson vs json | `anti-patterns/python-orjson-pitfalls.md` |
| Python: shutil.rmtree footguns | `anti-patterns/python-shutil-rmtree.md` |
| Python: functools.lru_cache unbounded | `anti-patterns/python-lru-cache-memory-leak.md` |
| TypeScript: any propagation | `anti-patterns/typescript-any-propagation.md` |
| TypeScript: useEffect cleanup | `anti-patterns/typescript-useeffect-cleanup.md` |
| Rust: unwrap/expect in production | `anti-patterns/rust-unwrap-in-production.md` |
| Go: defer inside loop | `anti-patterns/go-defer-in-loop.md` |
| Go: recover misuse | `anti-patterns/go-recover-misuse.md` |

**4.2 — Wiring anti-patterns into retrieval**
- Ensure anti-pattern entries use the proper `category: "anti-patterns"` frontmatter
- The `_boost_entries` in prompt.py already boosts anti-patterns — add a flag `--include-anti-patterns` to CLI
- Add anti-pattern queries to `test_retrieval_comprehensive.py`

**Files to modify/create:**
- `anti-patterns/` — 8-12 new entries
- `llm_kb/cli.py` — `--include-anti-patterns` flag
- `test_retrieval_comprehensive.py` — new test cases

---

## Phase 5: Smarter Retrieval (2-3 days)

### Problem
Retrieval is simple keyword scoring. No query expansion, no semantic boosting, no model-aware filtering at search time.

### Implementation Steps

**5.1 — Query expansion**
Before searching, expand abbreviations and synonyms:
```
jwt → jwt, json web token, auth, authentication, token, oauth
orm → orm, object relational mapping, sqlalchemy, hibernate, prisma
ci → ci, continuous integration, github actions, gitlab ci
```
- Implementation: `llm_kb/expand.py` with a curated expansion map
- Optional: use a small embeddings model for dynamic expansion when vector search is enabled

**5.2 — Tag-based cross-reference boosting**
- If an entry has tags that overlap with the query AND is referenced by Other entries via Related links → boost its score
- Query: traverse the Related link graph and add bonus points for well-linked entries
- Implementation: add `score_cross_reference_boost()` to retrieve.py scoring

**5.3 — Model-aware filtering in `cmd_search`**
- Currently `cli.py`'s `cmd_search` ignores profiles — it just returns `top_k`
- Fix: add `--model` and `--profile` flags to `llm-kb search`
- When profile is specified, `cmd_search` uses `condenser.py` to truncate entries to the right level
- Return mode-appropriate output (small=full text, medium=condensed, large=reference card)

**5.4 — Results diversification**
- When top results are all from the same category, penalize duplicates
- Ensure cross-category diversity in returned entries

**Files to modify:**
- `llm_kb/expand.py` (new)
- `llm_kb/retrieve.py` — add expansion step, tag boosting
- `llm_kb/cli.py` — `cmd_search` profile awareness
- `llm_kb/__init__.py` — expose expand API

**⚠️ Sequencing note:** P5 must run BEFORE P1 within Week 1. The scoring/subsetting layer (query expansion, tag boosting, model-aware filtering) is standalone logic that P1's vector search then plugs into. Reversed order would mean vector search wires into a scoring pipeline that then gets refactored underneath it — merge conflict churn.

---

## Phase 6: Testing Gaps (1-2 days)

### Problem
6 test files exist but: no MCP server test, no stress test with full 385 entries, no dedup test, no prompt command format test.

### Implementation Steps

**6.1 — MCP server integration test**
- Use `mcp` library's testing utilities or just call tool functions directly
- Test: `search_knowledge`, `build_code_prompt`, `list_languages`, `get_entry`, `get_model_profile`
- Test: tool invocation with various parameters, edge cases (empty query, unknown language)

**6.2 — Stress test for search with full dataset**
- Load ALL 385 entries
- Run random queries from `test_retrieval_comprehensive.py`
- Verify response time < 200ms for keyword search
- Verify response time < 2s for vector search (with cold start)
- Use `pytest-benchmark` or simple timing assertions

**6.3 — Deduplication test**
- Test `load_entries()` with a controlled environment containing duplicate IDs
- Verify the `seen` dict logic works correctly
- Test symlinked data directories

**6.4 — Prompt command format test**
- Test `build_prompt()` output format for all three profiles
- Verify output contains correct template sections
- Test budget calculation with token limits
- Test JSON metadata output format

**6.5 — Smoke test for `llm-kb index` CLI command**
- Test `llm-kb index` runs without crashing (even if chromadb not installed)
- Verify graceful fallback message when vector deps are missing
- Test `llm-kb index --force` re-indexes existing data
- Test that after indexing, `llm-kb search --use-vector` works and falls back to keyword when vector unavailable

**6.6 — Add `[skip ci]` compatibility**
- Ensure test runs can be skipped for non-critical changes

**Files to create/modify:**
- `test_mcp_server.py` (new)
- `test_retrieval_stress.py` (new)
- `test_retrieval.py` — add dedup test
- `test_prompt_format.py` (new)
- `test_cli_commands.py` (new) — includes `llm-kb index` smoke test

---

## Phase 7: Project Structure Housekeeping (1 day)

### Problem
- `LLM_CODEBASE_KNOWLEDGE_BASE.md` (35KB) duplicates README content in repo root
- `references/` (6 cloned repos) not integrated into any workflow
- `scripts/gap_detector.py` referenced in README but not auto-run
- `prompt_builder.py` duplicates `llm_kb/prompt.py` — legacy standalone script

### Implementation Steps

**7.1 — Move design doc**
- `LLM_CODEBASE_KNOWLEDGE_BASE.md` → `docs/architecture.md`
- Keep a one-line redirect in root

**7.2 — Integrate `references/` into gap detection**
- Write `scripts/crawl_references.py` that extracts patterns from cloned repos and cross-references them against existing entries
- Output: "These patterns from $REPO are not covered by any entry"
- Run as part of CI validation or gap detection

**7.3 — Make gap detector a CLI command**
- Add `llm-kb gaps` command that runs gap analysis
- Output: markdown report to stdout or file
- Integrate: `llm-kb gaps --language python --output gaps-python.md`

**7.4 — Clean up duplicate scripts**
- `prompt_builder.py` is a legacy standalone — add deprecation warning and redirect to `llm -m llm_kb.prompt`
- Consider merging `retrieval.py` (root-level) with `llm_kb/retrieve.py` — or clarify the relationship
- Either alias `retrieval.py` to `llm_kb.retrieve` or standardize on one module

**Files to modify:**
- `LLM_CODEBASE_KNOWLEDGE_BASE.md` → move to `docs/architecture.md`
- `scripts/crawl_references.py` (new)
- `llm_kb/cli.py` — add `cmd_gaps`
- `scripts/gap_detector.py` — refactor to be importable from llm_kb
- `prompt_builder.py` — add deprecation notice

---

## Phase 8: Standout / Differentiator Features (3-5 days — optional, order independently)

| Feature | Effort | Impact | Dependencies |
|---|---|---|---|
| **8.1** `llm-kb ask` with model invocation | Medium (1 day) | High | Phase 2 |
| **8.2** Auto-expire entries (last_verified > 12mo → flag) | Low (4h) | Medium | None |
| **8.3** Web UI / dashboard | High (3-5 days) | Medium | Phase 1 |
| **8.4** GitHub Actions auto-revalidation of stale entries | Low (4h) | Medium | None |
| **8.5** Reference repo integration for auto-gap detection | Medium (1 day) | Medium | Phase 7.2 |
| **8.6** Entry templates for remaining languages | Low (2h) | Low | None |

### 8.1 — `llm-kb ask` Command
- Implemented in Phase 2 already
- Key differentiator: retrieves + prompts + invokes in one shot
- Default: pipe to Ollama. Configurable: OpenAI, Anthropic, local endpoints

### 8.2 — Auto-Expire System
- `scripts/auto_freshness.py` already exists
- Wire it into: `llm-kb validate --stale`
- Add to `scorecard.py`: count entries with `last_verified` > 365 days
- Output: list of stale entries, auto-flag in CI

### 8.3 — Web UI (defer or split)
- FastAPI web app that wraps the MCP server logic
- Pages: search, browse by language/category, view entry, quality dashboard
- **Recommendation:** Defer this — highest effort, lowest ROI for core value prop

### 8.4 — CI Auto-Revalidation
- `.github/workflows/staleness.yml` — weekly cron
- Runs `python scripts/auto_freshness.py --ci`
- Opens PR if entries are stale: "Auto: flagged 12 entries as stale"
- Links to instructions for updating `last_verified`

### 8.5 — Reference Repo Integration
- `scripts/crawl_references.py` scans the 6 cloned repos in `references/`
- Maps patterns found in reference repos to existing entries
- Flags uncovered patterns as candidate entries
- Output to `scripts/gap_report.md`

### 8.6 — Remaining Entry Templates
- Currently only 3 templates: `python.md`, `typescript.md`, `java.md`
- Create: `go.md`, `rust.md`, `csharp.md`, `bash.md`, `kotlin.md`, `php.md`, `swift.md`, `sql.md`
- Use existing `templates/python.md` as reference structure

---

## Execution Order & Milestones

```
Milestone A (Week 1) — Foundation
  Phase 5: Smarter retrieval FIRST (query expansion, tag boosting, model-aware search)
    → This is the scoring/subsetting layer. Standalone logic, no new deps.
  Phase 1: Semantic search SECOND (wire chromadb into pipeline)
    → Vector search plugs INTO the P5 scoring pipeline, so P5 must exist first.
  Phase 6: Testing gaps (MCP test, stress test, dedup test, index smoke test)
    → Tests you can run before/after to verify nothing regressed.
 
Milestone B (Week 2) — Prompt & Content
  Phase 2: Better prompt builder + llm-kb ask
  Phase 3: Coverage gaps (30 new entries across 6 languages)
    → Use scripts/crawl_references.py to scaffold from references/ repos (Day 1)
    → Then fill in gotchas/mistakes manually (Days 2-3)
 
Milestone C (Week 3) — Polish
  Phase 4: Anti-pattern coverage (8-12 new deep entries)
  Phase 7: Project structure cleanup
  Phase 8: Standout features (auto-expire, CI revalidation, reference integration)
```

## Known Issues & Corrections (Post-Review)

### 1. Vector index location ambiguity (P1)
`embed_and_index.py` saves ChromaDB to `./chroma_db` (CWD). But `llm_kb.retrieve.get_kb_path()` resolves to `llm_kb/data/` when running as installed package. **Fix:** Make `CHROMA_DIR` configurable via `LLM_KB_CHROMA_DIR` env var, defaulting to `~/.cache/llm-kb/chroma_db/` for the installed package and `./chroma_db` when run from source. Update `embed_and_index.py` to accept `--chroma-dir`.

### 2. Vector search must remain optional (P1)
`sentence-transformers` pulls in PyTorch (~800MB). Many users install `llm-knowledge-base` for fast keyword search. **Rule:** Vector search is ALWAYS opt-in. Pure keyword remains the default path. The PyPI install should NOT include `vector` extras by default. CLI should gracefully fall back: "Vector search not available. Install: pip install llm-knowledge-base[vector]"

### 3. Anti-pattern entry locations (P4)
Root `anti-patterns/` is the authoritative source. `llm_kb/data/anti-patterns/` is a bundled copy. All new entries go in **root** `anti-patterns/`. The `llm_kb/data/` directory is a build artifact — do NOT write there directly.

### 4. `retrieval.py` vs `llm_kb/retrieve.py` (P7)
Root `retrieval.py` is the original standalone module. `llm_kb/retrieve.py` is the package version with schema imports. They have diverged slightly. **Fix:** After P7, root `retrieval.py` becomes `from llm_kb.retrieve import *` plus a deprecation warning. All tests import from root `retrieval` — update them to import from `llm_kb.retrieve` after the alias is in place.

### 5. Pydantic v2 coverage nuance (P3)
`python/data/pydantic-v2-models.md` already exists and covers basic models. The gap is **deep coverage**: `model_validator`, computed fields, serialization with `model_dump`, generic models, and advanced validation. The plan should generate `python/data/pydantic-v2-advanced.md` rather than redoing basic coverage.

### 6. No `python/async/` gap for TaskGroup
`python/concurrency/asyncio-basics.md` exists but doesn't cover `TaskGroup` (3.11+) or `asyncio.TaskGroup` error semantics. New entry: `python/concurrency/asyncio-taskgroup.md`.

---

## Scorecard Target After Each Milestone

| Metric | Current | Milestone A | Milestone B | Milestone C |
|---|---|---|---|---|
| Coverage | 100/100 | 100/100 | 100/100 | 100/100 |
| Depth | 93/100 | 94/100 | 96/100 | 97/100 |
| Cross-references | 93/100 | 94/100 | 95/100 | 96/100 |
| Freshness | 99/100 | 99/100 | 99/100 | 100/100 |
| Anti-pattern coverage | 80/100 | 82/100 | 85/100 | 95/100 |
| Retrieval test coverage | 87/100 | 92/100 | 93/100 | 95/100 |
| **Overall** | **92/100** | **94/100** | **96/100** | **98/100** |
