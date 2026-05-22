---
id: "integration-guide"
title: "Knowledge Base Integration Guide"
language: "python"
category: "web"
subcategory: "documentation"
tags: ["integration", "ollama", "lm-studio", "openai", "cli", "prompt"]
version: "3.10+"
retrieval_hint: "integration guide ollama lm studio openai compatible CLI prompt builder"
last_verified: "2026-05-22"
confidence: "high"
---

# Integration Guide

How to wire the LLM Codebase Knowledge Base into your local LLM setup.

## When to Use
- You want to use the knowledge base with a local LLM (Ollama, LM Studio, vLLM)
- You need to set up the retrieval pipeline for code generation
- You want to understand context window budgeting for your model
- You're building a custom integration with the knowledge base

## Standard Pattern

```python
# Complete integration: retrieve + build prompt + generate
import sys
from pathlib import Path

sys.path.insert(0, str(Path("/mnt/apps/ForLLm")))
from retrieval import search
from prompt_builder import build_prompt, format_metadata

# 1. Build prompt with knowledge context
system_prompt, metadata = build_prompt(
    query="write a FastAPI endpoint with JWT auth",
    top_k=3,
    max_tokens=8192,
)

# 2. Send to your LLM (Ollama, LM Studio, etc.)
# 3. The model receives curated knowledge and generates correct code
```

## Prerequisites

```bash
pip install pyyaml requests
# For vector-based retrieval (optional):
pip install chromadb sentence-transformers
```

## 1. Ollama Integration

Complete working script: query -> retrieve -> build prompt -> call Ollama -> output code.

```python
#!/usr/bin/env python3
"""query_kb_ollama.py — Query the knowledge base and generate code with Ollama."""

import json
import sys
from pathlib import Path

import requests

# Add KB to path
KB_PATH = Path("/mnt/apps/ForLLm")
sys.path.insert(0, str(KB_PATH))

from retrieval import search
from prompt_builder import build_prompt, build_user_prompt, format_metadata


def query_ollama(
    prompt: str,
    model: str = "codellama:7b",
    base_url: str = "http://localhost:11434",
    temperature: float = 0.1,
    max_tokens: int = 2048,
) -> str:
    """Call Ollama API with the assembled prompt."""
    response = requests.post(
        f"{base_url}/api/generate",
        json={
            "model": model,
            "system": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["response"]


def main():
    query = sys.argv[1] if len(sys.argv) > 1 else "write a FastAPI endpoint with JWT auth"
    model = sys.argv[2] if len(sys.argv) > 2 else "codellama:7b"

    # Build prompt with knowledge context
    system_prompt, metadata = build_prompt(
        query=query,
        top_k=3,
        kb_path=KB_PATH,
        max_tokens=8192,  # codellama:7b context window
    )

    print(format_metadata(metadata))
    print(f"\nGenerating with {model}...\n")

    # Call Ollama
    output = query_ollama(
        prompt=system_prompt,
        model=model,
    )

    print("=" * 60)
    print("GENERATED CODE:")
    print("=" * 60)
    print(output)


if __name__ == "__main__":
    main()
```

**Usage:**
```bash
python query_kb_ollama.py "write a FastAPI endpoint with JWT auth" codellama:7b
python query_kb_ollama.py "React useEffect with cleanup" codellama:13b
python query_kb_ollama.py "Go HTTP server with middleware" deepseek-coder:6.7b
```

**Before/After comparison:**

Without knowledge base — the model hallucinates:
```python
# Typical hallucination: inventing a non-existent FastAPI method
@app.jwt_required()  # DOES NOT EXIST
def protected_route():
    return {"user": get_jwt_identity()}
```

With knowledge base — correct pattern:
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        return {"user_id": payload["sub"]}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

## 2. LM Studio Integration

LM Studio exposes an OpenAI-compatible API on `http://localhost:1234/v1`.

```python
#!/usr/bin/env python3
"""query_kb_lmstudio.py — Query KB and generate with LM Studio."""

import json
import sys
from pathlib import Path

import requests

KB_PATH = Path("/mnt/apps/ForLLm")
sys.path.insert(0, str(KB_PATH))

from prompt_builder import build_prompt, format_metadata


def query_lmstudio(
    system_prompt: str,
    user_prompt: str,
    model: str = "local-model",
    base_url: str = "http://localhost:1234/v1",
    temperature: float = 0.1,
    max_tokens: int = 2048,
) -> str:
    """Call LM Studio's OpenAI-compatible API."""
    response = requests.post(
        f"{base_url}/chat/completions",
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def main():
    query = sys.argv[1] if len(sys.argv) > 1 else "write a React useEffect with cleanup"

    system_prompt, metadata = build_prompt(
        query=query,
        top_k=3,
        kb_path=KB_PATH,
        max_tokens=8192,
    )

    print(format_metadata(metadata))
    print(f"\nGenerating with LM Studio...\n")

    output = query_lmstudio(
        system_prompt=system_prompt,
        user_prompt=query,
    )

    print("=" * 60)
    print("GENERATED CODE:")
    print("=" * 60)
    print(output)


if __name__ == "__main__":
    main()
```

**curl test:**
```bash
# First, retrieve knowledge
python -c "
import sys; sys.path.insert(0, '.')
from prompt_builder import build_prompt
prompt, _ = build_prompt('FastAPI JWT auth', max_tokens=8192)
print(prompt[:500])
"

# Then call LM Studio
curl http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "local-model",
    "messages": [
      {"role": "system", "content": "<your retrieved knowledge here>"},
      {"role": "user", "content": "write a FastAPI endpoint with JWT auth"}
    ]
  }'
```

## 3. OpenAI-Compatible API (Generic)

Works with any OpenAI-compatible endpoint: vLLM, text-generation-inference, LocalAI, etc.

```python
#!/usr/bin/env python3
"""query_kb_openai_compat.py — Generic OpenAI-compatible integration."""

import sys
from pathlib import Path

import requests

KB_PATH = Path("/mnt/apps/ForLLm")
sys.path.insert(0, str(KB_PATH))

from prompt_builder import build_prompt, format_metadata


def query_openai_compat(
    system_prompt: str,
    user_prompt: str,
    base_url: str = "http://localhost:8000/v1",
    api_key: str = "not-needed",
    model: str = "default",
    temperature: float = 0.1,
    max_tokens: int = 2048,
) -> str:
    """Call any OpenAI-compatible API."""
    headers = {"Content-Type": "application/json"}
    if api_key and api_key != "not-needed":
        headers["Authorization"] = f"Bearer {api_key}"

    response = requests.post(
        f"{base_url}/chat/completions",
        headers=headers,
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Query KB + OpenAI-compatible LLM")
    parser.add_argument("query", help="Your coding question")
    parser.add_argument("--base-url", default="http://localhost:8000/v1")
    parser.add_argument("--api-key", default="not-needed")
    parser.add_argument("--model", default="default")
    parser.add_argument("--max-context", type=int, default=8192)
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()

    system_prompt, metadata = build_prompt(
        query=args.query,
        top_k=args.top_k,
        kb_path=KB_PATH,
        max_tokens=args.max_context,
    )

    print(format_metadata(metadata))

    output = query_openai_compat(
        system_prompt=system_prompt,
        user_prompt=args.query,
        base_url=args.base_url,
        api_key=args.api_key,
        model=args.model,
    )

    print("\n" + output)
```

## 4. CLI Tool

```python
#!/usr/bin/env python3
"""generate.py — CLI tool: ask question -> retrieve -> generate -> output.

Usage:
    python generate.py "write a FastAPI endpoint with JWT auth" --model codellama:7b
    python generate.py "React useEffect cleanup" --model deepseek-coder:6.7b --top-k 5
    python generate.py "Go HTTP server" --dry-run  # show prompt only
"""

import argparse
import sys
from pathlib import Path

KB_PATH = Path(__file__).parent
sys.path.insert(0, str(KB_PATH))

from prompt_builder import build_prompt, format_metadata


def main():
    parser = argparse.ArgumentParser(description="Knowledge-augmented code generation")
    parser.add_argument("query", help="Your coding question")
    parser.add_argument("--model", default="codellama:7b", help="Ollama model name")
    parser.add_argument("--top-k", type=int, default=3, help="Entries to retrieve")
    parser.add_argument("--max-context", type=int, default=8192, help="Context window")
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--dry-run", action="store_true", help="Show prompt only")
    parser.add_argument("--backend", choices=["ollama", "lmstudio", "openai"],
                        default="ollama")
    parser.add_argument("--base-url", default=None, help="API base URL")
    args = parser.parse_args()

    system_prompt, metadata = build_prompt(
        query=args.query,
        top_k=args.top_k,
        kb_path=KB_PATH,
        max_tokens=args.max_context,
    )

    print(format_metadata(metadata))

    if args.dry_run:
        print("\n--- SYSTEM PROMPT ---")
        print(system_prompt)
        return

    import requests

    if args.backend == "ollama":
        url = args.base_url or "http://localhost:11434/api/generate"
        resp = requests.post(url, json={
            "model": args.model,
            "system": system_prompt,
            "stream": False,
            "options": {"temperature": args.temperature},
        }, timeout=120)
        output = resp.json()["response"]
    else:
        url = args.base_url or "http://localhost:1234/v1/chat/completions"
        resp = requests.post(url, json={
            "model": args.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": args.query},
            ],
            "temperature": args.temperature,
        }, timeout=120)
        output = resp.json()["choices"][0]["message"]["content"]

    print("\n" + "=" * 60)
    print(output)


if __name__ == "__main__":
    main()
```

**Usage:**
```bash
# Basic usage
python generate.py "write a FastAPI endpoint with JWT auth" --model codellama:7b

# Dry run — see what prompt would be sent
python generate.py "React useEffect cleanup" --dry-run

# More entries, larger context
python generate.py "set up SQLAlchemy with async sessions" --top-k 5 --max-context 16384

# Use LM Studio backend
python generate.py "Go HTTP server" --backend lmstudio --model local-model
```

## 5. IDE Integration Concept

### VS Code Extension

The knowledge base can be integrated into VS Code via a custom extension:

```typescript
// Conceptual VS Code extension integration
// The extension would:
// 1. Detect the current file's language
// 2. Read the user's question from a sidebar or command palette
// 3. Call the retrieval system
// 4. Build the prompt with context budgeting
// 5. Send to local LLM
// 6. Display result in a panel or inline

// Context window budgeting for IDE:
// - VS Code sends current file content as additional context
// - Budget = model_context - system_prompt - query - current_file - response_reserve
// - Knowledge entries fill the remaining budget
```

### Neovim Integration

```lua
-- Conceptual Neovim integration using a Lua plugin
-- The plugin would:
-- 1. Get the current buffer content and filetype
-- 2. Call the Python retrieval script via jobstart
-- 3. Build the prompt
-- 4. Send to local LLM API
-- 5. Insert the result at cursor position

-- Example: call the CLI tool from Neovim
vim.api.nvim_create_user_command("KBAugment", function()
    local query = vim.fn.input("Question: ")
    local filetype = vim.bo.filetype
    local cmd = string.format(
        "python /path/to/generate.py '%s' --model codellama:7b --dry-run",
        query
    )
    local result = vim.fn.system(cmd)
    -- Parse and use the prompt...
end, {})
```

## Context Window Budgeting

How many entries fit in a given context window? This varies significantly by model size:

| Model Context | Profile | Max Entries | Entry Format | Knowledge Tokens |
|--------------|---------|-------------|--------------|------------------|
| 4,096 (7B)   | small   | 3           | full         | ~2,500           |
| 8,192 (27B)  | medium  | 5           | condensed    | ~4,000           |
| 16,384 (70B) | large   | 8           | reference    | ~3,200           |
| 32,768       | large   | 8           | reference    | ~3,200           |
| 65,536       | large   | 8           | condensed    | ~6,400           |

Use the budget calculator for precise numbers:
```bash
python scripts/context_budget.py --query "your question" --model-context 8192
```

## Model-Specific Setup

### For 7-14B Models (Qwen2.5-Coder 7B, CodeLlama 7B, Phi-3 14B)

These small models need maximum hand-holding. They get:
- **3 full entries** with all sections (Standard Pattern, When to Use, Common Mistakes, Gotchas)
- **Exhaustive WRONG/CORRECT pairs** (because they WILL make those mistakes)
- **Every import statement** (because they forget imports)
- **Verbose code comments** explaining each step

```bash
# Default profile (small) — backwards compatible
llm-kb prompt "write a REST API with JWT auth" --lang python | ollama run qwen2.5-coder:7b

# Explicit small profile (same behavior)
llm-kb prompt "write a REST API with JWT auth" --profile small | ollama run qwen2.5-coder:7b
```

### For 27-32B Models (Qwen2.5-Coder-32B, Command-R, Mixtral)

These models know most standard APIs. They benefit from:
- Library-specific patterns (not general syntax)
- Version-sensitive API differences
- Integration examples (wiring multiple systems together)
- Gotchas and uncommon edge cases

They DON'T need:
- Import statements (they know them)
- "When to Use" explanations (they can judge)
- Verbose code comments

```bash
# With Ollama — 32B model
llm-kb prompt "write a FastAPI app with JWT auth" --model qwen2.5-coder:32b | \
  ollama run qwen2.5-coder:32b

# Or specify profile directly
llm-kb prompt "write a FastAPI app with JWT auth" --profile medium | \
  ollama run qwen2.5-coder:32b

# Check what profile a model gets
llm-kb profile --model qwen2.5-coder:32b
```

**What the 32B model receives:**
- 5 condensed entries (~800 tokens each, 5x more topics than 7B)
- Standard Pattern + Common Mistakes + Gotchas per entry
- "When to Use" removed (the model knows)
- Code trimmed: no blank lines, no explanatory comments
- System prompt tailored for 27B+ models

### For 70B+ Models (Llama 3.1 70B, Qwen 2.5 72B)

These models are very capable. They only need:
- Reference signatures (function names, parameter orders)
- Non-obvious gotchas
- Version-specific quirks

```bash
# Reference mode — 8 entries, ~400 tokens each
llm-kb prompt "write a REST API" --profile large | ollama run llama3.1:70b
```

### Comparing Profiles

```bash
# See what each profile looks like for the same task
llm-kb profile --model qwen2.5-coder:7b
llm-kb profile --model qwen2.5-coder:32b
llm-kb profile --model llama3.1:70b

# List all 20+ supported models
llm-kb profile --list
```

## Retrieval Methods

### Grep-based (default, no dependencies)
```python
from retrieval import search
results = search("FastAPI JWT auth", top_k=3)
```

### Hybrid (vector + keyword, requires chromadb)
```bash
# First, build the index
python embed_and_index.py

# Then search
python -c "
from hybrid_retrieval import search
results = search('FastAPI JWT auth', top_k=3)
for r in results:
    print(f'{r.id}: {r.title} (score: {r.total_score:.2f})')
"
```

## Tips

1. **Start with `--dry-run`** to see what context the model receives
2. **Use `top_k=3`** for focused responses, `top_k=5` for comprehensive ones
3. **Set `max_context`** to your model's actual context window
4. **Temperature 0.1** for code generation (deterministic), 0.7 for creative tasks
5. **Check the budget report** — if entries are truncated, consider a larger context model

## Common Mistakes

```python
# WRONG: Not setting max_tokens, causing context overflow
system_prompt, _ = build_prompt(query, top_k=10)
# The model's context window is 8192 but you're sending 15000+ tokens

# CORRECT: Set max_tokens to match your model's context window
system_prompt, metadata = build_prompt(query, top_k=3, max_tokens=8192)
print(format_metadata(metadata))  # Verify budget usage
```

```python
# WRONG: Using top_k=10 with a small context model
system_prompt, _ = build_prompt(query, top_k=10, max_tokens=4096)
# Only 1-2 entries will fit, rest are wasted retrieval effort

# CORRECT: Match top_k to your context budget
# For 4096 tokens: top_k=1-2
# For 8192 tokens: top_k=3-4
# For 16384 tokens: top_k=5-8
system_prompt, _ = build_prompt(query, top_k=3, max_tokens=8192)
```

## Gotchas
- The grep-based retrieval matches on keywords in titles, tags, and retrieval_hints — vague queries like "make my code better" won't match well
- Hybrid retrieval (vector + keyword) requires running `python embed_and_index.py` first to build the ChromaDB index
- Context window budgeting is an estimate (~4 chars/token) — actual tokenization varies by model and tokenizer
- When entries are condensed to fit the budget, only Standard Pattern and Gotchas are shown — Common Mistakes are dropped
- Language auto-detection works for Python, Java, TypeScript, Go, Rust, C#, and Bash — other languages need explicit `language=` parameter
- Anti-pattern entries for the detected language are automatically included when available
- The `--dry-run` flag is essential for debugging — always verify what the model receives before generating
