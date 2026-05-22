# LLM Codebase Knowledge Base

> Make your local model write code like a senior engineer — works with any model size.

---

## Works With Any Model Size

Different models need different amounts of help. The knowledge base automatically adapts:

| Model Size | Examples | Entries | Format | What's Included |
|:---|:---|:---:|:---|:---|
| **7-14B** | Qwen2.5-Coder 7B, CodeLlama 7B | 3 | Full | Everything: patterns, mistakes, gotchas, imports |
| **27-32B** | Qwen2.5-Coder 32B, Command-R, Mixtral | 5 | Condensed | Key patterns, gotchas, mistakes (no imports, no "when to use") |
| **70B+** | Llama 3.1 70B, Qwen 2.5 72B | 8 | Reference | Signatures only, gotchas, version quirks |

```bash
# Auto-detect from model name
llm-kb prompt "write a REST API" --model qwen2.5-coder:32b

# Or specify profile explicitly
llm-kb prompt "write a REST API" --profile medium

# See what a model gets
llm-kb profile --model qwen2.5-coder:32b
llm-kb profile --list  # Show all 38 known models
```

---

## What It Does

Small coding models (7-14B) are fast and free, but they hallucinate APIs, invent nonexistent methods, and get syntax wrong. Larger models (27B+) are smarter but still miss library-specific patterns. This knowledge base gives them a cheat sheet — 278 curated, validated code patterns they can look up before writing code.

**Result:** Models of any size write better code because they check reference first.

---

## Quick Start

### Install
```bash
# Clone the repository
git clone https://github.com/example/llm-knowledge-base.git
cd ForLLm

# Install the Python package inside your virtual environment
pip install -e .
```

### Command Line Interface (CLI)
```bash
# Search for knowledge
llm-kb search "how to hash a file in Python"

# Build a prompt for your LLM and pipe it directly to a local coder
llm-kb prompt "write a REST API with JWT auth" --lang python | ollama run qwen2.5-coder:7b
```

### Python API
```python
from llm_kb import retrieve, build_prompt

# Retrieve relevant entries (outputs details about correct code, common mistakes and gotchas)
results = retrieve("FastAPI JWT authentication")
print(f"Top Result: {results[0]['title']}")

# Build a prompt with knowledge injected (handles budgeting automatically)
prompt = build_prompt("write a REST API", language="python", max_tokens=8192)
```

---

## The Proof

We benchmarked code generation on 20 standard tasks with and without the knowledge base. Here are the average results:

| Metric | Without KB | With KB |
|:---|:---:|:---:|
| **Quality Score** | ~45% | **92%** |
| **Tasks Fully Correct** | 3/20 | **19/20** |

See full benchmark results in [docs/integration-guide.md](docs/integration-guide.md).

---

## What's Inside

276 entries across 10 languages, curated by frontier models and validated by automated scripts:

| Language/Category | Entries |
|:---|:---:|
| Python | 74 |
| Java | 39 |
| TypeScript | 35 |
| Go | 20 |
| Rust | 15 |
| C# | 11 |
| Bash / Shell | 16 |
| Database / DevOps / Others | 68 |
| **Total** | **278** |

---

## MCP Integration

Use with Claude Desktop, Cursor, or any Model Context Protocol compatible client:

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

Provides 4 highly helpful coding tools:
- `search_knowledge`: Search for relevant coding patterns
- `build_code_prompt`: Build structured system prompts with knowledge for code generation
- `list_languages`: List all covered coding languages
- `get_entry`: Retrieve a single specific knowledge entry by ID

---

## IDE Integration

Pre-configured for frictionless adoption:

- **Cursor**: `.cursorrules` with MCP server setup, quick reference search patterns, and recommended AI workflow
- **VS Code**: `.vscode/tasks.json` with 7 tasks (Search, Prompt building for small/medium/large models, Validate, Scorecard, Run All Tests)
- **Claude Desktop**: `docs/claude-desktop-config.json` with MCP server configuration

All IDE configs use the 6 MCP tools: `search_knowledge`, `build_code_prompt`, `list_languages`, `get_entry`, `get_model_profile`, `list_supported_models`

---

## How It Works

```
[User Request] ─► [Retrieve 3-5 Related Patterns] ─► [Merge with System Prompt Template] ─► [Generate Senior-Grade Code]
```

1. **Ask a coding question:** Describe the task as normal.
2. **Context retrieval:** We run local grep-similarity matching to fetch the 3-5 most relevant validated coding patterns.
3. **Prompt injection:** Context is budgeted for of the target LLM and formatted into a highly polished structure.
4. **Senior code synthesis:** The local model synthesizes pristine code using the exact standards in the cheat sheet.

---

## Quality Scorecard

Run it yourself to see the quality metrics:
```bash
llm-kb scorecard
```

Our current metrics show the extreme maturity of the codebase:

- **Coverage:** 100%
- **Depth:** 94%
- **Cross-references:** 94%
- **Freshness:** 99%
- **Anti-patterns:** 80%
- **Retrieval accuracy:** 87%
- **Overall:** 92/100

---

## Contributing

Ready to add a new pattern? Please read our guidelines in [CONTRIBUTING.md](CONTRIBUTING.md).

