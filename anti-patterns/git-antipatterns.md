---
id: "antipatterns-git"
title: "Git Anti-Patterns: Committing Secrets, Force Pushing Main, and Merge Hell"
language: "multi"
category: "anti-patterns"
tags: ["antipatterns", "git", "secrets", "force-push", "gitignore", "merge-commits", "commit-messages"]
version: "n/a"
retrieval_hint: "git antipatterns committing secrets huge binary files force pushing main not using gitignore properly merge commit hell not writing commit messages"
last_verified: "2026-05-24"
confidence: "high"
---

# Git Anti-Patterns: Committing Secrets, Force Pushing Main, and Merge Hell

## When to Use
- Reviewing Git practices
- Training LLMs to avoid Git mistakes
- Git workflow checklist
- Understanding Git best practices

## Standard Pattern

```bash
# WRONG: Committing secrets
git add .
git commit -m "Add config"
# Committed .env with API keys, database passwords!

# CORRECT: Use .gitignore for secrets
echo ".env" >> .gitignore
echo "*.pem" >> .gitignore
echo "secrets/" >> .gitignore
git add .gitignore
git commit -m "Add .gitignore for secrets"

# Use environment variables for secrets, never commit them

# WRONG: Committing huge binary files
git add training_data.csv  # 500MB file!
git commit -m "Add data"
# Repository becomes huge and slow!

# CORRECT: Use Git LFS for large files
git lfs install
git lfs track "*.csv"
git lfs track "*.zip"
git add .gitattributes
git add training_data.csv  # Stored in LFS, not in repo

# WRONG: Force pushing to main
git push --force origin main
# Overwrites everyone's work!

# CORRECT: Never force push to shared branches
# Use --force-with-lease as a safer alternative
git push --force-with-lease origin feature-branch
# Only force push to your own feature branches

# WRONG: Not using .gitignore properly
# Committing node_modules, __pycache__, .DS_Store, build artifacts!

# CORRECT: Comprehensive .gitignore
# Python: __pycache__/, *.pyc, .env, venv/
# Node: node_modules/, .env, dist/
# General: .DS_Store, *.log, .idea/, .vscode/

# WRONG: Merge commit hell (long-lived feature branches)
# Feature branch diverged 3 months ago, 200 conflicts!

# CORRECT: Keep branches short-lived, rebase frequently
git checkout feature-branch
git rebase main  # Rebase onto latest main daily
# Or use squash merge for clean history

# WRONG: Not writing commit messages
git commit -m "fix"
git commit -m "update"
git commit -m "WIP"

# CORRECT: Write meaningful commit messages
git commit -m "feat: add user authentication with JWT"
git commit -m "fix: resolve race condition in counter increment"
git commit -m "docs: update API documentation for /users endpoint"

# Conventional commits format:
# type(scope): description
# Types: feat, fix, chore, docs, style, refactor, test, build, ci

# WRONG: Committing directly to main
git checkout main
git add .
git commit -m "Add feature"
# No code review, no testing!

# CORRECT: Use feature branches and pull requests
git checkout -b feature/user-auth
# ... work ...
git push origin feature/user-auth
# Create pull request for code review

# WRONG: git add . without reviewing changes
git add .
git commit -m "Update everything"
# May commit unintended changes!

# CORRECT: Review changes before committing
git diff          # Review unstaged changes
git diff --staged # Review staged changes
git add -p        # Stage changes interactively (hunk by hunk)
```

## Common Mistakes
- Committing secrets — API keys, passwords visible in Git history forever
- Huge binary files — bloat repository, slow clones and pulls
- Force pushing to main — overwrites everyone's work, use feature branches
- No .gitignore — commits node_modules, build artifacts, .env files
- Long-lived feature branches — diverge from main, create merge conflicts
- No commit messages — "fix" and "update" provide no context
- Committing directly to main — no code review, no testing
- git add . without reviewing — may commit unintended changes

## Gotchas
- Secrets committed to Git are VERY hard to remove. Use `git-filter-repo` or BFG Repo Cleaner.
- Git LFS (Large File Storage) stores large files outside the repository.
- `--force-with-lease` is safer than `--force` — it fails if someone else pushed.
- Conventional commits format makes changelog generation automatic.
- Feature branches should be short-lived (days, not weeks).
- `git rebase -i` (interactive rebase) lets you clean up commit history before merging.
- `.gitignore` should be committed to the repository so all developers share it.
- Use pre-commit hooks to prevent committing secrets automatically.

## Related
- bash/git-automation.md
- anti-patterns/docker-antipatterns.md
- anti-patterns/configuration-antipatterns.md
- anti-patterns/logging-antipatterns.md
