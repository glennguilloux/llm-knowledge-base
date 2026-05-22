---
id: "devops-ci-cd-github-actions"
title: "GitHub Actions Workflows"
language: "yaml"
category: "devops"
subcategory: "ci-cd"
tags: ["github", "actions", "ci-cd", "workflow", "pipeline"]
version: "n/a"
retrieval_hint: "GitHub Actions CI CD workflow pipeline build test deploy"
last_verified: "2026-05-22"
confidence: "high"
---

# GitHub Actions Workflows

## When to Use
- CI/CD pipelines
- Automated testing
- Build and deploy automation
- Scheduled tasks

## Standard Pattern

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [18, 20]

    steps:
      - uses: actions/checkout@v4

      - name: Use Node.js ${{ matrix.node-version }}
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'

      - run: npm ci
      - run: npm run lint
      - run: npm test
      - run: npm run build

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        run: echo "Deploying..."
```

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - uses: actions/checkout@v4

      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          generate_release_notes: true
```

## Common Mistakes

```yaml
# WRONG: Not caching dependencies
steps:
  - run: npm install  # Slow! Downloads every time.

# CORRECT: Use cache
steps:
  - uses: actions/setup-node@v4
    with:
      node-version: 20
      cache: 'npm'
  - run: npm ci

# WRONG: Running on every push to every branch
on: push  # Runs on all branches!

# CORRECT: Filter branches
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
```

## Gotchas
- `npm ci` is faster than `npm install` in CI
- Use `actions/cache` for custom caching
- `needs:` creates job dependencies
- `if:` for conditional execution
- Matrix strategy runs jobs in parallel
- Use `concurrency:` to cancel in-progress runs
- Secrets are available via `${{ secrets.SECRET_NAME }}`

## Related
- devops/docker/dockerfile-patterns.md
- devops/kubernetes/basics.md
