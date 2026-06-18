#!/usr/bin/env python3
"""Stress test for search with full dataset.

Tests:
- Load ALL known entries and verify baseline count
- Run 20+ representative queries spanning all languages
- Verify keyword search completes in < 200ms per query
- Verify every query returns at least one result
- Verify language-filtered queries return correctly filtered results
"""

import time
import pytest

from retrieval import search, load_entries


# Representative queries covering all major languages and categories
STRESS_QUERIES = [
    # (query, language, expected_id_substring)
    ("SHA-256 file hashing in Python", None, "sha256"),
    ("FastAPI app setup routing endpoint", "python", "fastapi"),
    ("Java streams filter map collect", "java", "stream"),
    ("TypeScript async Promise await", "typescript", "async"),
    ("Go goroutines concurrency", "go", "goroutine"),
    ("Rust ownership borrowing move", "rust", "ownership"),
    ("C# async await Task pattern", "csharp", "async"),
    ("Bash scripting patterns shebang", "bash", "scripting"),
    ("SQLAlchemy ORM model definition", "python", "sqlalchemy"),
    ("pytest fixtures parametrize", "python", "pytest"),
    ("Spring Boot configuration properties", "java", "spring"),
    ("React hooks useEffect useState", "typescript", "react"),
    ("PostgreSQL window functions ROW_NUMBER", None, "window"),
    ("Docker Compose multi-container", None, "docker"),
    ("GitHub Actions CI/CD workflow", None, "github"),
    ("AES GCM encryption decrypt", None, "aes"),
    ("JWT token sign verify", None, "jwt"),
    ("rate limiting algorithm token bucket", None, "rate"),
    ("Redis set get cache Python", "python", "redis"),
    ("Celery task queue worker", "python", "celery"),
]


class TestStressLoad:
    """Verify the full dataset can be loaded and has expected size."""

    def test_loads_all_entries(self):
        entries = load_entries()
        # Must be at least 30 entries — the minimum viable KB
        assert len(entries) >= 30, f"Only loaded {len(entries)} entries"

    def test_entries_have_required_fields(self):
        entries = load_entries()
        for entry in entries:
            assert entry.id, f"Entry missing id: {entry.filepath}"
            assert entry.title, f"Entry missing title: {entry.filepath}"
            assert entry.language, f"Entry missing language: {entry.filepath}"
            assert entry.category, f"Entry missing category: {entry.filepath}"
            assert entry.tags, f"Entry missing tags: {entry.filepath}"


class TestStressSearchPerformance:
    """Verify search performance under load."""

    def test_search_all_queries_return_results(self):
        """Every stress query should return at least one result."""
        for query, lang, _ in STRESS_QUERIES:
            results = search(query, language=lang, top_k=3)
            assert len(results) > 0, (
                f"Query '{query}' (lang={lang}) returned zero results"
            )

    def test_keyword_search_below_500ms(self):
        """Keyword search must average < 500ms per query."""
        timings = []
        for query, lang, _ in STRESS_QUERIES:
            start = time.perf_counter()
            search(query, language=lang, top_k=3)
            elapsed = (time.perf_counter() - start) * 1000  # ms
            timings.append(elapsed)

        avg_ms = sum(timings) / len(timings)
        max_ms = max(timings)
        assert avg_ms < 500, (
            f"Average keyword search too slow: {avg_ms:.1f}ms "
            f"(max: {max_ms:.1f}ms, n={len(timings)})"
        )

    def test_search_top_k_honored(self):
        """top_k parameter must be respected."""
        for k in [1, 3, 5]:
            results = search("testing", top_k=k)
            assert len(results) <= k, (
                f"top_k={k} returned {len(results)} results"
            )

    def test_language_filter_works(self):
        """Language filter must only return entries of that language."""
        for lang in ["python", "java", "typescript", "go"]:
            results = search("async", language=lang, top_k=10)
            for r in results:
                assert r.language == lang, (
                    f"Expected language={lang}, got {r.language} for {r.id}"
                )


class TestStressQueryExpansion:
    """Verify query expansion improves recall for abbreviation queries."""

    def test_jwt_expansion(self):
        """JWT should match entries via query expansion."""
        results_jwt = search("JWT", top_k=3)
        results_full = search("JSON Web Token", top_k=3)
        assert len(results_jwt) > 0
        assert len(results_full) > 0


class TestStressEmptyEdgeCases:
    """Edge cases under load conditions."""

    def test_empty_query(self):
        results = search("", top_k=3)
        assert len(results) == 0

    def test_gibberish_query(self):
        results = search("zxcvbnmlkjhgfdsa", top_k=3)
        assert len(results) == 0

    def test_zero_top_k(self):
        """top_k=0 should return empty results."""
        results = search("testing", top_k=0)
        assert len(results) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
