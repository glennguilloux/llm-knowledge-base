---
id: "anti-patterns-ci-no-cache"
title: "CI Anti-Pattern: No Dependency Caching"
language: "multi"
category: "anti-patterns"
tags: ["antipatterns", "ci", "caching", "github-actions", "pipeline", "performance"]
version: "n/a"
retrieval_hint: "CI no dependency caching rebuilding from scratch pip npm maven gradle docker layers GitHub Actions"
last_verified: "2026-05-24"
confidence: "high"
---

# CI Anti-Pattern: No Dependency Caching

## When to Use
- Setting up CI/CD pipelines for any language
- Optimizing build times for frequent commits
- Reviewing GitHub Actions, GitLab CI, or Jenkins configurations
- Reducing cloud CI costs from long-running jobs

## Standard Pattern

```yaml
# WRONG: No caching — installs everything from scratch every run
# .github/workflows/test.yml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt  # 2-5 minutes every run
      - run: pytest

# CORRECT: Cache pip dependencies
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: "pip"  # Built-in caching
      - run: pip install -r requirements.txt  # Seconds on cache hit
      - run: pytest
```

```yaml
# WRONG: No npm caching
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "22"
      - run: npm ci  # Full install every time
      - run: npm test

# CORRECT: Cache node_modules
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "22"
          cache: "npm"  # Caches ~/.npm, not node_modules
      - run: npm ci
      - run: npm test
```

```yaml
# WRONG: No Maven/Gradle caching
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          distribution: "temurin"
          java-version: "21"
      - run: mvn clean test  # Downloads all deps every run

# CORRECT: Cache Maven repository
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          distribution: "temurin"
          java-version: "21"
          cache: "maven"  # Caches ~/.m2/repository
      - run: mvn clean test
```

```dockerfile
# WRONG: No Docker layer caching — COPY everything before install
FROM node:22-slim
WORKDIR /app
COPY . .
RUN npm ci
# Every code change invalidates npm ci cache

# CORRECT: Copy package files first, install, then copy code
FROM node:22-slim
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# npm ci cached unless package files change
```

```yaml
# WRONG: Generic cache key — never invalidates
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: pip-cache  # Same key forever, stale deps

# CORRECT: Hash-based cache key
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: pip-${{ runner.os }}-${{ hashFiles('requirements*.txt') }}
    restore-keys: |
      pip-${{ runner.os }}-
```

## Common Mistakes
Not caching dependencies in CI is one of the most impactful anti-patterns for developer productivity and CI costs. A typical Python project takes 2-5 minutes to install dependencies from scratch, while a cache hit takes seconds. For Node.js projects with large dependency trees, `npm ci` can take 3+ minutes without caching. The fix is straightforward — most CI platforms and setup actions have built-in caching support. The key mistake is also using static cache keys that never invalidate, leading to stale dependencies.

## Gotchas
- `actions/setup-python` cache requires `requirements.txt` or `pyproject.toml` in repo root
- `actions/setup-node` caches `~/.npm` (the download cache), NOT `node_modules` — `npm ci` still runs but is fast
- Cache keys should include a hash of lock files to invalidate on dependency changes
- `restore-keys` with prefix matching enables partial cache hits (faster than cold)
- Docker layer caching only helps if `COPY package*.json` comes before `COPY . .`
- GitHub Actions caches are scoped to branch then default branch — feature branches inherit main's cache
- Monorepos need per-package cache keys to avoid cache pollution across services
- CI cache storage has limits (10 GB per repo on GitHub Actions) — evict old entries

## Related
- devops/ci-cd/github-actions.md
- devops/docker/dockerfile-patterns.md
- performance/caching-strategies.md
