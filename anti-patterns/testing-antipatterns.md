---
id: "antipatterns-testing"
title: "Testing Anti-Patterns: Flaky Tests, Over-Mocking, and Testing Implementation"
language: "multi"
category: "anti-patterns"
tags: ["antipatterns", "testing", "flaky-tests", "over-mocking", "integration-tests", "private-methods"]
version: "n/a"
retrieval_hint: "testing antipatterns testing implementation not behavior flaky tests not testing error paths over-mocking testing private methods no integration tests"
last_verified: "2026-05-24"
confidence: "high"
---

# Testing Anti-Patterns: Flaky Tests, Over-Mocking, and Testing Implementation

## When to Use
- Reviewing test code
- Training LLMs to write better tests
- Test code review checklist
- Understanding testing best practices

## Standard Pattern

```markdown
# WRONG: Testing implementation details instead of behavior
# Testing that internal method was called 3 times — brittle!
mock_processor.assert_called_with(data)
mock_processor.assert_called_with(data)  # Exact call count

# CORRECT: Test the observable behavior
result = process(data)
assert result.status == "completed"
assert result.output == expected_output

# WRONG: Flaky tests (depend on timing, external services, random data)
def test_user_creation():
    user = create_user()  # Uses random email
    assert get_user(user.id) == user  # May fail if timing issue

# CORRECT: Deterministic tests with controlled data
def test_user_creation():
    user = create_user(email="test@example.com")
    fetched = get_user(user.id)
    assert fetched.email == "test@example.com"

# WRONG: Not testing error paths
def test_divide():
    assert divide(10, 2) == 5
    # What about divide(10, 0)?

# CORRECT: Test both success and failure paths
def test_divide():
    assert divide(10, 2) == 5
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)

# WRONG: Over-mocking (mocking everything including the system under test)
mock_db = Mock()
mock_cache = Mock()
mock_logger = Mock()
service = Service(mock_db, mock_cache, mock_logger)
# Test passes but tests nothing real!

# CORRECT: Mock only external dependencies, use real objects for core logic
real_service = Service(real_db, mock_cache, mock_logger)
# Or use test doubles for external services

# WRONG: Testing private methods directly
service = Service()
result = service._internal_method(data)  # Testing private method!

# CORRECT: Test through public API
service = Service()
result = service.process(data)  # Tests private method indirectly

# WRONG: No integration tests (only unit tests)
# Unit tests pass but the system doesn't work when components are connected!

# CORRECT: Test pyramid — many unit tests, some integration tests, few E2E
# Unit: Test individual functions/classes in isolation
# Integration: Test component interactions (service + database)
# E2E: Test full user flows (API → database → response)

# WRONG: Tests depend on execution order
def test_create():
    db.insert("user1")  # Must run first!

def test_read():
    user = db.get("user1")  # Depends on test_create!
    assert user is not None

# CORRECT: Each test is independent
def test_create():
    db.insert("user1")
    assert db.get("user1") is not None

def test_read():
    db.insert("test_user")  # Set up own data
    user = db.get("test_user")
    assert user is not None

# WRONG: No test isolation (shared mutable state)
users = []  # Shared between tests!

def test_add_user():
    users.append(User("Alice"))  # Modifies shared state!

def test_count():
    assert len(users) == 0  # Fails if test_add_user ran first!

# CORRECT: Each test creates its own data
def test_add_user():
    users = [User("Alice")]  # Local state
    assert len(users) == 1

def test_count():
    users = []  # Fresh state
    assert len(users) == 0

# WRONG: printf debugging in production (leftover print statements)
def process(data):
    print(f"DEBUG: data = {data}")  # Left in production code!
    result = transform(data)
    print(f"DEBUG: result = {result}")
    return result

# CORRECT: Use proper logging with levels
import logging
logger = logging.getLogger(__name__)

def process(data):
    logger.debug("Processing data: %s", data)
    result = transform(data)
    logger.debug("Result: %s", result)
    return result
```

## Common Mistakes
- Testing implementation details — brittle tests that break on any refactoring
- Flaky tests — fail intermittently, erode trust in the test suite
- Not testing error paths — only testing the happy path, missing edge cases
- Over-mocking — mocking everything so tests test nothing real
- Testing private methods — breaks encapsulation, test through public API
- No integration tests — unit tests pass but system doesn't work when connected
- Tests depend on execution order — each test should be independent
- No test isolation — shared mutable state between tests causes interference

## Gotchas
- Tests should be **F**ast, **I**ndependent, **R**epeatable, **S**elf-validating, **T**imely (FIRST principles).
- The test pyramid: many cheap unit tests, fewer integration tests, few expensive E2E tests.
- Flaky tests erode trust. If tests fail randomly, developers stop running them.
- Mock external dependencies (APIs, databases), not the system under test.
- Test behavior (what the code does), not implementation (how it does it).
- Each test should set up its own data and clean up after itself.
- Use `setUp`/`tearDown` or fixtures for shared test setup.
- Error paths are where bugs hide. Always test them.
- Integration tests catch issues that unit tests miss (configuration, wiring, database schema).

## Related
- anti-patterns/database-antipatterns.md
- anti-patterns/api-antipatterns.md
- anti-patterns/concurrency-antipatterns.md
- anti-patterns/logging-antipatterns.md
