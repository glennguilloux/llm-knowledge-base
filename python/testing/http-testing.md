---
id: "python-testing-http-testing"
title: "Testing HTTP APIs"
language: "python"
category: "testing"
subcategory: "integration-testing"
tags: ["testing", "http", "api", "testclient", "httpx", "integration"]
version: "3.10+"
retrieval_hint: "testing HTTP API integration testclient httpx mock"
last_verified: "2026-05-24"
confidence: "high"
---

# Testing HTTP APIs

## When to Use
- Integration testing API endpoints
- Testing request/response flows
- Validating error handling and status codes
- Testing authentication and middleware

## Standard Pattern

```python
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, Mock


# FastAPI TestClient (sync)
@pytest.fixture
def client():
    from myapp import app
    return TestClient(app)


def test_get_user(client):
    response = client.get("/users/1")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data


def test_create_user(client):
    response = client.post("/users", json={"name": "Alice", "email": "alice@test.com"})
    assert response.status_code == 201
    assert response.json()["name"] == "Alice"


def test_not_found(client):
    response = client.get("/users/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Not found"


# Async TestClient (httpx)
@pytest.fixture
async def async_client():
    from myapp import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.anyio
async def test_async_endpoint(async_client):
    response = await async_client.get("/users/1")
    assert response.status_code == 200


# Testing with mocked external services
def test_with_mocked_api(client, mocker):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"external_id": 123}
    
    mocker.patch("httpx.AsyncClient.get", return_value=mock_response)
    
    response = client.get("/users/1/external-data")
    assert response.status_code == 200


# Testing authentication
def test_protected_endpoint(client):
    # Without auth
    response = client.get("/protected")
    assert response.status_code == 401
    
    # With auth
    response = client.get(
        "/protected",
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 200
```

## Common Mistakes

```python
# WRONG: Testing with real external APIs
def test_fetch_user(client):
    response = client.get("/users/1")  # Hits real database!

# CORRECT: Mock external dependencies
def test_fetch_user(client, mocker):
    mocker.patch("myapp.db.get_user", return_value={"id": 1, "name": "Alice"})
    response = client.get("/users/1")
    assert response.status_code == 200

# WRONG: Not testing error paths
def test_api(client):
    response = client.get("/items/1")
    assert response.status_code == 200  # What about errors?

# CORRECT: Test both success and error paths
def test_api_success(client):
    response = client.get("/items/1")
    assert response.status_code == 200

def test_api_not_found(client):
    response = client.get("/items/999")
    assert response.status_code == 404

# WRONG: Using requests in tests
def test_api():
    response = requests.get("http://localhost:8000/users")  # Requires running server!

# CORRECT: Use TestClient (no server needed)
def test_api(client):
    response = client.get("/users")
```

## Gotchas
- `TestClient` is synchronous; use `httpx.AsyncClient` for async tests
- `TestClient(app)` doesn't require a running server
- Use `json=` for JSON bodies, `data=` for form data
- `response.json()` returns parsed JSON
- Use `mocker.patch()` to mock external service calls
- Test authentication by passing `headers={"Authorization": "Bearer ..."}`
- Use `pytest.mark.anyio` (not `asyncio`) for async tests

## Real-World Example

### Integration Test with Mocked External API and Auth

```python
import pytest
from unittest.mock import AsyncMock, patch
from httpx import ASGITransport, AsyncClient

from myapp.main import app
from myapp.deps import get_current_user


async def override_auth():
    return {"id": 1, "username": "testuser"}


@pytest.fixture
def test_app():
    app.dependency_overrides[get_current_user] = override_auth
    yield app
    app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_get_user_profile(test_app):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/users/me",
            headers={"Authorization": "Bearer test-token"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"


@pytest.mark.anyio
async def test_fetch_external_data(test_app):
    mock_response = {"weather": "sunny", "temp": 72}
    with patch("myapp.services.httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.get.return_value.json.return_value = mock_response
        mock_instance.get.return_value.status_code = 200
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/weather")

    assert response.status_code == 200
    assert response.json()["weather"] == "sunny"


@pytest.mark.anyio
async def test_unauthorized_access(test_app):
    # Remove auth override for this test
    app.dependency_overrides.clear()
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/users/me")
    assert response.status_code == 401
```

## Related
- python/web/fastapi/testing.md
- python/testing/pytest-basics.md
- python/testing/mocking.md
