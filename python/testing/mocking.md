---
id: "python-testing-mocking"
title: "Mocking with unittest.mock and pytest-mock"
language: "python"
category: "testing"
subcategory: "mocking"
tags: ["mock", "patch", "unittest", "pytest-mock", "stub", "fake"]
version: "3.10+"
retrieval_hint: "mock patch unittest pytest mock stub fake test double"
last_verified: "2026-05-22"
confidence: "high"
---

# Mocking with unittest.mock and pytest-mock

## When to Use
- Isolating code from external dependencies (APIs, databases, files)
- Testing error conditions
- Verifying function calls
- Replacing slow operations in tests

## Standard Pattern

```python
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import pytest


# Mock with pytest-mock (recommended)
def test_user_creation(mocker):
    # Mock a function
    mock_send_email = mocker.patch("myapp.services.send_email")
    
    create_user("alice@example.com")
    
    mock_send_email.assert_called_once_with("alice@example.com")


# Mock with unittest.mock
@patch("myapp.services.send_email")
def test_user_creation_unittest(mock_send_email):
    create_user("alice@example.com")
    mock_send_email.assert_called_once_with("alice@example.com")


# Mock return value
def test_api_call(mocker):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": 1, "name": "Alice"}
    
    mocker.patch("requests.get", return_value=mock_response)
    
    result = fetch_user(1)
    assert result["name"] == "Alice"


# Mock side effects
def test_error_handling(mocker):
    mocker.patch("myapp.db.get_user", side_effect=Exception("DB error"))
    
    with pytest.raises(Exception, match="DB error"):
        get_user(1)


# Async mock
@pytest.mark.anyio
async def test_async_function(mocker):
    mock_fetch = mocker.patch("myapp.api.fetch_data", new_callable=AsyncMock)
    mock_fetch.return_value = {"data": "test"}
    
    result = await process_data()
    assert result == {"data": "test"}


# Context manager mock
def test_file_operations(mocker):
    mock_open = mocker.patch("builtins.open", mocker.mock_open(read_data="file content"))
    
    result = read_file("test.txt")
    assert result == "file content"
    mock_open.assert_called_once_with("test.txt", "r")
```

## Common Mistakes

```python
# WRONG: Mocking at the wrong level
@patch("requests.get")  # Patches the wrong module!
def test_api(mocker):
    from myapp.api import fetch_data
    fetch_data()

# CORRECT: Patch where it's used, not where it's defined
@patch("myapp.api.requests.get")  # Patch in the module that uses it
def test_api(mocker):
    fetch_data()

# WRONG: Not asserting mock was called
def test_send_email(mocker):
    mock_send = mocker.patch("myapp.send_email")
    process_order(order)
    # Forgot to check if send_email was called!

# CORRECT: Assert mock calls
def test_send_email(mocker):
    mock_send = mocker.patch("myapp.send_email")
    process_order(order)
    mock_send.assert_called_once_with(order.customer_email)

# WRONG: Mocking too much
def test_user_service(mocker):
    mocker.patch("myapp.db.get_user")
    mocker.patch("myapp.db.save_user")
    mocker.patch("myapp.email.send")
    mocker.patch("myapp.cache.set")
    # Test is now testing nothing real!

# CORRECT: Mock only external dependencies
def test_user_service(mocker):
    mocker.patch("myapp.email.send")  # Only mock external service
    result = create_user("alice@example.com")
    assert result.name == "Alice"
```

## Gotchas
- `mocker.patch("module.path")` patches where the name is looked up, not where it's defined
- `mock.assert_called_once_with()` checks exact arguments
- `mock.call_args` gives access to actual arguments
- `side_effect` can be an exception, a function, or an iterable
- `return_value` sets what the mock returns
- Use `mocker.patch.object()` to patch an object's attribute
- `AsyncMock` for async functions (Python 3.8+)

## Related
- python/testing/pytest-basics.md
- python/testing/http-testing.md
