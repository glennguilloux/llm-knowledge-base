---
id: "anti-patterns-git-bad-commit-messages"
title: "Git Anti-Pattern: Bad Commit Messages"
language: "multi"
category: "anti-patterns"
tags: ["antipatterns", "git", "commit-messages", "conventional-commits", "workflow"]
version: "n/a"
retrieval_hint: "bad commit messages fix stuff wip conventional commits committing secrets unrelated changes"
last_verified: "2026-05-24"
confidence: "high"
---

# Git Anti-Pattern: Bad Commit Messages

## When to Use
- Writing commit messages for any git repository
- Reviewing git history for debugging or auditing
- Onboarding developers to team git conventions
- Setting up commit linting hooks or CI checks

## Standard Pattern

```bash
# WRONG: Meaningless messages
git commit -m "fix stuff"
git commit -m "wip"
git commit -m "update"
git commit -m "changes"
git commit -m "asdf"
# 6 months later: what changed and why?

# CORRECT: Conventional commits with context
git commit -m "fix(auth): reject login after 5 failed attempts

Rate-limit authentication to prevent brute force attacks.
Resets counter after 15-minute window expires.

Closes #234"
```

```bash
# WRONG: Unrelated changes in one commit
git add src/auth/login.ts src/ui/Button.tsx docs/README.md
git commit -m "auth and UI updates"
# Impossible to revert one change without the other

# CORRECT: Atomic commits — one logical change per commit
git commit -m "fix(auth): add rate limiting to login endpoint"
git commit -m "style(ui): update Button component hover state"
git commit -m "docs: add setup instructions to README"
```

```bash
# WRONG: Committing secrets
git add .
git commit -m "add config"
# .env file with DATABASE_URL, API_KEY, AWS_SECRET committed

# CORRECT: Prevent secrets from being committed
echo ".env" >> .gitignore
echo "*.pem" >> .gitignore
echo "secrets/" >> .gitignore
git add .gitignore
git commit -m "chore: add .gitignore"
# Use git-secrets or pre-commit hooks to prevent accidental commits
```

```python
# WRONG: Committing everything with no review
git add -A
git commit -m "save progress"
# Includes debug code, temp files, commented-out blocks

# CORRECT: Stage selectively, review before commit
# git add -p  # Interactive staging — review each hunk
# git diff --cached  # Review staged changes
git commit -m "feat(api): add pagination to /users endpoint"
```

```bash
# WRONG: Verb in present tense (not imperative)
git commit -m "fixed the login bug"
git commit -m "adding new feature"
git commit -m "deleted old files"
# Inconsistent — sometimes past, sometimes present progressive

# CORRECT: Imperative mood (matches git's own messages)
git commit -m "fix(auth): correct password validation regex"
git commit -m "feat(users): add bulk import endpoint"
git commit -m "chore: remove deprecated API v1 routes"
```

```bash
# WRONG: No explanation of WHY (only WHAT)
git commit -m "change timeout from 30 to 120"
# Why? Is this a fix for production timeouts? Load testing result?

# CORRECT: Explain motivation in the body
git commit -m "fix(api): increase request timeout to 120s

Production requests to /reports/aggregate were timing out
at 30s due to large dataset processing. 120s covers p99
latency observed in monitoring.

Fixes #567"
```

## Common Mistakes
Bad commit messages are a long-term maintenance cost that compounds over time. When debugging a production issue, developers rely on `git log` and `git blame` to understand why code exists. Messages like "fix stuff" or "wip" provide zero context and force developers to read the actual diff to understand intent. Committing secrets (API keys, passwords, certificates) is a security incident that requires key rotation even if the commit is later amended, because the data persists in git history. Unrelated changes in a single commit make reverts risky and code review difficult.

## Gotchas
- `git commit --amend` rewrites history — never amend commits that have been pushed to shared branches
- `git add -p` lets you stage partial changes interactively — use it for clean atomic commits
- Conventional commit prefixes (`feat:`, `fix:`, `refactor:`, `chore:`, `docs:`) enable automated changelog generation
- `git-secrets` (AWS tool) or `pre-commit` hooks can block commits containing patterns like API keys
- Commit message subject line should be 50 characters or less; body wraps at 72 characters
- `git log --oneline` is only useful if messages are descriptive
- `git rebase -i` can clean up messy commit history before merging to main
- Signed commits (`git commit -S`) verify author identity but don't encrypt content

## Related
- anti-patterns/security-hardcoded-secrets.md
- devops/ci-cd/github-actions.md
- anti-patterns/git-antipatterns.md
- patterns/git-workflows.md
