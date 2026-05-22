---
id: "docker-deep-dive"
title: "Docker Deep Dive and Best Practices"
language: "docker"
category: "devops"
tags: ["docker", "container", "multi-stage", "security", "health-check", "optimization"]
version: "n/a"
retrieval_hint: "Docker multi-stage build security health check resource limits best practices"
last_verified: "2026-05-22"
confidence: "high"
---

# Docker Deep Dive and Best Practices

## When to Use
- Containerizing applications for deployment
- Optimizing Docker images for size and security
- Setting up health checks and resource limits
- Building reproducible, production-ready containers

## Standard Pattern

```dockerfile
# === Multi-Stage Build (Node.js example) ===
# Stage 1: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production && \
    cp -R node_modules /prod_modules && \
    npm ci
COPY . .
RUN npm run build

# Stage 2: Production
FROM node:20-alpine AS production
WORKDIR /app

# Run as non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Copy only production artifacts
COPY --from=builder /prod_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package.json ./

# Security: non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

EXPOSE 3000

# Use exec form (PID 1 handles signals correctly)
CMD ["node", "dist/server.js"]
```

```dockerfile
# === Python Multi-Stage Build ===
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --target=/deps -r requirements.txt

FROM python:3.12-slim AS production
WORKDIR /app
COPY --from=builder /deps /usr/local/lib/python3.12/site-packages
COPY . .

RUN useradd --create-home appuser
USER appuser

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# === Docker Compose with Resource Limits ===
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/myapp
    depends_on:
      db:
        condition: service_healthy
    deploy:
      resources:
        limits:
          cpus: "2.0"
          memory: 512M
        reservations:
          cpus: "0.5"
          memory: 128M
      restart_policy:
        condition: on-failure
        max_attempts: 3
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3

  db:
    image: postgres:16-alpine
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U myapp"]
      interval: 10s
      timeout: 5s
      retries: 5

secrets:
  db_password:
    file: ./secrets/db_password.txt

volumes:
  pgdata:
```

```dockerfile
# === .dockerignore ===
node_modules
.git
.env
.env.local
*.md
tests
coverage
__pycache__
*.pyc
.venv
dist
build
.DS_Store
```

## Common Mistakes

```dockerfile
# WRONG: Running as root
FROM node:20
WORKDIR /app
COPY . .
CMD ["node", "server.js"]  # Runs as root — security risk

# CORRECT: Non-root user
FROM node:20
WORKDIR /app
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
COPY --chown=appuser:appgroup . .
USER appuser
CMD ["node", "server.js"]

# WRONG: COPY . . before installing dependencies (cache bust)
COPY . .                    # Any file change invalidates all layers
RUN npm ci                  # Re-downloads everything

# CORRECT: Copy dependency files first
COPY package*.json ./
RUN npm ci
COPY . .                    # Only this layer invalidated on code change

# WRONG: Using latest tag
FROM node:latest            # Non-reproducible — changes unpredictably

# CORRECT: Pin specific version
FROM node:20.11-alpine      # Reproducible

# WRONG: Shell form CMD (no signal handling)
CMD node server.js          # PID 1 is /bin/sh, not node — SIGTERM ignored

# CORRECT: Exec form CMD
CMD ["node", "server.js"]   # PID 1 is node — handles SIGTERM

# WRONG: Not ignoring .env and secrets
COPY . .                    # .env with API keys in image layer

# CORRECT: .dockerignore excludes secrets
# .dockerignore: .env .env.*

# WRONG: Single-stage build (includes dev dependencies in production)
FROM node:20
COPY . .
RUN npm ci                  # Includes devDependencies
CMD ["node", "server.js"]

# CORRECT: Multi-stage build
FROM node:20 AS builder
COPY . .
RUN npm ci
RUN npm run build

FROM node:20-slim
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
CMD ["node", "dist/server.js"]
```

## Gotchas
- Multi-stage builds dramatically reduce image size — build tools stay in the build stage
- `COPY --chown` sets file ownership — prevents permission issues with non-root users
- `HEALTHCHECK` is crucial for orchestrators (Docker Compose, Kubernetes) to know if the app is ready
- `CMD ["exec", "form"]` makes your process PID 1 — it receives SIGTERM for graceful shutdown
- `CMD shell form` wraps in `/bin/sh` — signals don't reach your process
- Layer order matters — put rarely-changing layers first for better caching
- `.dockerignore` prevents sending unnecessary files to the build context (faster builds)
- `alpine` images are ~5x smaller than `slim` — but may need extra packages for native deps
- `--no-cache-dir` for pip and `--only=production` for npm reduce image size
- Resource limits prevent containers from consuming all host resources

## Related
- devops/ci-cd/github-actions.md
- devops/kubernetes/basics.md
- security/web-security-basics.md
