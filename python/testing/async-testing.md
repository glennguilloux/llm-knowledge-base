---
id: "python-testing-async-testing"
title: "Testing Async Python Code"
language: "python"
category: "testing"
subcategory: "async"
tags: ["pytest", "async", "asyncio", "httpx", "testing", "mock"]
version: "3.10+"
retrieval_hint: "pytest async asyncio anyio httpx AsyncClient test async function"
last_verified: "2026-05-22"
confidence: "high"
---

# Testing Async Python Code

## When to Use
- Testing FastAPI/Starlette endpoints with async dependencies
- Testing async database operations (SQLAlchemy async sessions)
- Testing async HTTP clients, WebSocket connections, or event-driven code
- Any code using `async def` that needs test coverage

## Standard Pattern

```python
# --- pyproject.toml ---
# [tool.pytest.ini_options]
# asyncio_mode = "auto"  # All async tests run automatically

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch


# --- FastAPI test client ---
@pytest_asyncio.fixture
async def client():
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_list_users(client: AsyncClient):
    response = await client.get("/users")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    response = await client.post("/users", json={"name": "Alice", "email": "alice@test.com"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Alice"
    assert "id" in data


# --- Testing async functions directly ---
@pytest.mark.asyncio
async def test_fetch_data():
    result = await fetch_from_api("https://api.example.com/data")
    assert result["status"] == "ok"


# --- Mocking async functions ---
@pytest.mark.asyncio
async def test_with_mock():
    mock_fetch = AsyncMock(return_value={"status": "ok"})
    with patch("app.services.fetch_from_api", mock_fetch):
        result = await process_data("test")
        assert result["processed"] is True
        mock_fetch.assert_called_once()


# --- Async fixture with cleanup ---
@pytest_asyncio.fixture
async def db_session():
    from app.db import async_session
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.mark.asyncio
async def test_db_operation(db_session):
    user = User(name="Test")
    db_session.add(user)
    await db_session.flush()
    assert user.id is not None


# --- Testing async generators (SSE, streaming) ---
@pytest.mark.asyncio
async def test_streaming_response(client: AsyncClient):
    async with client.stream("GET", "/events") as response:
        events = []
        async for line in response.aiter_lines():
            if line.startswith("data:"):
                events.append(line.removeprefix("data:"))
    assert len(events) > 0


# --- Async context manager testing ---
@pytest.mark.asyncio
async def test_async_context_manager():
    async with MyAsyncResource() as resource:
        result = await resource.do_work()
    assert result is not None
```

## Common Mistakes

```python
# WRONG: Using sync test for async code
def test_async_function():
    result = await fetch_data()  # SyntaxError — can't await in sync function

# CORRECT: Mark as async test
@pytest.mark.asyncio
async def test_async_function():
    result = await fetch_data()

# WRONG: Using sync TestClient with async app
from fastapi.testclient import TestClient  # Sync client

def test_api():
    client = TestClient(app)  # Works but uses a thread pool (not truly async)
    response = client.get("/users")

# CORRECT: Use httpx AsyncClient for true async testing
@pytest.mark.asyncio
async def test_api():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/users")

# WRONG: Not awaiting mock assertions
mock_func = AsyncMock()
await mock_func("test")
mock_func.assert_called_once_with("test")  # May pass even if wrong — always await first

# CORRECT: Await the mock call, then assert
mock_func = AsyncMock()
await mock_func("test")
mock_func.assert_called_once_with("test")

# WRONG: Forgetting asyncio_mode in pyproject.toml
# Every test needs @pytest.mark.asyncio (verbose)

# CORRECT: Set auto mode
# pyproject.toml: asyncio_mode = "auto"
# Then just: async def test_something(): ...
```

## Gotchas
- `pytest-asyncio` is required (`pip install pytest-asyncio`) — not built into pytest
- `asyncio_mode = "auto"` in `pyproject.toml` removes the need for `@pytest.mark.asyncio`
- `AsyncClient` from `httpx` is preferred over `TestClient` from `starlette` for async tests
- `ASGITransport` wraps the ASGI app without starting a real server
- Async fixtures must use `@pytest_asyncio.fixture`, not `@pytest.fixture`
- Use `AsyncMock` from `unittest.mock` for mocking async functions (Python 3.8+)
- `anyio` pytest plugin (`pytest-anyio`) is an alternative to `pytest-asyncio` for framework-agnostic async
- Tests using `asyncio_mode = "auto"` don't need the `@pytest.mark.asyncio` decorator

## Related
- python/testing/pytest-fixtures.md
- python/web/fastapi/testing.md
- python/testing/mocking.md
