---
id: "python-testing-pytest-basics"
title: "Pytest Basics and Fixtures"
language: "python"
category: "testing"
subcategory: "unit-testing"
tags: ["pytest", "testing", "fixture", "parametrize", "markers"]
version: "3.10+"
retrieval_hint: "pytest test fixture parametrize marker assert"
last_verified: "2026-05-22"
confidence: "high"
---

# Pytest Basics and Fixtures

## When to Use
- Writing unit tests
- Test fixtures for setup/teardown
- Parametrized tests for multiple inputs
- Test organization with markers

## Standard Pattern

```python
import pytest


# Basic test
def test_addition():
    assert 1 + 1 == 2


# Test with expected exception
def test_division_by_zero():
    with pytest.raises(ZeroDivisionError):
        1 / 0


# Fixture
@pytest.fixture
def sample_user() -> dict:
    return {"name": "Alice", "email": "alice@example.com"}


def test_user_name(sample_user: dict):
    assert sample_user["name"] == "Alice"


# Fixture with cleanup
@pytest.fixture
def temp_file(tmp_path):
    file = tmp_path / "test.txt"
    file.write_text("test data")
    yield file
    # Cleanup happens automatically with tmp_path


# Parametrize
@pytest.mark.parametrize(
    "input_val,expected",
    [
        (1, 1),
        (2, 4),
        (3, 9),
        (0, 0),
        (-1, 1),
    ],
)
def test_square(input_val: int, expected: int):
    assert input_val**2 == expected


# Markers
@pytest.mark.slow
def test_slow_operation():
    import time
    time.sleep(5)
    assert True


# Fixture scope
@pytest.fixture(scope="module")
def database_connection():
    conn = create_connection()
    yield conn
    conn.close()


# conftest.py (shared fixtures)
# Place in tests/conftest.py for project-wide fixtures
@pytest.fixture
def api_client():
    from fastapi.testclient import TestClient
    from myapp import app
    return TestClient(app)
```

## Common Mistakes

```python
# WRONG: Using unittest style
class TestMath(unittest.TestCase):
    def test_add(self):
        self.assertEqual(1 + 1, 2)  # Verbose!

# CORRECT: Use pytest style
def test_add():
    assert 1 + 1 == 2

# WRONG: Not using fixtures for setup
def test_with_setup():
    db = create_db()
    db.insert("test data")
    result = db.query()
    assert result == "test data"
    db.close()  # Never runs if assertion fails!

# CORRECT: Use fixtures for setup/teardown
@pytest.fixture
def db():
    db = create_db()
    yield db
    db.close()

def test_with_fixture(db):
    db.insert("test data")
    result = db.query()
    assert result == "test data"

# WRONG: Testing multiple things in one test
def test_user():
    user = create_user("Alice")
    assert user.name == "Alice"
    assert user.email == "alice@example.com"
    assert user.age == 30  # Too many assertions!

# CORRECT: One assertion per test (or related group)
def test_user_name():
    user = create_user("Alice")
    assert user.name == "Alice"

def test_user_email():
    user = create_user("Alice")
    assert user.email == "alice@example.com"
```

## Gotchas
- `pytest.raises()` as context manager to test exceptions
- `tmp_path` fixture provides a temporary directory (auto-cleaned)
- `scope="module"` runs fixture once per module (not per test)
- `conftest.py` fixtures are auto-discovered (no import needed)
- Use `@pytest.mark.skip` and `@pytest.mark.skipif` for conditional skipping
- `pytest -x` stops on first failure; `-v` for verbose output
- Use `assert` statements, not `self.assertEqual()`

## Real-World Example

### Complete Test Suite with Fixtures, Parametrize, and Markers

```python
import pytest
from unittest.mock import AsyncMock, patch
from myapp.services import UserService, EmailService


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.query.return_value.filter.return_value.first.return_value = None
    return db


@pytest.fixture
def user_service(mock_db):
    return UserService(db=mock_db)


@pytest.fixture
def email_service():
    return AsyncMock(spec=EmailService)


@pytest.fixture
def sample_user():
    return {"id": 1, "email": "alice@example.com", "name": "Alice"}


class TestUserService:
    @pytest.mark.anyio
    async def test_create_user(self, user_service, mock_db, email_service):
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        user = await user_service.create("alice@example.com", "Alice")
        mock_db.add.assert_called_once()
        email_service.send_welcome.assert_called_once_with("alice@example.com")

    @pytest.mark.anyio
    async def test_create_user_duplicate(self, user_service, mock_db):
        mock_db.commit.side_effect = IntegrityError("duplicate", {}, None)
        with pytest.raises(ValueError, match="already exists"):
            await user_service.create("alice@example.com", "Alice")

    @pytest.mark.parametrize("email,valid", [
        ("user@example.com", True),
        ("invalid", False),
        ("@example.com", False),
        ("user@", False),
    ])
    def test_email_validation(self, email, valid):
        assert UserService.is_valid_email(email) == valid

    @pytest.mark.slow
    @pytest.mark.anyio
    async def test_bulk_import(self, user_service):
        # Marked as slow — skipped with: pytest -m "not slow"
        users = [{"email": f"user{i}@test.com"} for i in range(100)]
        result = await user_service.bulk_create(users)
        assert result == 100
```

## Related
- python/testing/mocking.md
- python/testing/http-testing.md
- python/web/fastapi/testing.md
