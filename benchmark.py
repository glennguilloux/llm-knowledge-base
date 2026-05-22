#!/usr/bin/env python3
"""Benchmark retrieval accuracy: grep vs vector vs hybrid."""

import time
from pathlib import Path

from retrieval import search as grep_search
from hybrid_retrieval import search as hybrid_search


# Test queries with expected relevant entry IDs
TEST_CASES = [
    {
        "query": "how to hash a file in Python",
        "expected_ids": ["python-stdlib-hashlib-sha256", "crypto-sha256"],
    },
    {
        "query": "FastAPI JWT authentication",
        "expected_ids": ["python-web-fastapi-auth-jwt"],
    },
    {
        "query": "SQLAlchemy ORM model definition",
        "expected_ids": ["python-db-sqlalchemy-2.0-models"],
    },
    {
        "query": "pytest fixtures and parametrize",
        "expected_ids": ["python-testing-pytest-basics"],
    },
    {
        "query": "retry with exponential backoff",
        "expected_ids": ["python-patterns-retry-logic"],
    },
    {
        "query": "Redis caching set get",
        "expected_ids": ["python-db-redis-basics"],
    },
    {
        "query": "password hashing bcrypt argon2",
        "expected_ids": ["crypto-password-hashing"],
    },
    {
        "query": "database migrations alembic",
        "expected_ids": ["python-db-sqlalchemy-2.0-migrations-alembic"],
    },
    {
        "query": "HTTP requests sessions cookies",
        "expected_ids": ["python-web-requests-sessions", "python-web-requests-basics"],
    },
    {
        "query": "async await concurrency",
        "expected_ids": ["python-stdlib-asyncio-basics"],
    },
]


def evaluate_results(results: list, expected_ids: list[str], top_k: int = 5) -> dict:
    """Evaluate search results against expected IDs."""
    result_ids = [r.id if hasattr(r, "id") else r.get("id", "") for r in results[:top_k]]
    hits = sum(1 for eid in expected_ids if eid in result_ids)
    return {
        "hits": hits,
        "total_expected": len(expected_ids),
        "recall": hits / len(expected_ids) if expected_ids else 0,
        "result_ids": result_ids,
    }


def run_benchmark() -> None:
    """Run benchmark comparing grep and hybrid retrieval."""
    print("=" * 60)
    print("Knowledge Base Retrieval Benchmark")
    print("=" * 60)

    grep_total_recall = 0
    grep_total_time = 0
    hybrid_total_recall = 0
    hybrid_total_time = 0

    for i, test in enumerate(TEST_CASES, 1):
        query = test["query"]
        expected = test["expected_ids"]

        print(f"\n{i}. Query: \"{query}\"")
        print(f"   Expected: {expected}")

        # Grep search
        start = time.perf_counter()
        grep_results = grep_search(query, top_k=5)
        grep_time = time.perf_counter() - start
        grep_eval = evaluate_results(grep_results, expected)

        print(f"   Grep:   {grep_eval['hits']}/{grep_eval['total_expected']} recall "
              f"({grep_time:.3f}s) → {grep_eval['result_ids']}")

        # Hybrid search (if ChromaDB is available)
        try:
            start = time.perf_counter()
            hybrid_results = hybrid_search(query, top_k=5)
            hybrid_time = time.perf_counter() - start
            hybrid_eval = evaluate_results(hybrid_results, expected)

            print(f"   Hybrid: {hybrid_eval['hits']}/{hybrid_eval['total_expected']} recall "
                  f"({hybrid_time:.3f}s) → {hybrid_eval['result_ids']}")

            hybrid_total_recall += hybrid_eval["recall"]
            hybrid_total_time += hybrid_time
        except Exception as e:
            print(f"   Hybrid: Skipped ({e})")

        grep_total_recall += grep_eval["recall"]
        grep_total_time += grep_time

    n = len(TEST_CASES)
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Grep:   Avg recall = {grep_total_recall/n:.2f}, Total time = {grep_total_time:.3f}s")
    if hybrid_total_time > 0:
        print(f"Hybrid: Avg recall = {hybrid_total_recall/n:.2f}, Total time = {hybrid_total_time:.3f}s")


if __name__ == "__main__":
    run_benchmark()
