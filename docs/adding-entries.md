# Adding Knowledge Entries

This guide walks you through contributing a new knowledge entry to the base.

## Why Contribute?

Every entry you add helps **every small model user** get better code. Your "Python asyncio patterns" entry might be the thing that stops someone's 7B model from writing broken concurrent code.

## Entry Anatomy

Every entry is a Markdown file with YAML frontmatter:

```markdown
---
id: python-stdlib-asyncio-basics
title: Python asyncio Basics
language: python
category: stdlib
tags: [asyncio, async, await, concurrency, coroutine]
retrieval_hint: how to use async await in Python asyncio coroutine
confidence: high
---

## When to Use

Use asyncio when you need concurrent I/O-bound operations without threads...

## Standard Pattern

\`\`\`python
import asyncio

async def fetch_data(url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

async def main():
    results = await asyncio.gather(
        fetch_data("https://api.example.com/1"),
        fetch_data("https://api.example.com/2"),
    )
    return results

if __name__ == "__main__":
    asyncio.run(main())
\`\`\`

## Common Mistakes

### WRONG: Forgetting await

\`\`\`python
# This returns a coroutine object, not the result
result = fetch_data("https://api.example.com")
\`\`\`

### CORRECT:

\`\`\`python
result = await fetch_data("https://api.example.com")
\`\`\`

### WRONG: Using asyncio.run() inside another async function

\`\`\`python
async def main():
    # Don't do this — asyncio.run() creates a new event loop
    result = asyncio.run(fetch_data("https://api.example.com"))
\`\`\`

### CORRECT:

\`\`\`python
async def main():
    result = await fetch_data("https://api.example.com")
\`\`\`

### WRONG: Blocking the event loop with synchronous I/O

\`\`\`python
async def fetch_data(url: str) -> dict:
    # requests.get() blocks the entire event loop
    response = requests.get(url)
    return response.json()
\`\`\`

### CORRECT:

\`\`\`python
async def fetch_data(url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
\`\`\`

## Gotchas

1. **Event loop per thread**: asyncio.run() creates a new event loop. Never call it inside an existing async function.
2. **Task vs coroutine**: `asyncio.create_task()` schedules concurrent execution. Just calling `coroutine()` creates an unawaited coroutine.
3. **Exception handling**: Unawaited task exceptions are raised when the task is garbage collected, not when they occur.

## Related

- [python-stdlib-concurrency-choices](python/stdlib/concurrency-choices.md)
- [python-patterns-retry-logic](python/patterns/retry-logic.md)
```

## Quality Bar

Every entry **must** meet these standards:

| Requirement | Minimum | Why |
|:---|:---:|:---|
| WRONG/CORRECT pairs | 3+ | Models learn from mistakes |
| Gotchas | 3+ | Subtle bugs are the hardest to debug |
| Related links | 2+ | Cross-referencing improves retrieval |
| Runnable code | Yes | Models copy patterns directly |
| Imports included | Yes | Missing imports = broken code |

## Step-by-Step

### 1. Choose a Topic

Run the gap detector to find uncovered topics:

```bash
python scripts/gap_detector.py
```

Or check the [gap report](scripts/gap_report.md) for ideas.

### 2. Copy a Template

```bash
# Python
cp templates/python.md python/<category>/<topic>.md

# Java
cp templates/java.md java/<category>/<topic>.md

# TypeScript
cp templates/typescript.md typescript/<category>/<topic>.md
```

### 3. Choose an Entry ID

Format: `{language}-{category}-{subcategory}-{topic}`

Examples:
- `python-stdlib-hashlib-sha256`
- `java-spring-security-jwt-auth`
- `typescript-web-nextjs-app-router`

### 4. Write the Entry

Fill in all sections:
- `## When to Use` — Concrete scenarios
- `## Standard Pattern` — Idiomatic, runnable code
- `## Common Mistakes` — 3+ WRONG/CORRECT pairs
- `## Gotchas` — 3+ subtle edge cases
- `## Related` — 2+ links to existing entries

### 5. Validate Locally

```bash
# Check frontmatter and sections
llm-kb validate

# Run quality tests
python -m pytest test_entries_quality.py -v

# Run retrieval tests
python -m pytest test_retrieval_comprehensive.py -v

# Full test suite
python -m pytest -v
```

### 6. Open a PR

Use the PR template. CI will run all checks automatically.

## Entry Ideas

High-priority gaps (as of v1.0.0):

- **Python**: `pathlib` patterns, `typing` generics, `functools` advanced
- **Java**: Jakarta EE patterns, Micronaut framework
- **TypeScript**: Deno runtime patterns, advanced generics
- **Go**: gRPC patterns, context propagation
- **Rust**: async/await with tokio, lifetime patterns
- **DevOps**: GitHub Actions patterns, Terraform modules

## Recognition

All contributors are listed in the README. Your name, your entry, every model gets better.
