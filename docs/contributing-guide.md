# Contributing Guide

Thank you for helping build retrieval-ready code patterns for small LLMs! Every entry you add makes models write better code for everyone.

## Why Contribute?

Small coding models (7-14B) hallucinate APIs, invent nonexistent methods, and get syntax wrong. Your contributions directly fix this. When you add a "Python asyncio patterns" entry, every developer using a 7B model with this knowledge base gets better asyncio code.

**Your entry helps every small model user.**

## The Quality Bar

Every entry must meet these standards:

| Requirement | Minimum | Why It Matters |
|:---|:---:|:---|
| WRONG/CORRECT pairs | 3+ | Models learn from seeing mistakes |
| Gotchas | 3+ | Subtle bugs are the hardest to debug |
| Related links | 2+ | Cross-referencing improves retrieval |
| Runnable code | Required | Models copy patterns directly |
| Imports included | Required | Missing imports = broken code |

### Before/After Example

**Weak entry** (doesn't meet the bar):
```markdown
## Common Mistakes
- Don't forget to close files
```

**Strong entry** (meets the bar):
```markdown
## Common Mistakes

### WRONG: Not closing files

```python
f = open("data.txt")
data = f.read()
# File never closed — resource leak
```

### CORRECT: Use context manager

```python
with open("data.txt") as f:
    data = f.read()
# File automatically closed
```

### WRONG: Using read() for large files

```python
# Loads entire file into memory
data = open("huge.txt").read()
```

### CORRECT: Stream line by line

```python
with open("huge.txt") as f:
    for line in f:
        process(line)
```

### WRONG: Not specifying encoding

```python
# Uses system default encoding — breaks on different machines
f = open("data.txt")
```

### CORRECT: Always specify encoding

```python
f = open("data.txt", encoding="utf-8")
```
```

## How to Add an Entry

### Step 1: Find a Gap

```bash
# See what's missing
python scripts/gap_detector.py
cat scripts/gap_report.md
```

### Step 2: Copy a Template

```bash
cp templates/python.md python/<category>/<topic>.md
```

### Step 3: Choose an Entry ID

Format: `{language}-{category}-{subcategory}-{topic}`

Examples:
- `python-stdlib-hashlib-sha256`
- `java-spring-security-jwt-auth`
- `go-concurrency-worker-pool`

### Step 4: Write the Entry

Required sections:
1. **When to Use** — Concrete scenarios where this pattern applies
2. **Standard Pattern** — Idiomatic, runnable code with imports and type annotations
3. **Common Mistakes** — 3+ WRONG/CORRECT pairs with exact code comparisons
4. **Gotchas** — 3+ subtle edge cases (concurrency, encoding, thread-safety, version quirks)
5. **Related** — 2+ links to existing `.md` files

### Step 5: Validate Locally

```bash
# Check frontmatter and sections
llm-kb validate

# Run quality tests
python -m pytest test_entries_quality.py -v

# Full test suite
python -m pytest -v
```

### Step 6: Open a PR

Use the PR template. CI runs all checks automatically.

## The Review Process

### Automated Checks (CI)

1. **Schema Validation** — `llm-kb validate` checks frontmatter and required sections
2. **Quality Checks** — `pytest test_entries_quality.py` verifies mistake/gotcha/link counts
3. **Retrieval Regression** — `pytest test_retrieval_comprehensive.py` ensures queries still work
4. **Cross-platform** — Tests run on Ubuntu, macOS, and Windows with Python 3.10-3.13

### Human Review

Maintainers check:
- Accuracy of patterns and code examples
- Quality of WRONG/CORRECT pairs (are they realistic mistakes?)
- Gotcha depth (are they genuinely subtle?)
- Cross-reference quality (do related links make sense?)

### Merge

Once CI passes and a maintainer approves, your entry is merged. It's immediately available to all users.

## Recognition

All contributors are listed in the README. Your name, your entry, every model gets better.

## Proposing New Languages or Categories

Want to add Swift, Kotlin, Web3, or another category?

1. Open a proposal issue describing the language/category
2. Include 3-5 example entries you'd add
3. If approved, update `VALID_LANGUAGES` or `VALID_CATEGORIES` in `llm_kb/schema.py`

## Code of Conduct

Be respectful. We're all here to make models write better code.
