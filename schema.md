# Knowledge Base Entry Schema

Every knowledge entry is a Markdown file with YAML frontmatter. One entry per file, one topic per entry.

---

## Frontmatter (YAML)

```yaml
---
id: "python-stdlib-hashlib-sha256"
title: "SHA-256 Hashing with hashlib"
language: "python"
category: "stdlib"
subcategory: "cryptography"
tags: ["hashlib", "sha256", "checksum", "integrity"]
version: "3.12+"
retrieval_hint: "SHA-256 hashing file checksum integrity verify"
last_verified: "2025-01-15"
confidence: "high"
---
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier: `{lang}-{category}-{topic}` |
| `title` | string | Human-readable title |
| `language` | string | Primary language (`python`, `java`, `typescript`, `multi`) |
| `category` | string | Domain: `stdlib`, `web`, `db`, `testing`, `data`, `patterns`, `crypto`, `devops` |
| `tags` | string[] | Searchable keywords (3-8 tags) |
| `retrieval_hint` | string | Keywords for semantic/keyword retrieval |
| `last_verified` | date | When code was last validated (`YYYY-MM-DD`) |
| `confidence` | enum | `high` (tested), `medium` (reviewed), `draft` (generated) |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `subcategory` | string | Further classification |
| `version` | string | Minimum language/library version |

---

## Entry Sections

Every entry MUST include these sections in order:

### 1. `# Title`
Matches the `title` frontmatter field.

### 2. `## When to Use`
Bullet list of scenarios where this pattern applies. Be specific.

### 3. `## Standard Pattern`
Complete, runnable code with:
- All necessary imports
- Type hints (Python/TS) or annotations (Java)
- Docstrings
- Error handling (no bare try/except)

### 4. `## Common Mistakes`
WRONG vs CORRECT pairs showing typical errors:

```markdown
## Common Mistakes

# WRONG: Description of mistake
bad_code_example()

# CORRECT: What to do instead
good_code_example()
```

### 5. `## Gotchas`
Non-obvious pitfalls, edge cases, and warnings as bullet points.

### 6. `## Related`
Links to related entries using relative paths:
```markdown
## Related
- python/web/requests/auth.md
- crypto/password-hashing.md
```

---

## Entry Template

```markdown
---
id: "{lang}-{category}-{topic}"
title: "{Descriptive Title}"
language: "{python|java|typescript|multi}"
category: "{stdlib|web|db|testing|data|patterns|crypto|devops}"
subcategory: "{optional-subcategory}"
tags: ["tag1", "tag2", "tag3"]
version: "{version}+"
retrieval_hint: "{keywords for search}"
last_verified: "2025-01-15"
confidence: "high"
---

# {Title}

## When to Use
- {Scenario 1}
- {Scenario 2}

## Standard Pattern

```{language}
{complete, runnable code}
```

## Common Mistakes

```{language}
# WRONG: {mistake description}
{bad code}

# CORRECT: {fix description}
{good code}
```

## Gotchas
- {Pitfall 1}
- {Pitfall 2}

## Related
- {path/to/related.md}
```

---

## ID Convention

Format: `{language}-{category}-{subcategory?}-{topic}`

Examples:
- `python-stdlib-hashlib-sha256`
- `python-web-fastapi-auth-jwt`
- `java-spring-security-jwt-auth`
- `typescript-web-nextjs-app-router`
- `crypto-sha256`
- `db-postgres-json-queries`

---

## Confidence Levels

| Level | Meaning | When to Use |
|-------|---------|-------------|
| `high` | Tested and verified | Code examples run correctly, patterns are battle-tested |
| `medium` | Reviewed but not tested | Code looks correct, patterns follow best practices |
| `draft` | Auto-generated | Needs human review before marking as high/medium |
