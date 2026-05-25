---
id: "devops-docker-compose"
title: "Docker Compose: Deploy Multi-Container Application"
language: "yaml"
category: "devops"
subcategory: "container"
tags: ["docker", "compose", "services", "networks", "volumes", "deploy", "containers", "application"]
version: "n/a"
retrieval_hint: "Docker Compose services networks volumes multi-container deploy application containers"
last_verified: "2026-05-24"
confidence: "high"
---

# Docker Compose

## When to Use
- Multi-container applications
- Local development environments
- Service orchestration
- Environment configuration

## Standard Pattern

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/mydb
      - REDIS_URL=redis://redis:6379
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    volumes:
      - .:/app
      - /app/node_modules
    networks:
      - app-network

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: mydb
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d mydb"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres-data:

networks:
  app-network:
    driver: bridge
```

## Common Mistakes

```yaml
# WRONG: Using 'latest' tag
services:
  app:
    image: node:latest  # Unpredictable!

# CORRECT: Pin version
services:
  app:
    image: node:20-alpine

# WRONG: Not using healthcheck
services:
  db:
    image: postgres:16
  app:
    depends_on:
      - db  # May start before DB is ready!

# CORRECT: Use healthcheck
services:
  db:
    image: postgres:16
    healthcheck:
      test: ["CMD-SHELL", "pg_isready"]
      interval: 5s
      retries: 5
  app:
    depends_on:
      db:
        condition: service_healthy

# WRONG: depends_on with condition but no healthcheck on target
services:
  db:
    image: postgres:16
  app:
    depends_on:
      db:
        condition: service_healthy  # Error: no healthcheck defined for db!

# CORRECT: Define healthcheck on the target service
services:
  db:
    image: postgres:16
    healthcheck:
      test: ["CMD-SHELL", "pg_isready"]
      interval: 5s
      retries: 5
  app:
    depends_on:
      db:
        condition: service_healthy
```

## Gotchas
- `depends_on` only waits for container start, not readiness
- Use `healthcheck` + `condition: service_healthy` for proper ordering
- Named volumes persist data; bind mounts are for development
- `environment` can use `${VARIABLE}` syntax for env vars
- Use `docker compose up -d` for detached mode
- `docker compose down -v` removes volumes too
- Use `.env` file for environment variables

## Related
- devops/docker/dockerfile-patterns.md
- devops/ci-cd/github-actions.md
