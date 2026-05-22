---
id: "python-stdlib-unittest-basics"
title: "unittest Basics for Legacy Codebases"
language: "python"
category: "testing"
subcategory: "unittest"
tags: ["unittest", "testing", "legacy", "mock", "assert", "testcase"]
version: "3.10+"
retrieval_hint: "unittest TestCase mock patch assert legacy test runner setUp"
last_verified: "2026-05-22"
confidence: "high"
---

# unittest Basics for Legacy Codebases

## When to Use
- Maintaining legacy Python codebases that use unittest (very common)
- Projects that predate pytest or have organizational unittest mandates
- Understanding existing test suites before migrating to pytest
- Simple test scenarios where pytest's features aren't needed

## Standard Pattern

```python
import unittest
from unittest.mock import patch, MagicMock, PropertyMock
from pathlib import Path


class TestUserService(unittest.TestCase):
    """Test suite for UserService."""

    @classmethod
    def setUpClass(cls) -> None:
        """Runs once before all tests in this class."""
        cls.db = create_test_database()

    @classmethod
    def tearDownClass(cls) -> None:
        """Runs once after all tests in this class."""
        cls.db.close()

    def setUp(self) -> None:
        """Runs before each test method."""
        self.service = UserService(self.db)
        self.db.begin_transaction()

    def tearDown(self) -> None:
        """Runs after each test method."""
        self.db.rollback()

    def test_create_user(self) -> None:
        user = self.service.create(name="Alice", email="alice@test.com")
        self.assertIsNotNone(user.id)
        self.assertEqual(user.name, "Alice")

    def test_duplicate_email_raises(self) -> None:
        self.service.create(name="Alice", email="alice@test.com")
        with self.assertRaises(DuplicateEmailError):
            self.service.create(name="Bob", email="alice@test.com")

    def test_user_count(self) -> None:
        self.service.create(name="Alice", email="alice@test.com")
        self.service.create(name="Bob", email="bob@test.com")
        self.assertEqual(self.service.count(), 2)

    @patch("app.services.email_sender.send")
    def test_welcome_email_sent(self, mock_send: MagicMock) -> None:
        self.service.create(name="Alice", email="alice@test.com")
        mock_send.assert_called_once_with(
            to="alice@test.com",
            subject="Welcome!",
        )


# --- Common assertions ---
class TestAssertions(unittest.TestCase):
    def test_equality(self):
        self.assertEqual(1 + 1, 2)
        self.assertNotEqual(1, 2)

    def test_boolean(self):
        self.assertTrue(True)
        self.assertFalse(False)
        self.assertIsNone(None)
        self.assertIsNotNone(42)

    def test_membership(self):
        self.assertIn(1, [1, 2, 3])
        self.assertNotIn(4, [1, 2, 3])

    def test_identity(self):
        a = [1, 2, 3]
        b = a
        self.assertIs(a, b)       # Same object
        self.assertIsNot(a, [1, 2, 3])  # Different object

    def test_approximate(self):
        self.assertAlmostEqual(0.1 + 0.2, 0.3, places=7)

    def test_regex(self):
        self.assertRegex("error: not found", r"error:.*not found")


# --- Running tests ---
# python -m unittest discover -s tests -p "test_*.py"
# python -m unittest tests.test_user_service
# python -m unittest tests.test_user_service.TestUserService.test_create_user
```

## Common Mistakes

```python
# WRONG: Test methods must start with "test_"
class TestExample(unittest.TestCase):
    def check_something(self):  # Not discovered by test runner!
        self.assertTrue(True)

# CORRECT: Prefix with test_
class TestExample(unittest.TestCase):
    def test_something(self):
        self.assertTrue(True)

# WRONG: Using assertEqual for floating point
self.assertEqual(0.1 + 0.2, 0.3)  # Fails due to float precision

# CORRECT: Use assertAlmostEqual
self.assertAlmostEqual(0.1 + 0.2, 0.3, places=7)

# WRONG: Mocking the wrong target
@patch("app.models.User.save")  # Patches the class method
def test_save(self, mock_save):
    user = User()
    user.save()  # Doesn't use the mock!

# CORRECT: Patch where it's used, not where it's defined
@patch("app.services.UserService.save")  # Patches where it's imported
def test_save(self, mock_save):
    service = UserService()
    service.save()  # Uses the mock

# WRONG: Not cleaning up mocks between tests
@patch("app.services.send_email")
class TestEmail(unittest.TestCase):
    def test_one(self, mock_send):
        send_email("test@test.com", "Subject", "Body")
        # mock_send not reset between tests!

# CORRECT: Use setUp/tearDown or patch as decorator/context manager
class TestEmail(unittest.TestCase):
    def test_one(self):
        with patch("app.services.send_email") as mock_send:
            send_email("test@test.com", "Subject", "Body")
            mock_send.assert_called_once()
```

## Gotchas
- Test methods MUST start with `test_` — otherwise they're silently skipped
- `setUp` runs before each test; `setUpClass` runs once for the entire class
- `tearDown` runs after each test even if it fails — use for cleanup
- `@patch` decorator applies patches in reverse order (bottom-up)
- `assertRaises` as context manager gives access to the exception: `with self.assertRaises(E) as cm`
- `MagicMock` auto-creates attributes and methods — use `spec=ClassName` for strict mocking
- `patch.object(target, "method")` patches a specific method on an instance
- pytest can run unittest tests — you can mix both frameworks during migration

## Related
- python/testing/pytest-basics.md
- python/testing/mocking.md
- python/testing/pytest-fixtures.md
