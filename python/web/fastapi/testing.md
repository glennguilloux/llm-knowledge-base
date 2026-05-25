---
id: "python-web-fastapi-testing"
title: "Testing FastAPI with TestClient"
language: "python"
category: "web"
subcategory: "testing"
tags: ["fastapi", "testing", "testclient", "pytest", "httpx"]
version: "3.10+"
retrieval_hint: "FastAPI testing TestClient pytest httpx async test"
last_verified: "2026-05-24"
confidence: "high"
---

# Testing FastAPI with TestClient

## When to Use
- Unit testing API endpoints
- Integration testing request/response flows
- Testing authentication and authorization
- Validating error handling

## Standard Pattern

```python
import pytest
from fastapi import FastAPI, Depends, HTTPException
from fastapi.testclient import TestClient
from httpx import AsyncClient

# App under test
app = FastAPI()

@app.get("/items/{item_id}")
async def get_item(item_id: int) -> dict:
    if item_id < 1:
        raise HTTPException(status_code=404, detail="Not found")
    return {"id": item_id, "name": f"Item {item_id}"}

@app.post("/items")
async def create_item(item: dict) -> dict:
    return {"id": 1, **item}


# Sync tests with TestClient
client = TestClient(app)

def test_get_item():
    response = client.get("/items/1")
    assert response.status_code == 200
    assert response.json() == {"id": 1, "name": "Item 1"}

def test_get_item_not_found():
    response = client.get("/items/0")
    assert response.status_code == 404
    assert response.json()["detail"] == "Not found"

def test_create_item():
    response = client.post("/items", json={"name": "Widget"})
    assert response.status_code == 200
    assert response.json()["name"] == "Widget"


# Async tests with httpx
@pytest.mark.anyio
async def test_get_item_async():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/items/1")
        assert response.status_code == 200
```

## Common Mistakes

```python
# WRONG: Testing with real database
def test_create_user():
    response = client.post("/users", json={"name": "Test"})
    # Pollutes real database!

# CORRECT: Use test database or mocks
@pytest.fixture
def test_db():
    # Setup test database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    # Cleanup

# WRONG: Not testing error cases
def test_get_item():
    response = client.get("/items/1")
    assert response.status_code == 200  # What about errors?

# CORRECT: Test both success and error paths
def test_get_item_success():
    response = client.get("/items/1")
    assert response.status_code == 200

def test_get_item_not_found():
    response = client.get("/items/999")
    assert response.status_code == 404

# WRONG: Using assertEqual for status codes
self.assertEqual(response.status_code, 200)  # unittest style

# CORRECT: Use pytest assert
assert response.status_code == 200
```

## Gotchas
- `TestClient` is synchronous; use `httpx.AsyncClient` for async tests
- `TestClient(app)` creates a fresh client per test (no shared state)
- Use `json=` parameter for JSON bodies, not `data=`
- `response.json()` returns parsed JSON (dict/list)
- Use `pytest.mark.anyio` (not `asyncio`) for async test support
- Override dependencies with `app.dependency_overrides` for testing
- Use `httpx.AsyncClient(app=app)` for testing without a running server

## Real-World Example

### Full API Test Suite with Dependency Overrides and Async Client

```python
import pytest
from httpx import ASGITransport, AsyncClient
from fastapi import Depends, FastAPI
from unittest.mock import AsyncMock

from myapp.main import app, get_db, get_current_user


# Mock database
mock_db = AsyncMock()
mock_db.get_user.return_value = {"id": 1, "name": "Alice", "email": "alice@example.com"}
mock_db.list_users.return_value = [mock_db.get_user.return_value]
mock_db.create_user.return_value = {"id": 2, "name": "Bob", "email": "bob@example.com"}


async def override_get_db():
    return mock_db


async def override_get_current_user():
    return {"id": 1, "username": "testuser"}


@pytest.fixture
def test_app():
    app = FastAPI()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    # Register routes from main app
    from myapp.main import router
    app.include_router(router)
    return app


@pytest.mark.anyio
async def test_list_users(test_app):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/users")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Alice"


@pytest.mark.anyio
async def test_create_user(test_app):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/users",
            json={"name": "Bob", "email": "bob@example.com"},
        )
    assert response.status_code == 201
    assert response.json()["id"] == 2


@pytest.mark.anyio
async def test_get_user_not_found(test_app):
    mock_db.get_user.return_value = None
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/users/999")
    assert response.status_code == 404
```

## Related
- python/web/fastapi/basics.md
- python/testing/pytest-basics.md
- python/testing/http-testing.md
