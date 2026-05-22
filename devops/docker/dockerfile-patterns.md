---
id: "devops-docker-dockerfile-patterns"
title: "Dockerfile Best Practices"
language: "docker"
category: "devops"
subcategory: "container"
tags: ["docker", "dockerfile", "multi-stage", "slim", "security"]
version: "n/a"
retrieval_hint: "Dockerfile multi-stage slim image build security"
last_verified: "2026-05-22"
confidence: "high"
---

# Dockerfile Best Practices

## When to Use
- Building container images
- Multi-stage builds for smaller images
- Security hardening
- CI/CD pipelines

## Standard Pattern

```dockerfile
# Multi-stage build for Node.js
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

FROM node:20-alpine AS runtime
WORKDIR /app
RUN addgroup -g 1001 -S nodejs && adduser -S nextjs -u 1001
COPY --from=builder --chown=nextjs:nodejs /app/dist ./dist
COPY --from=builder --chown=nextjs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nextjs:nodejs /app/package.json ./
USER nextjs
EXPOSE 3000
CMD ["node", "dist/index.js"]

# Multi-stage build for Python
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=builder /install /usr/local
COPY . .
RUN useradd -m appuser
USER appuser
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Common Mistakes

```dockerfile
# WRONG: Running as root
FROM node:20
WORKDIR /app
COPY . .
CMD ["node", "index.js"]  # Runs as root!

# CORRECT: Create and use non-root user
FROM node:20-alpine
WORKDIR /app
RUN addgroup -g 1001 -S nodejs && adduser -S nextjs -u 1001
COPY --chown=nextjs:nodejs . .
USER nextjs
CMD ["node", "index.js"]

# WRONG: Not using .dockerignore
COPY . .  # Copies node_modules, .git, etc.

# CORRECT: Use .dockerignore
# .dockerignore:
# node_modules
# .git
# *.md
```

## Gotchas
- Use `-alpine` variants for smaller images
- Multi-stage builds reduce final image size
- Always create a non-root user for security
- Use `.dockerignore` to exclude unnecessary files
- `COPY --chown` sets file ownership
- `RUN` layers are cached — order matters
- Use `--no-cache` for pip/npm to reduce image size

## Related
- devops/docker/compose.md
- devops/ci-cd/github-actions.md
