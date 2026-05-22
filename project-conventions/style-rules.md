---
id: "project-conventions-style-rules"
title: "Project Style Rules Template"
language: "multi"
category: "project-conventions"
subcategory: "style"
tags: ["conventions", "style", "linting", "formatting", "project"]
version: "n/a"
retrieval_hint: "project conventions style rules linting formatting"
last_verified: "2025-01-15"
confidence: "draft"
---

# Project Style Rules Template

## When to Use
- Defining project-specific coding standards
- Configuring linters and formatters
- Onboarding new team members
- Code review guidelines

## Standard Pattern

```markdown
# Project Style Rules

## Naming Conventions
- Files: `kebab-case.ts`
- Components: `PascalCase.tsx`
- Functions: `camelCase`
- Constants: `UPPER_SNAKE_CASE`
- Database tables: `snake_case`
- Database columns: `snake_case`

## Code Style
- Indentation: 2 spaces (JS/TS), 4 spaces (Python)
- Line length: 100 characters max
- Quotes: Single quotes (JS/TS), double quotes (Python)
- Semicolons: Required (JS/TS)
- Trailing commas: Always

## Import Order
1. External libraries
2. Internal modules
3. Local files
4. Types

## Error Handling
- Always handle errors explicitly
- Use custom error classes
- Log errors with context
- Never swallow errors silently

## Testing
- Minimum 80% coverage
- Test file naming: `*.test.ts` or `*_test.py`
- One assertion per test (preferred)
- Use fixtures for test data

## Git
- Branch naming: `feature/`, `fix/`, `chore/`
- Commit messages: Conventional Commits format
- PR description: Required with test plan
```

## Common Mistakes

- Defining rules that are too strict and ignored by the team
- Not configuring linters to enforce the rules
- Copying rules from other projects without adapting to your stack
- Having conflicting rules between different tools (ESLint vs Prettier)

## Gotchas
- Rules should be enforced by tooling, not just documentation
- Keep rules minimal — too many rules are hard to follow
- Update rules as the project evolves
- Document the "why" behind non-obvious rules

## Template

```markdown
# Project Style Rules

## Naming Conventions
- Files: `kebab-case.ts`
- Components: `PascalCase.tsx`
- Functions: `camelCase`
- Constants: `UPPER_SNAKE_CASE`
- Database tables: `snake_case`
- Database columns: `snake_case`

## Code Style
- Indentation: 2 spaces (JS/TS), 4 spaces (Python)
- Line length: 100 characters max
- Quotes: Single quotes (JS/TS), double quotes (Python)
- Semicolons: Required (JS/TS)
- Trailing commas: Always

## Import Order
1. External libraries
2. Internal modules
3. Local files
4. Types

## Error Handling
- Always handle errors explicitly
- Use custom error classes
- Log errors with context
- Never swallow errors silently

## Testing
- Minimum 80% coverage
- Test file naming: `*.test.ts` or `*_test.py`
- One assertion per test (preferred)
- Use fixtures for test data

## Git
- Branch naming: `feature/`, `fix/`, `chore/`
- Commit messages: Conventional Commits format
- PR description: Required with test plan
```

## How to Customize

1. Copy this template to your project
2. Modify rules to match your team's preferences
3. Configure linters (ESLint, Prettier, Ruff) to enforce rules
4. Add to project README or CONTRIBUTING.md

## Related
- project-conventions/architecture.md
