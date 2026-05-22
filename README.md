# LLM Knowledge Base

> **Make your 7B model write code like a senior engineer.**
> 275 curated patterns. 2,804 tests. 92/100 quality score. Zero ML dependencies.

![Validate](https://github.com/glennguilloux/llm-knowledge-base/actions/workflows/validate.yml/badge.svg)
![Release](https://github.com/glennguilloux/llm-knowledge-base/actions/workflows/release.yml/badge.svg)
![PyPI](https://img.shields.io/pypi/v/llm-knowledge-base)
![Python](https://img.shields.io/pypi/pyversions/llm-knowledge-base)
![License](https://img.shields.io/badge/license-MIT-blue)

---

## The Problem

Small coding models (7-14B) are fast and free, but they **hallucinate APIs**, invent nonexistent methods, and get syntax wrong. Larger models (27B+) are smarter but still miss library-specific patterns.

**The fix:** Give them a cheat sheet. Before the model writes code, we inject 3-5 relevant, validated patterns directly into the prompt. The model writes better code because it checks reference first.

**The proof:**

| Metric | Without KB | With KB |
|:---|:---:|:---:|
| Quality Score | ~45% | **92%** |
| Tasks Fully Correct | 3/20 | **19/20** |
| Hallucinated APIs | Frequent | **Rare** |

---

## 30-Second Demo

```bash
pip install llm-knowledge-base

# Search for patterns
llm-kb search "FastAPI JWT authentication"

# Build a prompt for your model (auto-detects model size)
llm-kb prompt "write a FastAPI endpoint with JWT auth" --model qwen2.5-coder:32b

# Pipe directly to your local model
llm-kb prompt "write a REST API with JWT auth" --lang python | ollama run qwen2.5-coder:7b
```

That's it. One install, immediate improvement.

---

## What's Inside

275 validated knowledge entries across 13 languages and categories:

| Language | Entries | Language | Entries |
|:---|:---:|:---|:---:|
| Python | 74 | Go | 20 |
| Java | 39 | Rust | 15 |
| TypeScript | 35 | SQL | 11 |
| C# | 11 | Bash/Shell | 5 |
| Crypto | 5 | DevOps/Other | 9 |

Each entry contains:
- **Standard Pattern** — Idiomatic, runnable code with imports and type annotations
- **Common Mistakes** — 3+ WRONG/CORRECT pairs showing exactly what goes wrong
- **Gotchas** — 3+ subtle edge cases (concurrency, encoding, thread-safety, version quirks)
- **Related Links** — Cross-references to related patterns

---

## Works With Your Model

The knowledge base automatically adapts to model size. 38 models pre-mapped, auto-detect from name:

| Profile | Models | Entries | Format | Context |
|:---|:---|:---:|:---|:---:|
| **Small** (7-14B) | Qwen2.5-Coder 7B, CodeLlama 7B, Phi-3, DeepSeek-Coder 6.7B | 3 | Full | Everything: patterns, mistakes, gotchas, imports |
| **Medium** (14-32B) | Qwen2.5-Coder 32B, Command-R, Mixtral, Codestral 22B | 5 | Condensed | Key patterns, gotchas, mistakes |
| **Large** (70B+) | Llama 3.1 70B, Qwen 2.5 72B, DeepSeek-Coder-V2 236B | 8 | Reference | Signatures, gotchas, version quirks |

```bash
# Auto-detect from model name
llm-kb prompt "write a REST API" --model qwen2.5-coder:32b

# Or specify profile explicitly
llm-kb prompt "write a REST API" --profile medium

# See all 38 known models
llm-kb profile --list
```

---

## MCP Integration

Use with Claude Desktop, Cursor, or any MCP-compatible client. Add to your config:

```json
{
  "mcpServers": {
    "llm-kb": {
      "command": "python",
      "args": ["-m", "llm_kb.mcp_server"]
    }
  }
}
```

Four tools available to your AI assistant:
- `search_knowledge(query, language?, top_k?)` — Find relevant code patterns
- `build_code_prompt(query, language?, model?)` — Build a system prompt with knowledge injected
- `list_languages()` — List all covered languages
- `get_entry(entry_id)` — Get a specific entry by ID

---

## Quick Reference

### CLI

```bash
# Search
llm-kb search "how to hash a file in Python"
llm-kb search "JWT auth" --lang python

# Build prompt (pipe to any model)
llm-kb prompt "write a REST API" --lang python --model qwen2.5-coder:32b
llm-kb prompt "write a REST API" --lang python | ollama run qwen2.5-coder:7b

# Validate all entries
llm-kb validate

# Quality scorecard
llm-kb scorecard

# Model profiles
llm-kb profile --model qwen2.5-coder:32b
llm-kb profile --list

# Statistics
llm-kb stats
```

### Python API

```python
from llm_kb import retrieve, build_prompt, get_stats

# Search for entries
results = retrieve("FastAPI JWT authentication", language="python", top_k=3)
print(results[0]["title"])  # "JWT Authentication with FastAPI"

# Build a prompt with knowledge injected
prompt = build_prompt(
    "write a REST API with JWT auth",
    language="python",
    model="qwen2.5-coder:32b"
)

# Get stats
stats = get_stats()
print(f"{stats['total_entries']} entries, quality: {stats['quality_score']}/100")
```

### IDE Integration

Pre-configured for zero-friction adoption:
- **Cursor** — `.cursorrules` with MCP setup and search patterns
- **VS Code** — `.vscode/tasks.json` with 7 tasks (search, prompt, validate, scorecard, test)
- **Claude Desktop** — `docs/claude-desktop-config.json` with MCP server config

---

## Quality Scorecard

```bash
$ llm-kb scorecard
```

| Metric | Score |
|:---|:---:|
| Coverage | 100/100 |
| Depth | 93/100 |
| Cross-references | 93/100 |
| Freshness | 99/100 |
| Anti-pattern coverage | 80/100 |
| Retrieval test coverage | 87/100 |
| **Overall** | **92/100** |

---

## How It Works

```
[User Request]
      │
      ▼
[Retrieve 3-5 Related Patterns]  ←  keyword + tag matching, no ML required
      │
      ▼
[Condense for Model Size]        ←  small=full, medium=condensed, large=reference
      │
      ▼
[Inject into System Prompt]      ←  budget-aware, fits context window
      │
      ▼
[Model Writes Better Code]       ←  with exact patterns, gotchas, and mistakes
```

No vector database. No embeddings. No API calls. Pure grep + smart ranking. Works offline.

---

## Contributing

We welcome new entries! See [CONTRIBUTING.md](CONTRIBUTING.md) for the quality bar and submission checklist.

**Entry ideas:** Run `python scripts/gap_detector.py` to find coverage gaps.

**Quick start:**
```bash
# 1. Copy a template
cp templates/python.md python/stdlib/your-topic.md

# 2. Fill in the pattern, mistakes, gotchas, and related links

# 3. Validate
llm-kb validate

# 4. Run tests
python -m pytest test_entries_quality.py -v

# 5. Open a PR
```

---

## License

MIT — see [LICENSE](LICENSE).
