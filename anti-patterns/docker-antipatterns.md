---
id: "antipatterns-docker"
title: "Docker Anti-Patterns: Running as Root, Huge Images, and Secrets in Env Vars"
language: "multi"
category: "anti-patterns"
tags: ["antipatterns", "docker", "root", "image-size", "dockerignore", "latest-tag", "health-check", "secrets"]
version: "n/a"
retrieval_hint: "docker antipatterns running as root huge images no dockerignore latest tag secrets in env vars no health check"
last_verified: "2026-05-24"
confidence: "high"
---

# Docker Anti-Patterns: Running as Root, Huge Images, and Secrets in Env Vars

## When to Use
- Writing Dockerfiles
- Reviewing Docker configurations
- Training LLMs to write better Dockerfiles
- Docker security and optimization checklist

## Standard Pattern

```dockerfile
# WRONG: Running as root
FROM ubuntu:latest
COPY . /app
CMD ["python", "app.py"]
# Container runs as root — security risk!

# CORRECT: Create and use non-root user
FROM python:3.12-slim
RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app
COPY --chown=appuser:appuser . .
USER appuser
CMD ["python", "app.py"]

# WRONG: Huge base image with build tools in production
FROM ubuntu:latest
RUN apt-get update && apt-get install -y python3 python3-pip gcc make
COPY . /app
RUN pip install -r requirements.txt
# Image size: 500MB+

# CORRECT: Use slim base image, multi-stage build
FROM python:3.12-slim as builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim
COPY --from=builder /install /usr/local
COPY . /app
WORKDIR /app
CMD ["python", "app.py"]
# Image size: ~150MB

# WRONG: No .dockerignore (copies node_modules, .git, etc.)
# .dockerignore missing!
# Build context: 500MB

# CORRECT: Use .dockerignore
# .dockerignore:
# .git/
# node_modules/
# __pycache__/
# .env
# *.log
# .vscode/
# tests/
# Build context: 5MB

# WRONG: Using latest tag
FROM node:latest
# "latest" is not reproducible! Different builds get different images.

# CORRECT: Pin to specific version
FROM node:20.11-slim
# Reproducible builds

# WRONG: Secrets in environment variables
ENV DATABASE_PASSWORD=supersecret
ENV API_KEY=abc123
# Secrets visible in `docker inspect`, image history, logs!

# CORRECT: Use Docker secrets or mount at runtime
# docker run -e DB_PASSWORD_FILE=/run/secrets/db_password ...
# Or use Docker Compose secrets:
# secrets:
#   db_password:
#     file: ./secrets/db_password.txt

# WRONG: No health check
# Container is "running" but the app is stuck!

# CORRECT: Add health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# WRONG: Putting secrets in docker-compose.yml
# environment:
#   DB_PASSWORD: "supersecret"  # Committed to Git!

# CORRECT: Use env_file or secrets
# env_file:
#   - .env  # In .gitignore!
# Or:
# secrets:
#   - db_password

# WRONG: Running multiple processes in one container
# web server + database + cache in one container!

# CORRECT: One process per container
# Use docker-compose to orchestrate multiple containers

# WRONG: Not using COPY --chown
COPY . /app
# Files owned by root!

# CORRECT: Set ownership
COPY --chown=appuser:appuser . /app
```

## Common Mistakes
- Running as root — container escape gives root access to host, use non-root user
- Huge images — build tools in production increase attack surface and slow deployments
- No .dockerignore — huge build context, may leak secrets, slower builds
- Using latest tag — non-reproducible builds, different images at different times
- Secrets in environment variables — visible in docker inspect, image history, logs
- No health checks — can't detect stuck or unhealthy containers
- Multiple processes per container — violates single-responsibility principle

## Gotchas
- Running as root in a container is a security risk. Use `USER` directive.
- Multi-stage builds reduce image size by 60-80%.
- `.dockerignore` reduces build context size and prevents leaking secrets.
- Pin base image versions for reproducible builds.
- Docker secrets or mounted files are safer than environment variables for secrets.
- Health checks enable automatic restart of unhealthy containers.
- One process per container. Use docker-compose for multi-container apps.
- `COPY --chown` sets file ownership during copy.
- Image layers are cached. Order Dockerfile commands from least to most frequently changing.
- Use `dive` tool to analyze Docker image layers and size.

## Related
- bash/docker-cli.md
- anti-patterns/git-antipatterns.md
- anti-patterns/configuration-antipatterns.md
- anti-patterns/error-handling-antipatterns.md
