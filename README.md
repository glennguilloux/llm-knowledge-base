# LLM Knowledge Base

Retrieval-ready code patterns that help small LLMs write correct, idiomatic code.

**Current baseline:** 670 validated entries, 16 languages, 16 categories, 38 mapped model profiles, 96/100 quality score. No ML dependencies are required for the default CLI, retrieval layer, prompt builder, or MCP server.

![Validate](https://github.com/glennguilloux/llm-knowledge-base/actions/workflows/validate.yml/badge.svg)
![Release](https://github.com/glennguilloux/llm-knowledge-base/actions/workflows/release.yml/badge.svg)
![PyPI](https://img.shields.io/pypi/v/llm-knowledge-base)
![Python](https://img.shields.io/pypi/pyversions/llm-knowledge-base)
![License](https://img.shields.io/badge/license-MIT-blue)

---

## The Problem

Small coding models are fast and cheap, but they often hallucinate APIs, invent nonexistent methods, and miss framework-specific conventions. Larger models are better, but they still miss project-specific patterns and version-sensitive details.

**LLM Knowledge Base fixes that by retrieving verified examples before the model writes code.** A user asks for a coding task, the package finds relevant entries, condenses them for the target model size, and injects the result into the prompt.

---

## Current Baseline

| Area | Current state |
|:---|:---|
| Entries | 670 validated knowledge entries |
| Languages | 16: Bash, C#, Docker, Go, Java, JavaScript, Kotlin, Multi, PHP, Python, Rust, Shell, SQL, Swift, TypeScript, YAML |
| Categories | 16: anti-patterns, API design, build, concurrency, crypto, data, DB, DevOps, error handling, patterns, performance, project conventions, security, stdlib, testing, web |
| Model support | 38 mapped models with small, medium, and large profiles |
| Quality score | 96/100 |
| Validation | `python -m llm_kb validate` reports 670/670 |
| Quality audit | 4,002/4,002 checks |
| Retrieval regression | 1,715/1,715 representative retrieval cases |
| CI | Ubuntu, macOS, and Windows across Python 3.10-3.13 |

---

## Install

```bash
pip install llm-knowledge-base
```

Install from source when you want the latest repository state:

```bash
pip install -e .
```

Optional extras:

| Extra | Use case |
|:---|:---|
| `vector` | Build a ChromaDB index for hybrid keyword + vector search |
| `mcp` | Run the MCP server for Claude Desktop, Cursor, and other MCP clients |
| `jinja2` | Use full Jinja2 templates for prompt formatting |
| `ollama` | Use the built-in Ollama client via `llm-kb ask` |

For local development:

```bash
pip install -e ".[vector,mcp,jinja2,ollama]"
```

---

## 30-Second Demo

```bash
# Check the package
llm-kb stats

# Find relevant patterns
llm-kb search "FastAPI JWT authentication" --lang python --top 3

# Build a model-aware prompt
llm-kb prompt "write a FastAPI endpoint with JWT auth" --model qwen2.5-coder:32b

# Ask an LLM with retrieved knowledge injected
llm-kb ask "write a REST API with JWT auth" --lang python --provider ollama --llm-model qwen2.5-coder:7b

# Or pipe a prompt directly to your local model
llm-kb prompt "write a REST API with JWT auth" --lang python --model qwen2.5-coder:32b | ollama run qwen2.5-coder:7b
```

---

## What's Inside

### Language Coverage

| Language | Entries | Language | Entries |
|:---|---:|:---|---:|
| Java | 200 | Python | 116 |
| Multi | 77 | Go | 44 |
| Rust | 39 | C# | 31 |
| Kotlin | 24 | SQL | 22 |
| PHP | 18 | Bash | 17 |
| Swift | 17 | JavaScript | 6 |
| YAML | 6 | TypeScript | 4 |
| Docker | 3 | Shell | 2 |

### Entry Format

Each entry is a Markdown file with YAML frontmatter and a consistent body:

- `When to Use` — concrete scenarios where the pattern applies
- `Standard Pattern` — runnable code with imports and useful type hints
- `Common Mistakes` — at least 3 `WRONG` / `CORRECT` pairs
- `Gotchas` — at least 3 subtle edge cases
- `Related` — links to related entries for retrieval and navigation
- Metadata — `language`, `category`, `tags`, `retrieval_hint`, `version`, `last_verified`, and `confidence`

The knowledge base also includes anti-patterns for common failure modes in security, performance, API design, concurrency, logging, testing, Git workflows, and language-specific pitfalls.

---

## Works With Your Model

The prompt builder adapts retrieval count, entry detail, and prompt verbosity to model size.

| Profile | Model size | Entries | Format | Use when |
|:---|:---|:---:|:---|:---|
| **Small** | 7-14B | 3 | Full | The model needs maximum guidance |
| **Medium** | 14-32B | 5 | Condensed | The model needs key patterns and gotchas |
| **Large** | 30B+ | 8 | Reference | The model needs quick reminders and signatures |

If your model is not listed, pass `--model my-model:32b` or `--profile medium` and the CLI will infer the profile from the size hint.

See [Model Support](docs/model-support.md) for the full model list and context windows.

---

## MCP Integration

Use the knowledge base from Claude Desktop, Cursor, Continue, or any MCP-compatible client.

```json
{
  "mcpServers": {
    "llm-kb": {
      "command": "python",
      "args": ["-m", "llm_kb.mcp_server"],
      "cwd": "/path/to/llm-knowledge-base"
    }
  }
}
```

Available MCP tools:

- `search_knowledge(query, language?, top_k?)` — find relevant code patterns
- `build_code_prompt(query, language?, max_tokens?, model?)` — build a model-aware system prompt
- `list_languages()` — list covered languages
- `get_entry(entry_id)` — fetch one entry by ID
- `get_model_profile(model_name?, size_hint?)` — inspect profile settings
- `list_supported_models()` — list known model names and profiles

---

## Quick Reference

### CLI

```bash
# Search for patterns
llm-kb search "JWT auth" --lang python
llm-kb search "PostgreSQL partitioning" --top 5 --format json

# Build a prompt
llm-kb prompt "write a FastAPI endpoint with JWT auth" --model qwen2.5-coder:32b
llm-kb prompt "write a REST API" --profile medium --format-template openai-chat

# Ask an LLM with KB context
llm-kb ask "how do I stream a file in Python?" --provider ollama --llm-model qwen2.5-coder:7b

# Inspect the knowledge base
llm-kb stats
llm-kb scorecard
llm-kb profile --list
llm-kb gaps --skip-trends --skip-simulation

# Validate and benchmark
llm-kb validate
llm-kb benchmark

# Optional vector search
pip install -e ".[vector]"
llm-kb index
llm-kb search "Redis rate limiting" --use-vector
```

### Python API

```python
from llm_kb import retrieve, build_prompt, get_profile, get_stats

results = retrieve(
    "FastAPI JWT authentication",
    language="python",
    top_k=3,
)

prompt = build_prompt(
    "write a REST API with JWT auth",
    language="python",
    model="qwen2.5-coder:32b",
)

profile = get_profile(model="qwen2.5-coder:32b")
stats = get_stats()

print(results[0]["title"])
print(profile.name, profile.entry_mode)
print(stats["total_entries"], stats["quality_score"])
```

### IDE Integration

- **Cursor** — `.cursorrules` with search, prompt, and MCP setup
- **VS Code** — `.vscode/tasks.json` with search, prompt, validate, scorecard, and test tasks
- **Claude Desktop** — `docs/claude-desktop-config.json` with MCP server config

---

## Quality Scorecard

```bash
llm-kb scorecard --verbose
```

| Metric | Score |
|:---|:---:|
| Coverage | 100/100 |
| Depth | 100/100 |
| Cross-references | 99/100 |
| Freshness | 100/100 |
| Anti-pattern coverage | 100/100 |
| Retrieval test coverage | 80/100 |
| **Overall** | **96/100** |

Fast PR checks:

```bash
python -m llm_kb validate
python -m pytest -m "smoke or sanity" -q
```

Full regression for maintainers and releases:

```bash
python -m llm_kb validate
python scripts/quality_auditor.py
python -m pytest test_retrieval.py test_entries_quality.py test_retrieval_comprehensive.py test_e2e.py test_retrieval_edge_cases.py test_phase14_profiles.py test_quality_audit.py -v --tb=short
```

---

## How It Works

```
[User Request]
      │
      ▼
[Retrieve Relevant Entries]  ← keyword matching, query expansion, cross-reference boost
      │
      ▼
[Choose Model Profile]       ← small, medium, or large
      │
      ▼
[Condense for Context]       ← fit entries into the model's context budget
      │
      ▼
[Build Prompt]               ← raw text, OpenAI chat JSON, or Claude XML
      │
      ▼
[Generate or Pipe]           ← use llm-kb ask, your own LLM client, or a local model
```

Default retrieval is local, deterministic, and offline. Optional ChromaDB hybrid search is available through the `vector` extra.

---

## Documentation

- [Getting Started](docs/getting-started.md) — install, first search, first prompt, MCP setup
- [Model Support](docs/model-support.md) — model profiles and context windows
- [Integration Guide](docs/integration-guide.md) — Ollama, LM Studio, OpenAI-compatible APIs, and custom integrations
- [Adding Entries](docs/adding-entries.md) — contribution workflow and entry quality bar
- [Test Automation Strategy](docs/test-automation-strategy.md) — pytest markers, fast gate, full regression
- [PR Checklist](docs/checklists/pr.md) — entry and CI checklist before review
- [Contributing Guide](docs/contributing-guide.md) — contributor workflow and review process
- [Architecture](docs/architecture.md) — design notes and folder structure

---

## Contributing

New entries are welcome. Start with a gap report:

```bash
python scripts/gap_detector.py
```

Then copy a template, write the required sections, validate locally, run the fast PR gate, and open a pull request.

```bash
cp templates/python.md python/<category>/<topic>.md
llm-kb validate
python -m pytest -m "smoke or sanity" -q
```

See [Adding Entries](docs/adding-entries.md) and the [PR Checklist](docs/checklists/pr.md) before opening a PR.

---

## License

MIT — see [LICENSE](LICENSE).
