# Contributing to the Knowledge Base

Thank you for helping build retrieval-ready code patterns for small LLMs!

---

## The Quality Bar

Every new or updated pattern must meet our rigorous standards. When reviewing Pull Requests, maintainers look for the following:

- **Mistakes Coverage:** Every entry must include at least **3+ WRONG/CORRECT pairs** highlighting common library misconceptions or semantic bugs.
- **Gotchas:** Every entry must provide at least **3+ Gotchas** (hidden costs, concurrency bugs, encoding differences, thread-safety, etc.).
- **Related Links:** Every entry must include at least **2+ Related links** linking to other `.md` files in the repository.
- **Runnable Code:** The standard pattern must contain full, idiomatic, runnable code examples including imports and type signatures/type annotations.

---

## How to Add an Entry

### Step 1: Copy a Template
Start from one of our starter templates:
- [templates/python.md](templates/python.md)
- [templates/java.md](templates/java.md)
- [templates/typescript.md](templates/typescript.md)

### Step 2: Choose a Unique Entry ID Schema
Format: `{language}-{category}-{subcategory?}-{topic}`

Examples:
- `python-stdlib-hashlib-sha256`
- `java-spring-security-jwt-auth`
- `typescript-web-nextjs-app-router`

### Step 3: Complete Frontmatter and All Sections
Fill out all header fields and the 4 required markdown sections:
- `## When to Use` — Concrete design scenarios where this pattern applies.
- `## Standard Pattern` — Idiomatic correct patterns with type hints and annotations.
- `## Common Mistakes` — Pairs of WRONG and CORRECT sections containing exact comment-level comparisons.
- `## Gotchas` — Subtle edge cases.
- `## Related` — Links to associated files.

### Step 4: Local Validation
Validate your newly added file against the database schema before committing:
```bash
llm-kb validate
```

---

## Running Validation and Tests

We enforce quality and retrieval precision through automated test suites:

```bash
# Validate frontmatter and mandatory sections
llm-kb validate

# Run quality regression tests (checks Mistakes, Gotchas, Related Links counts)
python -m pytest test_entries_quality.py -v

# Run retrieval query recall tests
python -m pytest test_retrieval_comprehensive.py -v
```

---

## CI / CD Pipeline

Our GitHub Actions pipeline runs on every Pull Request and branch merge:
1. **Linter / Schema Validation:** Runs `llm-kb validate` inside Python 3.10 and 3.14 environments.
2. **Quality Checks:** Runs `pytest test_entries_quality.py` to assert that every single entry meets mistakes coverages.
3. **Retrieval Regression Check:** Runs `pytest test_retrieval_comprehensive.py` to prevent any queries from losing their correct retrieval hits.

All pipeline jobs must pass green before a Pull Request can be merged.

---

## Proposing New Languages or Categories

Want to introduce a new language (e.g., Swift, Kotlin) or category (e.g., Web3)?
- Open a **proposals issue** on GitHub to discuss database-wide interest.
- If approved, update `VALID_LANGUAGES` or `VALID_CATEGORIES` in [llm_kb/schema.py](llm_kb/schema.py) and [schema.md](schema.md) so files can pass validation checks.

---

## PR Submission Checklist

Before opening your Pull Request, verify every item is ticked off:
- [ ] Entry added under the correct category folder structure.
- [ ] Frontmatter contains all required fields with `confidence: high` or `confidence: medium`.
- [ ] Entry contains at least **3+ WRONG/CORRECT pairs** in the Mistakes section.
- [ ] Entry contains at least **3+ Gotchas**.
- [ ] Entry contains at least **2+ Related links** matching existing md files.
- [ ] `llm-kb validate` command exits with code 0 on your updates.
- [ ] All tests pass successfully under `pytest`.

