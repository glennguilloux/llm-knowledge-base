---
id: "python-testing-snapshot-testing"
title: "Snapshot Testing with syrupy"
language: "python"
category: "testing"
subcategory: "snapshot"
tags: ["snapshot", "syrupy", "testing", "golden", "regression", "output"]
version: "3.10+"
retrieval_hint: "snapshot testing syrupy golden file regression test output comparison"
last_verified: "2026-05-22"
confidence: "high"
---

# Snapshot Testing with syrupy

## When to Use
- Testing complex output that's tedious to assert field by field (API responses, HTML, JSON)
- Regression testing: catch unexpected changes in output format
- Testing serialization/deserialization roundtrips
- Verifying generated code, templates, or configuration files

## Standard Pattern

```python
# Install: pip install syrupy
# Run: pytest --snapshot-update (to update snapshots)

import pytest
from syrupy.assertion import SnapshotAssertion


def test_api_response(snapshot: SnapshotAssertion):
    """Snapshot test for API response structure."""
    response = get_user_api(user_id=1)
    assert response.status_code == 200
    assert response.json() == snapshot


def test_user_serialization(snapshot: SnapshotAssertion):
    """Test that User serialization matches expected format."""
    user = User(id=1, name="Alice", email="alice@test.com", created_at=datetime(2024, 1, 1))
    serialized = user.to_dict()
    assert serialized == snapshot


def test_html_output(snapshot: SnapshotAssertion):
    """Test rendered HTML template."""
    html = render_template("user_card.html", user=user)
    assert html == snapshot


def test_json_export(snapshot: SnapshotAssertion):
    """Test JSON export format."""
    data = export_to_json(records)
    assert json.loads(data) == snapshot


# --- Custom snapshot directory ---
def test_with_custom_dir(snapshot: SnapshotAssertion):
    snapshot = snapshot.with_defaults(extension_class=SingleFileSnapshotExtension)
    assert complex_object == snapshot


# --- Updating specific snapshots ---
# pytest --snapshot-update tests/test_api.py::test_api_response
# pytest --snapshot-update -k "test_user"
```

## Common Mistakes

```python
# WRONG: Using snapshots for values that change every run
def test_timestamp(snapshot):
    result = {"timestamp": time.time(), "data": "test"}
    assert result == snapshot  # Fails every time!

# CORRECT: Exclude volatile fields from snapshots
def test_timestamp(snapshot):
    result = {"timestamp": time.time(), "data": "test"}
    assert result["data"] == snapshot
    assert isinstance(result["timestamp"], float)

# WRONG: Not reviewing snapshot changes before committing
# Just running --snapshot-update without checking diffs

# CORRECT: Always review snapshot diffs
# git diff __snapshots__/ before committing

# WRONG: Using snapshots for simple values
def test_addition(snapshot):
    assert 1 + 1 == snapshot  # Overkill — just use assertEqual

# CORRECT: Use snapshots for complex, structured output
def test_api_response(snapshot):
    assert response.json() == snapshot  # Complex nested structure

# WRONG: Snapshot tests without --snapshot-update on new tests
def test_new_feature(snapshot):
    assert new_output == snapshot  # Fails because snapshot doesn't exist yet

# CORRECT: Run with --snapshot-update first for new tests
# pytest --snapshot-update tests/test_new_feature.py
```

## Gotchas
- Snapshots are stored in `__snapshots__/` directory next to the test file (by default)
- Use `pytest --snapshot-update` to create or update snapshots
- Snapshots are committed to version control — review diffs like code changes
- `syrupy` supports JSON, text, image, and custom serializers
- Use `snapshot.with_defaults(extension_class=...)` for custom formats
- `SingleFileSnapshotExtension` stores all snapshots in one file per test module
- Snapshot names auto-derive from test function name + index for parametrized tests
- `assert ... == snapshot` order matters — snapshot must be on the right side

## Related
- python/testing/pytest-fixtures.md
- python/testing/pytest-basics.md
- python/web/fastapi/testing.md
