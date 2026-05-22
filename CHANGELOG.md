# Changelog

All notable changes to the LLM Knowledge Base project.

---

## [1.0.0] - 2025-01-15

### Added

- **278 knowledge entries** across 10 languages: Python (74), Java (39), TypeScript (35), Go (20), Rust (15), C# (11), Bash/Shell (16), SQL (11), Crypto (5), DevOps/others (54)
- **Python package** (`pip install llm-knowledge-base`) with public API: `retrieve()`, `build_prompt()`, `get_stats()`
- **CLI tool** with 6 commands: `search`, `prompt`, `stats`, `validate`, `scorecard`, `benchmark`
- **MCP server** (`python -m llm_kb.mcp_server`) for Claude Desktop, Cursor, Continue with 4 tools: `search_knowledge`, `build_code_prompt`, `list_languages`, `get_entry`
- **Hybrid retrieval** system combining grep keyword matching with optional ChromaDB vector search
- **Context budget calculator** that estimates token usage and fits entries within model context windows
- **Quality scorecard** with 6 metrics: Coverage (100), Depth (95), Cross-references (94), Freshness (99), Anti-patterns (80), Retrieval (87) — **Overall: 92/100**
- **Code generation benchmark** (20 tasks across 10 languages, +66% improvement with knowledge base)
- **Integration guides** for Ollama, LM Studio, OpenAI-compatible APIs, VS Code, and Neovim
- **CI pipeline** (`.github/workflows/validate.yml`) — validates on every push and PR
- **13 anti-pattern entries** across 8 languages
- **20 entries with Real-World Example sections**
- **Automated freshness pipeline** (`scripts/auto_freshness.py`) — version checks, deprecation detection, link checking, consistency analysis
- **Entry generator** (`scripts/entry_generator.py`) — bootstrap draft entries from URLs, GitHub repos, code files, and prompts
- **Gap detector** (`scripts/gap_detector.py`) — trend analysis, internal coverage analysis, query simulation
- **Release workflow** (`.github/workflows/release.yml`) — automated PyPI publishing on version tags
- **Monthly freshness CI** (`.github/workflows/freshness.yml`) — scheduled checks with auto-issue creation
- **Hosted API design document** (`docs/architecture/hosted-api-design.md`) for future deployment
- **Phase 14 — Model profiles** (small/medium/large) for 38 mapped models, auto-adaptive context condensation, model-aware prompt builder
- **Phase 15 — Comprehensive testing** (54 new tests): e2e tests, edge case tests, profile tests, retrieval comprehensive — 2,790/2,790 tests pass
- **Phase 16 — v1.0.0 release readiness**: Maven/Gradle build entries (java-build-maven-patterns, java-build-gradle-basics), IDE integration configs (Cursor `.cursorrules`, VS Code tasks, Claude Desktop config), cross-platform CI test matrix (3 OS × 4 Python versions), updated release pipeline with trusted PyPI publishing

### Languages Covered

Python (74), Java (39), TypeScript (35), Go (20), Rust (15), C# (11), Bash (5), SQL (11), Crypto (5), DevOps (5+)

### Quality Metrics (as of v1.0.0)

| Metric               | Score |
|----------------------|-------|
| Coverage             | 100   |
| Depth                | 95    |
| Cross-references     | 94    |
| Freshness            | 99    |
| Anti-pattern coverage| 80    |
| Retrieval accuracy   | 87    |
| **Overall**          | **92** |

### Key Dependencies

- **Required:** Python 3.10+, PyYAML
- **Optional:** ChromaDB (vector search), MCP SDK (MCP server)
