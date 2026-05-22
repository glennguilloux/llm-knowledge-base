#!/usr/bin/env python3
"""Tests for the retrieval system."""

import pytest
from pathlib import Path

from retrieval import search, load_entries, parse_entry, search_by_keywords


@pytest.fixture
def kb_path():
    return Path(".")


@pytest.fixture
def entries(kb_path):
    return load_entries(kb_path)


class TestLoadEntries:
    def test_loads_all_entries(self, entries):
        assert len(entries) >= 30

    def test_entries_have_required_fields(self, entries):
        for entry in entries:
            assert entry.id
            assert entry.title
            assert entry.language
            assert entry.category
            assert entry.tags


class TestSearchByKeywords:
    def test_find_sha256(self, entries):
        results = search_by_keywords(entries, "SHA-256 hashing")
        assert len(results) > 0
        assert any("sha256" in e.id for e in results)

    def test_find_fastapi(self, entries):
        results = search_by_keywords(entries, "FastAPI routing")
        assert len(results) > 0
        assert any("fastapi" in e.id for e in results)

    def test_find_jwt(self, entries):
        results = search_by_keywords(entries, "JWT authentication")
        assert len(results) > 0
        assert any("jwt" in e.id for e in results)

    def test_find_sqlalchemy(self, entries):
        results = search_by_keywords(entries, "SQLAlchemy ORM model")
        assert len(results) > 0
        assert any("sqlalchemy" in e.id for e in results)

    def test_find_pytest(self, entries):
        results = search_by_keywords(entries, "pytest testing fixtures")
        assert len(results) > 0
        assert any("pytest" in e.id for e in results)

    def test_empty_query_returns_empty(self, entries):
        results = search_by_keywords(entries, "")
        assert len(results) == 0

    def test_no_match_returns_empty(self, entries):
        results = search_by_keywords(entries, "cobol fortran mainframe")
        assert len(results) == 0


class TestSearch:
    def test_search_with_language_filter(self, kb_path):
        results = search("hashing", language="python", kb_path=kb_path)
        assert all(e.language == "python" for e in results)

    def test_search_top_k(self, kb_path):
        results = search("testing", top_k=2, kb_path=kb_path)
        assert len(results) <= 2

    def test_search_returns_relevant(self, kb_path):
        results = search("how to hash a file in Python", kb_path=kb_path)
        assert len(results) > 0
        # Should find hashlib or sha256 entries
        ids = [e.id for e in results]
        assert any("hashlib" in id or "sha256" in id for id in ids)


class TestParseEntry:
    def test_parse_valid_entry(self, tmp_path):
        entry_file = tmp_path / "test.md"
        entry_file.write_text("""---
id: "test-entry"
title: "Test Entry"
language: "python"
category: "stdlib"
tags: ["test"]
retrieval_hint: "test entry"
last_verified: "2025-01-15"
confidence: "high"
---

# Test Entry

## When to Use
- Testing

## Standard Pattern
```python
print("hello")
```

## Common Mistakes
```python
# WRONG: bad
# CORRECT: good
```

## Gotchas
- None

## Related
""")
        entry = parse_entry(entry_file)
        assert entry is not None
        assert entry.id == "test-entry"
        assert entry.title == "Test Entry"

    def test_parse_invalid_entry(self, tmp_path):
        entry_file = tmp_path / "invalid.md"
        entry_file.write_text("# Not a valid entry")
        entry = parse_entry(entry_file)
        assert entry is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
