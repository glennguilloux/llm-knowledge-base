---
id: "python-testing-pytest-parametrize-deep"
title: "Advanced pytest Parametrize Patterns"
language: "python"
category: "testing"
subcategory: "pytest"
tags: ["pytest", "parametrize", "testing", "parameterized", "fixtures", "indirect", "ids"]
version: "3.10+"
retrieval_hint: "pytest parametrize parameterized tests indirect fixture stacked mark ids"
last_verified: "2026-05-25"
confidence: "high"
---

# Advanced pytest Parametrize Patterns

## When to Use
- Running the same test logic with many different inputs
- Testing edge cases, error conditions, and boundary values systematically
- Generating test matrices (combinations of independent parameters)
- Feeding fixture data into tests at parameterization time (indirect)
- Making test failure output readable with custom test IDs

## Standard Pattern

```python
import pytest
from typing import Any


# --- Basic parametrize with multiple arguments ---
@pytest.mark.parametrize("input_val, expected", [
    (1, 2),
    (2, 4),
    (3, 6),
    (10, 20),
])
def test_double(input_val: int, expected: int):
    assert input_val * 2 == expected


# --- Custom test IDs for readability ---
@pytest.mark.parametrize(
    "email, expected_valid",
    [
        ("user@example.com", True),
        ("user.name+tag@example.co.uk", True),
        ("not-an-email", False),
        ("@missing-user.com", False),
        pytest.param("", False, id="empty-string"),
        pytest.param("a" * 256 + "@example.com", False, id="too-long-local-part"),
    ],
)
def test_email_validation(email: str, expected_valid: bool):
    from re import match
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    assert bool(match(pattern, email)) == expected_valid


# --- Stacked parametrize decorators (Cartesian product) ---
@pytest.mark.parametrize("auth_method", ["none", "basic", "token"])
@pytest.mark.parametrize("endpoint", ["/api/users", "/api/posts", "/api/health"])
@pytest.mark.parametrize("method", ["GET", "POST"])
def test_api_combinations(method: str, endpoint: str, auth_method: str):
    """Tests ALL combinations: 3 endpoints × 2 methods × 3 auth = 18 tests."""
    assert isinstance(method, str)
    assert isinstance(endpoint, str)
    assert isinstance(auth_method, str)


# --- Indirect parametrization (feeds parametrize into fixtures) ---
class FakeDB:
    def __init__(self):
        self.data: dict[str, Any] = {}

@pytest.fixture
def db(request) -> FakeDB:
    """Creates a FakeDB, pre-populated from parametrize."""
    database = FakeDB()
    seed_data = getattr(request, "param", {})
    database.data.update(seed_data)
    return database

@pytest.mark.parametrize("db", [
    {"users": [{"id": 1, "name": "Alice"}]},
    {"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]},
    {"posts": [{"title": "Hello"}]},
], indirect=True)
def test_db_with_seed(db: FakeDB):
    if "users" in db.data:
        assert len(db.data["users"]) >= 1
    if "posts" in db.data:
        assert len(db.data["posts"]) >= 1


# --- Parametrize with pytest.param for granular marking ---
@pytest.mark.parametrize("url, status_code", [
    pytest.param("/api/health", 200, marks=pytest.mark.slow),
    pytest.param("/api/users", 200, marks=pytest.mark.smoke),
    pytest.param("/api/nonexistent", 404, marks=[pytest.mark.smoke, pytest.mark.slow]),
])
def test_endpoint_status(url: str, status_code: int):
    """Each parameter can have different marks."""
    assert isinstance(url, str)
    assert isinstance(status_code, int)


# --- Lazy evaluation with pytest.param and fixtures via request ---
@pytest.fixture
def user_service():
    return {"base_url": "http://testserver/api/v1"}

@pytest.mark.parametrize("user_id, expected_name", [
    (1, "Alice"),
    (2, "Bob"),
    pytest.param(
        999, "Unknown",
        marks=pytest.mark.xfail(reason="User 999 may not exist", strict=False)
    ),
])
def test_user_lookup(user_service, user_id, expected_name):
    """xfail marking works inside parametrize."""
    # Simulate lookup
    users = {1: "Alice", 2: "Bob"}
    result = users.get(user_id, "Unknown")
    assert result == expected_name
```

## Common Mistakes

```python
# WRONG: Mutable default in parametrize — all tests share the same list
@pytest.mark.parametrize("items", [
    [],     # These are FINE — literals
    [1, 2],
    [3],
])
def test_bad_mutable_default(items: list[int]):
    items.append(99)  # This modifies... nothing bad, actually

# CORRECT: Use immutable fixtures for shared state
# Prefer tuple or frozen data structures when tests share references.
@pytest.fixture
def fresh_list():
    """Returns a new list for each test — no sharing issues."""
    return []

# What IS dangerous is fixtures with mutable defaults:
@pytest.fixture
def shared_list():
    return []  # NOT shared between tests unless you use scope="module"

# WRONG: Quadratic explosion — 10×10×10 = 1000 tests you didn't expect
@pytest.mark.parametrize("x", range(10))
@pytest.mark.parametrize("y", range(10))
@pytest.mark.parametrize("z", range(10))
def test_explosion(x, y, z):
    pass  # 1000 tests generated!

# CORRECT: Use pytest.mark.parametrize with a single list of tuples for N parameters
@pytest.mark.parametrize("x, y, z", [
    (1, 2, 3),
    (4, 5, 6),
    (7, 8, 9),
])
def test_controlled(x, y, z):
    pass  # Only 3 tests

# WRONG: Missing ids= for readable output
@pytest.mark.parametrize("n", [1, 2, 3, 100, -1, 0])
def test_opaque(n):
    assert n >= 0 or n < 0  # Test names will be test_opaque[1], test_opaque[2], etc.

# CORRECT: Using ids with a function
def id_fn(n):
    return f"n-is-{n}"

@pytest.mark.parametrize("n", [1, 2, 3, 100, -1, 0], ids=id_fn)
def test_readable(n):
    assert isinstance(n, int)
```

## Gotchas
- **`indirect=True` scope interaction:** When using `indirect=True`, the fixture's scope determines setup/teardown frequency. A `scope="session"` fixture with indirect parametrize will ONLY be set up ONCE with the FIRST parameter value — subsequent parameters are ignored! Use `scope="function"` for per-parameter re-initialization.
- **Stacking order matters:** When stacking `@pytest.mark.parametrize`, the OUTER decorator varies slowest, the INNER varies fastest. `@parametrize("x")` over `@parametrize("y")` produces `x0_y0, x0_y1, x1_y0, x1_y1`. Read tests carefully — this is easy to mis-order.
- **`pytest.param` marks propagate:** Marks on individual parameters (`pytest.param(x, marks=pytest.mark.slow)`) apply ONLY to that specific test variant. Combined with `-m` filtering, you can selectively run subsets of parametrized tests.
- **Parametrizing class-level fixtures:** You can parametrize fixtures defined in a class using `@pytest.mark.parametrize` on the class or method, but class-scoped fixtures get parametrized ONCE for the whole class. Use `scope="function"` if you need per-test parametrization.
- **Empty parametrization = skipped test:** If the parametrize list is empty (e.g., `@pytest.mark.parametrize("x", [])`), the test is SKIPPED entirely, not failed. This can silently drop coverage if a data source returns empty results.

## Related
- python/testing/pytest-basics.md
- python/testing/pytest-fixtures.md
