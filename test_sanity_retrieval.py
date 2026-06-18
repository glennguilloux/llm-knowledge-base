#!/usr/bin/env python3
"""Fast sanity checks for offline retrieval APIs."""

import pytest

from llm_kb import retrieve
from llm_kb.retrieve import load_entries, search_by_keywords


pytestmark = pytest.mark.sanity


EXPECTED_IDS = {
    "sha256_file_hashing": "python-stdlib-hashlib-sha256",
    "fastapi_jwt": "python-web-fastapi-auth-jwt",
    "typescript_async_promise": "typescript-stdlib-async-patterns",
    "postgres_window_functions": "db-postgres-window-functions",
}


@pytest.fixture(scope="module")
def entries():
    return load_entries()


def result_ids(results):
    return [entry.id for entry in results]


def assert_recalled(results, expected_id):
    assert expected_id in result_ids(results)


def test_sha256_file_hashing_recall(entries):
    results = search_by_keywords(entries, "SHA-256 file hashing in Python")

    assert_recalled(results, EXPECTED_IDS["sha256_file_hashing"])


def test_fastapi_jwt_recall(entries):
    results = search_by_keywords(entries, "FastAPI JWT authentication")

    assert_recalled(results, EXPECTED_IDS["fastapi_jwt"])


def test_typescript_async_promise_recall(entries):
    results = search_by_keywords(entries, "TypeScript async Promise await")

    assert_recalled(results, EXPECTED_IDS["typescript_async_promise"])


def test_public_retrieve_language_filter_python():
    results = retrieve("hashing", language="python", top_k=5)

    assert results
    assert all(entry["language"] == "python" for entry in results)
    assert EXPECTED_IDS["sha256_file_hashing"] in [entry["id"] for entry in results]


def test_empty_query_returns_without_crashing(entries):
    results = search_by_keywords(entries, "")

    assert results == []


def test_optional_postgresql_window_function_recall(entries):
    results = search_by_keywords(entries, "PostgreSQL window functions ROW_NUMBER")

    assert_recalled(results, EXPECTED_IDS["postgres_window_functions"])
