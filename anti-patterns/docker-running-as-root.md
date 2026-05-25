---
id: "anti-patterns-docker-running-as-root"
title: "Docker Anti-Pattern: Running Containers as Root"
language: "docker"
category: "anti-patterns"
tags: ["antipatterns", "docker", "security", "root", "container", "image"]
version: "n/a"
retrieval_hint: "Docker container running as root USER directive :latest tag no health check multi-stage build"
last_verified: "2026-05-24"
confidence: "high"
---

# Docker Anti-Pattern: Running Containers as Root

## When to Use
- Writing Dockerfiles for production applications
- Reviewing container security configurations
- Building CI/CD pipelines with container images
- Auditing existing container deployments

## Standard Pattern

```dockerfile
# WRONG: Running as root (default)
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
# Process runs as root — attacker gets full container access

# CORRECT: Create non-root user
FROM python:3.12-slim
RUN useradd --create-home appuser
WORKDIR /app
COPY --chown=appuser:appuser . .
RUN pip install --no-cache-dir -r requirements.txt
USER appuser
CMD ["python", "app.py"]
```

```dockerfile
# WRONG: Using :latest tag
FROM node:latest
# Unpredictable builds, no reproducibility, may pull breaking changes

# CORRECT: Pin specific version
FROM node:22.3.1-slim
# Reproducible builds, predictable behavior
```

```dockerfile
# WRONG: No .dockerignore, copying everything
COPY . .
# Copies .git, node_modules, .env, secrets, test data

# CORRECT: Use .dockerignore
# .git
# node_modules
# .env
# *.log
# tests/
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ ./src/
```

```dockerfile
# WRONG: Single-stage build with build tools in production
FROM python:3.12
COPY . .
RUN pip install -r requirements.txt
RUN apt-get update && apt-get install -y gcc build-essential
# 1.2GB image with compilers and source code

# CORRECT: Multi-stage build
FROM python:3.12-slim AS builder
RUN apt-get update && apt-get install -y gcc build-essential && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

FROM python:3.12-slim
COPY --from=builder /install /usr/local
COPY src/ ./src/
# 150MB image, no compilers
```

```dockerfile
# WRONG: COPY secrets into image
COPY .env /app/.env
COPY id_rsa /root/.ssh/id_rsa
# Secrets baked into image layers — anyone with image has them

# CORRECT: Use build secrets or runtime injection
# Docker BuildKit:
# --mount=type=secret,id=env_file,target=/app/.env
# Or pass at runtime:
# docker run --env-file .env myapp
```

```yaml
# WRONG: Docker Compose with no health check
services:
  api:
    build: .
    ports:
      - "8000:8000"

# CORRECT: Add health check
services:
  api:
    build: .
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

## Common Mistakes
Running containers as root is the most critical Docker security anti-pattern. If an attacker exploits a vulnerability in the application, they gain root access inside the container, which can be leveraged for container escapes on misconfigured hosts. Using `:latest` tags makes builds non-reproducible and can silently introduce breaking changes. Copying `.env` files or SSH keys into images exposes secrets in image layers that persist even if the file is later deleted. Single-stage builds include compilers and build tools in production images, increasing attack surface and image size.

## Gotchas
- `USER` directive must come AFTER all `RUN` commands that need root privileges (package installs, user creation)
- `COPY --chown` avoids needing a separate `RUN chown` layer
- `.dockerignore` must be in the build context root, same level as the Dockerfile
- Multi-stage builds can reference named stages: `COPY --from=builder /app /app`
- `HEALTHCHECK NONE` disables inherited health checks — don't accidentally use it
- `--security-opt no-new-privileges` prevents privilege escalation at runtime
- `--read-only` filesystem prevents writes — use tmpfs for writable paths
- `apt-get install --no-install-recommends` reduces image size and attack surface
- Secrets in `RUN` commands are also cached in layer metadata — use BuildKit secrets

## Related
- devops/docker/dockerfile-patterns.md
- devops/docker/compose.md
- security/web-security-basics.md
- anti-patterns/docker-antipatterns.md
