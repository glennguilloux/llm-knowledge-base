---
id: "patterns-git-workflows"
title: "Git Workflows and Conventions"
language: "multi"
category: "patterns"
subcategory: "workflow"
tags: ["git", "branching", "commit", "rebase", "merge", "conventional"]
version: ""
retrieval_hint: "Git branching rebase merge conventional commits workflow PR review"
last_verified: "2026-05-24"
confidence: "high"
---

# Git Workflows and Conventions

## When to Use
- Team collaboration with shared repositories
- Release management and versioning
- Code review workflows (PRs/MRs)
- Automated CI/CD triggered by branch events

## Standard Pattern

```bash
# --- Feature branch workflow ---
git checkout main
git pull origin main
git checkout -b feature/user-auth

# Work and commit
git add -A
git commit -m "feat: add JWT authentication middleware"

# Keep branch updated
git fetch origin
git rebase origin/main  # Rebase preferred over merge for linear history

# Push and create PR
git push -u origin feature/user-auth

# After PR approval, squash merge
git checkout main
git merge --squash feature/user-auth
git commit -m "feat: add JWT authentication (#123)"
git push origin main
git branch -d feature/user-auth
```

```yaml
# --- Conventional commits ---
# Format: <type>(<scope>): <description>
#
# Types:
#   feat:     New feature
#   fix:      Bug fix
#   refactor: Code change that neither fixes nor adds
#   docs:     Documentation only
#   test:     Adding tests
#   chore:    Build process, dependencies
#   perf:     Performance improvement
#   ci:       CI/CD changes
#
# Examples:
#   feat(auth): add JWT token refresh endpoint
#   fix(api): handle null response in user endpoint
#   refactor(db): extract query builder to separate module
#   docs(readme): update installation instructions
#   test(auth): add integration tests for login flow
```

```yaml
# --- Branch protection rules (GitHub) ---
# main branch:
#   - Require PR reviews (1-2 approvals)
#   - Require status checks (CI must pass)
#   - Require linear history (squash or rebase merge)
#   - No force push
#   - No deletion
```

## Common Mistakes

```text
# WRONG: Working directly on main
git checkout main
# Make changes
git commit -m "fix stuff"
git push  # No review, no CI check!

# CORRECT: Use feature branches
git checkout -b feature/my-change
# Make changes
git push -u origin feature/my-change
# Create PR, get review, CI passes

# WRONG: Giant commits
git add -A
git commit -m "implemented entire feature"  # 50 files changed

# CORRECT: Small, focused commits
git commit -m "feat: add user model"
git commit -m "feat: add user repository"
git commit -m "feat: add user API endpoints"
git commit -m "test: add user integration tests"

# WRONG: Merge commits creating messy history
git merge main  # Creates merge commit in feature branch

# CORRECT: Rebase for linear history
git rebase origin/main

# WRONG: Force pushing shared branches
git push --force origin main  # Destroys others' work!

# CORRECT: Only force push personal branches
git push --force-with-lease origin feature/my-change
```

## Gotchas
- Conventional commits enable automatic changelog generation and semantic versioning
- Squash merge keeps main branch history clean and linear
- Rebase rewrites history — only do it on personal branches, never shared ones
- `--force-with-lease` is safer than `--force` — it fails if remote has new commits
- Branch protection rules enforce review and CI before merge
- Use `git stash` to temporarily save work when switching branches
- Pre-commit hooks can enforce commit message format, linting, and tests
- Consider trunk-based development with feature flags for faster iteration

## Related
- patterns/feature-flags.md
- patterns/health-checks.md
- api-design/versioning.md
