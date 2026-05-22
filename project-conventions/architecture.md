---
id: "project-conventions-architecture"
title: "Architecture Decision Records Template"
language: "multi"
category: "project-conventions"
subcategory: "architecture"
tags: ["architecture", "adr", "decisions", "design", "documentation"]
version: "n/a"
retrieval_hint: "architecture decision record ADR design documentation"
last_verified: "2025-01-15"
confidence: "draft"
---

# Architecture Decision Records Template

## When to Use
- Documenting architectural decisions
- Onboarding new team members
- Tracking decision rationale
- Reviewing past choices

## Standard Pattern

```markdown
# ADR-{NUMBER}: {TITLE}

## Status
{Proposed | Accepted | Deprecated | Superseded}

## Context
What is the issue that we're seeing that is motivating this decision?

## Decision
What is the change that we're proposing and/or doing?

## Consequences
What becomes easier or more difficult to do because of this change?

## Alternatives Considered
- Option A: {description}
- Option B: {description}
- Option C: {description}

## Related
- ADR-{NUMBER}: {related decision}
```

## Common Mistakes

- Writing ADRs after the decision is already implemented
- Not including enough context for future readers
- Forgetting to update status when decisions are superseded
- Writing vague consequences that don't help future decision-making

## Gotchas
- ADRs should be immutable once accepted — create a new ADR to supersede
- Keep ADRs focused on one decision each
- Include the "why" not just the "what"
- Reference ADRs in code comments for traceability

## Template

```markdown
# ADR-{NUMBER}: {TITLE}

## Status
{Proposed | Accepted | Deprecated | Superseded}

## Context
What is the issue that we're seeing that is motivating this decision?

## Decision
What is the change that we're proposing and/or doing?

## Consequences
What becomes easier or more difficult to do because of this change?

## Alternatives Considered
- Option A: {description}
- Option B: {description}
- Option C: {description}

## Related
- ADR-{NUMBER}: {related decision}
```

## Example

```markdown
# ADR-001: Use FastAPI for Backend API

## Status
Accepted

## Context
We need a Python web framework for our REST API. Requirements:
- Async support for high concurrency
- Automatic API documentation
- Type safety with Pydantic
- Good performance

## Decision
We will use FastAPI as our web framework.

## Consequences
- Easier: Auto-generated OpenAPI docs, type validation
- Easier: Async support for database queries
- Harder: Smaller community than Django/Flask
- Harder: Fewer third-party packages

## Alternatives Considered
- Django REST Framework: Too heavyweight for our needs
- Flask: No native async, no auto-docs
- Starlette: Lower level, more boilerplate
```

## How to Use

1. Create `docs/adr/` directory in your project
2. Number ADRs sequentially: `001-first-decision.md`
3. Never delete ADRs — mark as Deprecated or Superseded
4. Reference ADRs in code comments and PRs

## Related
- project-conventions/style-rules.md
