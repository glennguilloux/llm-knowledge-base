# Getting Started

## Install

```bash
pip install llm-knowledge-base
```

That's it. No ML dependencies, no API keys, no configuration files.

## Verify It Works

```bash
# Check the installation
llm-kb --help

# See what's inside
llm-kb stats

# Run a search
llm-kb search "how to hash a file in Python"

# Validate all entries
llm-kb validate

# View quality scorecard
llm-kb scorecard
```

## Your First Prompt

```bash
# Build a prompt for a 7B model (full entries)
llm-kb prompt "write a FastAPI endpoint with JWT auth" --model qwen2.5-coder:7b

# Build a prompt for a 32B model (condensed entries)
llm-kb prompt "write a FastAPI endpoint with JWT auth" --model qwen2.5-coder:32b

# Pipe directly to Ollama
llm-kb prompt "write a REST API with JWT auth" --lang python | ollama run qwen2.5-coder:7b
```

## Python API

```python
from llm_kb import retrieve, build_prompt, get_stats

# Search for relevant patterns
results = retrieve("FastAPI JWT authentication", language="python")
for r in results:
    print(f"  {r['title']} ({r['language']}/{r['category']})")

# Build a complete prompt with knowledge injected
prompt = build_prompt(
    "write a REST API with JWT auth",
    language="python",
    model="qwen2.5-coder:32b"
)
print(prompt)  # Ready to send to your model

# Get knowledge base statistics
stats = get_stats()
print(f"{stats['total_entries']} entries across {len(stats['languages'])} languages")
print(f"Quality score: {stats['quality_score']}/100")
```

## MCP Setup (Claude Desktop / Cursor)

Add to your MCP configuration file:

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS, `%APPDATA%\Claude\claude_desktop_config.json` on Windows):

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

**Cursor** (`.cursorrules` in your project root — already included in this repo):

```
Search patterns: python -m llm_kb search "QUERY" --lang python --top 3
```

Restart your IDE. The `search_knowledge` and `build_code_prompt` tools are now available to your AI assistant.

## Next Steps

- [Model Support](model-support.md) — Full compatibility table for 38 models
- [Adding Entries](adding-entries.md) — Contribute new knowledge patterns
- [Integration Guide](../docs/integration-guide.md) — Ollama, LM Studio, OpenAI-compatible APIs
