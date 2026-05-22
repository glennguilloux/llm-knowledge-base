---
id: "python-infra-docker-sdk"
title: "Docker SDK for Python"
language: "python"
category: "devops"
subcategory: "docker"
tags: ["docker", "sdk", "container", "image", "api", "dockerfile"]
version: "3.10+"
retrieval_hint: "Docker SDK Python container image build run API client"
last_verified: "2026-05-22"
confidence: "high"
---

# Docker SDK for Python

## When to Use
- Managing Docker containers programmatically (CI/CD, testing, deployment)
- Building and pushing images from Python scripts
- Running integration tests in containers (databases, services)
- Automating Docker Compose-like workflows

## Standard Pattern

```python
import docker
from docker.models.containers import Container
from typing import Optional


# --- Client setup ---
client = docker.from_env()  # Uses DOCKER_HOST env or default socket


# --- List containers ---
def list_running() -> list[dict]:
    return [
        {"id": c.short_id, "name": c.name, "status": c.status}
        for c in client.containers.list()
    ]


# --- Run a container ---
def run_container(
    image: str,
    command: str | None = None,
    ports: dict[str, int] | None = None,
    environment: dict[str, str] | None = None,
    detach: bool = True,
) -> Container:
    container = client.containers.run(
        image=image,
        command=command,
        ports=ports,         # {"8080/tcp": 8080}
        environment=environment,  # {"KEY": "value"}
        detach=detach,       # Run in background
        remove=True,         # Auto-remove when stopped
    )
    return container


# --- Build an image ---
def build_image(path: str, tag: str) -> docker.models.images.Image:
    image, logs = client.images.build(path=path, tag=tag, rm=True)
    for log in logs:
        if "stream" in log:
            print(log["stream"].strip())
    return image


# --- Container lifecycle ---
container = run_container("nginx:alpine", ports={"80/tcp": 8080})
print(container.status)  # "running"
container.stop(timeout=10)
container.start()
container.restart(timeout=5)
container.remove(force=True)


# --- Execute command in running container ---
def exec_in_container(container: Container, command: str) -> tuple[int, str]:
    exit_code, output = container.exec_run(command)
    return exit_code, output.decode()


exit_code, output = exec_in_container(container, "nginx -v")


# --- Get container logs ---
def get_logs(container: Container, tail: int = 100) -> str:
    return container.logs(tail=tail, timestamps=True).decode()


# --- Wait for container to be ready ---
def wait_for_port(host: str, port: int, timeout: int = 30) -> bool:
    import socket
    import time
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    return False
```

## Common Mistakes

```python
# WRONG: Not removing containers (resource leak)
container = client.containers.run("nginx", detach=True)
# Container stays running forever

# CORRECT: Use remove=True or clean up explicitly
container = client.containers.run("nginx", detach=True, remove=True)
# Or: container.stop(); container.remove()

# WRONG: Building image without tag
image, _ = client.images.build(path=".")  # Gets <none>:<none> tag

# CORRECT: Always specify a tag
image, _ = client.images.build(path=".", tag="myapp:latest")

# WRONG: Not handling build errors
image, logs = client.images.build(path=".", tag="myapp:latest")
# If build fails, raises docker.errors.BuildError

# CORRECT: Wrap in try/except
try:
    image, logs = client.images.build(path=".", tag="myapp:latest")
except docker.errors.BuildError as e:
    print(f"Build failed: {e}")
    for log in e.build_log:
        if "stream" in log:
            print(log["stream"].strip())

# WRONG: Using host network without caution
container = client.containers.run("nginx", network_mode="host")  # Shares host network

# CORRECT: Use bridge networking with port mapping
container = client.containers.run("nginx", ports={"80/tcp": 8080})
```

## Gotchas
- `docker.from_env()` reads `DOCKER_HOST` env var — useful for remote Docker daemons
- `detach=True` returns immediately with a Container object; `detach=False` waits for completion
- `container.logs(follow=True)` streams logs — iterate with `for line in logs`
- Port mapping format: `{"container_port/tcp": host_port}` (protocol required)
- `client.images.build()` returns `(Image, generator_of_logs)` — consume logs to see output
- Use `container.exec_run()` for running commands inside a container (like `docker exec`)
- `docker.errors.ContainerError` is raised when a non-detached container exits with non-zero
- For testing, use `testcontainers-python` library for managed container lifecycle

## Related
- python/concurrency/celery-basics.md
- devops/docker-compose.md
- python/testing/pytest-fixtures.md
