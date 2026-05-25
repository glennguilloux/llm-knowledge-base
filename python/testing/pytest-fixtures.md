---
id: "python-testing-pytest-fixtures"
title: "Pytest Fixtures, Conftest, and Parametrize"
language: "python"
category: "testing"
subcategory: "pytest"
tags: ["pytest", "fixtures", "conftest", "parametrize", "scope", "testing"]
version: "3.10+"
retrieval_hint: "pytest fixtures conftest parametrize scope session module factory"
last_verified: "2026-05-24"
confidence: "high"
---

# Pytest Fixtures, Conftest, and Parametrize

## When to Use
- Setting up test dependencies (database, HTTP client, temp files) before tests run
- Sharing common test data or setup across multiple test files (conftest.py)
- Running the same test logic with different inputs (parametrize)
- Managing resource lifecycles (create on setup, cleanup on teardown)

## Standard Pattern

```python
# --- conftest.py (project root) ---
import pytest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


# Session-scoped: runs once per test session (expensive setup)
@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


# Function-scoped: runs per test (default)
@pytest.fixture
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(connection)
    yield session
    session.close()
    transaction.rollback()  # Each test runs in a rolled-back transaction
    connection.close()


# Factory fixture: create test data with custom params
@pytest.fixture
def create_user(db_session):
    created = []

    def _create(name: str = "Alice", email: str = "alice@test.com", **kwargs):
        user = User(name=name, email=email, **kwargs)
        db_session.add(user)
        db_session.flush()
        created.append(user)
        return user

    yield _create
    # Cleanup happens via transaction rollback in db_session


# Fixture with tmp_path (built-in)
@pytest.fixture
def config_file(tmp_path):
    config = tmp_path / "config.json"
    config.write_text('{"debug": true}')
    return config


# --- test_users.py ---
import pytest


def test_create_user(create_user):
    user = create_user(name="Bob", email="bob@test.com")
    assert user.id is not None
    assert user.name == "Bob"


# Parametrize: run test with multiple inputs
@pytest.mark.parametrize(
    "name,email,expected_valid",
    [
        ("Alice", "alice@example.com", True),
        ("", "alice@example.com", False),       # Empty name
        ("Alice", "invalid-email", False),       # Bad email
        ("Alice", "", False),                    # Empty email
        ("A" * 101, "a@b.com", False),           # Name too long
    ],
)
def test_user_validation(name, email, expected_valid):
    user = User(name=name, email=email)
    assert user.is_valid() == expected_valid


# Parametrize with fixtures
@pytest.mark.parametrize("create_user", [{"name": "Admin"}], indirect=True)
def test_admin_user(create_user):
    user = create_user()  # Uses the parametrized fixture
    assert user.name == "Admin"


# Parametrize with IDs for readable test names
@pytest.mark.parametrize(
    "status_code",
    [200, 201, 204],
    ids=["ok", "created", "no-content"],
)
def test_success_status_codes(status_code):
    assert status_code in {200, 201, 204}


# conftest.py in subdirectories for scoped fixtures
# tests/api/conftest.py
@pytest.fixture
def api_client():
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")
```

## Common Mistakes

```python
# WRONG: Repeating setup in every test
def test_user_create():
    engine = create_engine("sqlite:///:memory:")  # Created 100 times!
    Base.metadata.create_all(engine)
    session = Session(engine)
    # ... test ...
    session.close()

# CORRECT: Use fixtures for shared setup
def test_user_create(db_session):
    # db_session is created once (session scope) and provided by conftest
    pass

# WRONG: Not using yield for cleanup
@pytest.fixture
def temp_dir():
    path = Path("/tmp/test_data")
    path.mkdir()
    return path  # No cleanup — temp files accumulate!

# CORRECT: Use yield for cleanup
@pytest.fixture
def temp_dir():
    path = Path("/tmp/test_data")
    path.mkdir()
    yield path
    shutil.rmtree(path)  # Runs after test completes

# WRONG: Test depends on execution order
def test_create_user():
    global user_id
    user = create_user("Alice")
    user_id = user.id

def test_get_user():
    user = get_user(user_id)  # Fails if test_create_user didn't run first!

# CORRECT: Each test is independent (use fixtures for setup)
def test_get_user(create_user):
    user = create_user("Alice")
    found = get_user(user.id)
    assert found.name == "Alice"

# WRONG: Overusing session scope (tests share mutable state)
@pytest.fixture(scope="session")
def db_session():
    session = Session(engine)
    yield session  # All tests share the same session — state leaks!

# CORRECT: Use function scope with transaction rollback
@pytest.fixture
def db_session(connection):
    transaction = connection.begin()
    session = Session(connection)
    yield session
    session.close()
    transaction.rollback()  # Clean state for every test
```

## Gotchas
- Fixture scope order: `function` (default) < `class` < `module` < `package` < `session`
- Higher-scoped fixtures can't depend on lower-scoped fixtures (session can't use function)
- `conftest.py` is auto-discovered — don't import it, just use the fixture names
- `tmp_path` is a built-in fixture providing a unique temp directory per test
- `monkeypatch` is a built-in fixture for patching env vars, attributes, and dicts
- Use `@pytest.fixture(autouse=True)` sparingly — it runs for every test in scope
- Parametrize with `indirect=True` passes params to the fixture function instead of the test
- `conftest.py` in subdirectories only applies to tests in that directory

## Related
- python/testing/pytest-basics.md
- python/testing/mocking.md
- python/db/sqlite/patterns.md
