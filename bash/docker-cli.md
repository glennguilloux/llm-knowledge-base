---
id: "bash-docker-cli"
title: "Bash Docker CLI: Run, Compose, Health Checks, and Image Cleanup"
language: "bash"
category: "stdlib"
tags: ["bash", "docker", "docker-compose", "health-check", "image-cleanup", "volume", "network"]
version: "n/a"
retrieval_hint: "bash docker run patterns compose from CLI health checks image cleanup volume management network operations"
last_verified: "2026-05-24"
confidence: "high"
---

# Bash Docker CLI: Run, Compose, Health Checks, and Image Cleanup

## When to Use
- Managing Docker containers from shell scripts
- Running docker-compose from CLI
- Setting up health checks
- Cleaning up unused images and volumes
- Managing Docker networks

## Standard Pattern

```bash
#!/bin/bash
set -euo pipefail

# docker run patterns
# Basic run
docker run -d --name my-app -p 8080:80 nginx:latest
# -d: detached (background)
# --name: container name
# -p: port mapping (host:container)

# Run with environment variables
docker run -d --name my-app \
    -e DB_HOST=localhost \
    -e DB_PORT=5432 \
    -e API_KEY="$API_KEY" \
    my-app:latest

# Run with volume mount
docker run -d --name my-app \
    -v /host/data:/app/data \
    -v my-volume:/app/storage \
    my-app:latest

# Run with network
docker run -d --name my-app \
    --network my-network \
    my-app:latest

# Run with resource limits
docker run -d --name my-app \
    --memory=512m \
    --cpus=1.0 \
    my-app:latest

# Run with auto-restart
docker run -d --name my-app \
    --restart=unless-stopped \
    my-app:latest

# Run with health check
docker run -d --name my-app \
    --health-cmd="curl -f http://localhost:8080/health || exit 1" \
    --health-interval=30s \
    --health-retries=3 \
    --health-timeout=10s \
    my-app:latest

# docker-compose from CLI
# Start services
docker compose up -d
# -d: detached

# Start specific service
docker compose up -d web db

# View logs
docker compose logs -f web
# -f: follow (tail)

# Execute command in running container
docker compose exec web php artisan migrate

# Stop services
docker compose down

# Stop and remove volumes
docker compose down -v

# Rebuild and restart
docker compose up -d --build

# Scale a service
docker compose up -d --scale web=3

# Check service status
docker compose ps

# Health check status
docker inspect --format='{{.State.Health.Status}}' my-app

# Image cleanup
# Remove dangling images (untagged)
docker image prune -f

# Remove all unused images (not just dangling)
docker image prune -a -f

# Remove images older than 24 hours
docker image prune -a --force --filter "until=24h"

# Remove specific image
docker rmi my-app:old-tag

# Volume cleanup
# Remove unused volumes
docker volume prune -f

# Remove specific volume
docker volume rm my-volume

# List volumes
docker volume ls

# System cleanup (images, containers, volumes, networks)
docker system prune -a --volumes -f

# Network operations
# Create network
docker network create my-network

# List networks
docker network ls

# Inspect network
docker network inspect my-network

# Connect container to network
docker network connect my-network my-app

# Disconnect container from network
docker network disconnect my-network my-app

# Remove network
docker network rm my-network

# Container management
# Stop all running containers
docker stop $(docker ps -q)

# Remove all stopped containers
docker rm $(docker ps -aq)

# Remove all containers (force)
docker rm -f $(docker ps -aq)

# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# Inspect container
docker inspect my-app

# View container resource usage
docker stats my-app

# Copy files to/from container
docker cp my-file.txt my-app:/app/
docker cp my-app:/app/log.txt ./log.txt

# View container logs
docker logs my-app
docker logs -f --tail 100 my-app  # Last 100 lines, follow

# Wait for container to be healthy
wait_for_healthy() {
    local container="$1"
    local timeout="${2:-60}"
    
    echo "Waiting for $container to be healthy..."
    for i in $(seq 1 "$timeout"); do
        status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "starting")
        if [[ "$status" == "healthy" ]]; then
            echo "$container is healthy!"
            return 0
        fi
        sleep 1
    done
    echo "Timeout waiting for $container"
    return 1
}
```

## Common Mistakes

```bash
# WRONG: Not using -d for long-running containers
docker run my-app  # Blocks terminal!

# CORRECT: Use -d for background
docker run -d --name my-app my-app

# WRONG: Not setting restart policy
docker run -d my-app  # Container stays down if it crashes!

# CORRECT: Set restart policy
docker run -d --restart=unless-stopped my-app

# WRONG: Using docker-compose in scripts without -f for custom file
docker compose up -d  # Uses docker-compose.yml in current dir

# CORRECT: Specify compose file explicitly
docker compose -f /opt/myapp/docker-compose.yml up -d

# WRONG: Not checking if container is healthy before proceeding
docker compose up -d db
docker compose exec web php migrate  # DB might not be ready!

# CORRECT: Wait for health check
docker compose up -d db
wait_for_healthy db 60
docker compose exec web php migrate

# WRONG: Not cleaning up unused images (disk space leak)
# Over time, old images accumulate and waste disk space

# CORRECT: Regular cleanup
docker image prune -a -f --filter "until=168h"  # Keep last 7 days

# WRONG: Using docker system prune in production without caution
docker system prune -a --volumes -f
# This removes ALL unused data — including build cache!

# CORRECT: Be specific about what to clean
docker container prune -f
docker image prune -f
docker volume prune -f

# WRONG: Not quoting variables in docker run
docker run -e MY_VAR=$myvar my-app
# If $myvar contains spaces, it breaks!

# CORRECT: Quote variables
docker run -e "MY_VAR=$myvar" my-app
```

## Gotchas
- `docker compose` (space) is the modern V2 command. `docker-compose` (hyphen) is legacy V1.
- `--restart=unless-stopped` restarts containers automatically unless explicitly stopped.
- Health checks are defined in Dockerfile or docker-compose.yml, not just `docker run`.
- `docker system prune -a --volumes` is destructive. Test with `--dry-run` first.
- `docker stats` shows real-time resource usage (CPU, memory, network, disk I/O).
- `docker cp` works in both directions: host-to-container and container-to-host.
- `docker network create` enables DNS-based service discovery between containers.
- `docker compose exec` runs a command in a RUNNING container. Use `docker compose run` for new containers.
- `docker compose logs -f` follows logs from all services. Specify a service name to filter.
- Always use `set -euo pipefail` in Docker automation scripts.

## Related
- bash/network-operations.md
- bash/file-operations.md
- bash/git-automation.md
- bash/scripting-patterns.md
