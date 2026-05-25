---
id: "db-sqlite-testing"
title: "SQLite for Testing: In-Memory DB, Fixtures, Test Patterns"
language: "sql"
category: "db"
tags: ["sqlite", "testing", "in-memory", "fixtures", "transactions", "rollback"]
version: "n/a"
retrieval_hint: "sqlite testing in-memory database fixtures rollback transaction test patterns"
last_verified: "2026-05-24"
confidence: "high"
---

# SQLite for Testing: In-Memory DB, Fixtures, Test Patterns

## When to Use
- Replacing production databases in tests (unit/integration)
- Fast, isolated test runs without external dependencies
- Testing schema migrations and queries
- CI environments where PostgreSQL/MySQL aren't available

## Standard Pattern

```python
# === In-Memory Database (Python/pytest example) ===

import sqlite3
import pytest


@pytest.fixture
def db():
    """Create an in-memory SQLite database for each test."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    yield conn
    conn.close()


# === Schema and Fixtures ===

@pytest.fixture
def schema(db):
    """Create tables before each test."""
    db.executescript("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            total REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending'
        );

        CREATE INDEX idx_orders_user ON orders(user_id);
    """)
    return db


@pytest.fixture
def seed_data(schema):
    """Insert test data."""
    schema.execute(
        "INSERT INTO users (email, name) VALUES (?, ?)",
        ("alice@example.com", "Alice")
    )
    schema.execute(
        "INSERT INTO users (email, name) VALUES (?, ?)",
        ("bob@example.com", "Bob")
    )

    schema.execute(
        "INSERT INTO orders (user_id, total, status) VALUES (?, ?, ?)",
        (1, 50.00, "completed")
    )
    schema.execute(
        "INSERT INTO orders (user_id, total, status) VALUES (?, ?, ?)",
        (2, 150.00, "pending")
    )
    return schema


# === Test Patterns ===

def test_user_count(seed_data):
    cursor = seed_data.execute("SELECT COUNT(*) FROM users")
    assert cursor.fetchone()[0] == 2


def test_pending_orders(seed_data):
    cursor = seed_data.execute(
        "SELECT COUNT(*) FROM orders WHERE status = 'pending'"
    )
    assert cursor.fetchone()[0] == 1


def test_transaction_rollback(seed_data):
    """Test that invalid operations don't corrupt data."""
    with pytest.raises(sqlite3.IntegrityError):
        seed_data.execute(
            "INSERT INTO orders (id, user_id, total) VALUES (?, ?, ?)",
            (999, 999, 100.00)  # FK violation — user 999 doesn't exist
        )
    # Data is still consistent
    cursor = seed_data.execute("SELECT COUNT(*) FROM orders")
    assert cursor.fetchone()[0] == 2


def test_json_field(db, schema):
    """Test JSON path queries (SQLite 3.38+)."""
    db.execute("""
        INSERT INTO users (email, name, metadata)
        VALUES (?, ?, ?)
    """, ("test@example.com", "Test", '{"role": "admin"}'))

    cursor = db.execute(
        "SELECT json_extract(metadata, '$.role') FROM users WHERE email = ?",
        ("test@example.com",)
    )
    assert cursor.fetchone()[0] == "admin"


# === Migration Testing ===

def test_migration_rollback(schema):
    """Test that a migration can be rolled back."""
    # Apply migration
    schema.executescript("""
        ALTER TABLE users ADD COLUMN timezone TEXT;
    """)

    # Verify new column
    cursor = schema.execute("SELECT timezone FROM users LIMIT 1")
    assert cursor.description[0][0] == "timezone"

    # Rollback (SQLite trick: rename + recreate)
    schema.executescript("""
        ALTER TABLE users RENAME TO users_old;
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
        INSERT INTO users (id, email, name, created_at)
            SELECT id, email, name, created_at FROM users_old;
        DROP TABLE users_old;
    """)

    # Verify column is gone
    cursor = schema.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    assert "timezone" not in columns


# === Performance Test Pattern ===

@pytest.mark.slow
def test_bulk_insert_performance(db, schema):
    """Test insert speed with transaction batching."""
    import time

    N = 10000

    # Bad: individual inserts
    start = time.time()
    for i in range(N):
        db.execute(
            "INSERT INTO users (email, name) VALUES (?, ?)",
            (f"user{i}@example.com", f"User{i}")
        )
    individual_time = time.time() - start

    # Good: batched in transaction
    start = time.time()
    db.execute("BEGIN")
    for i in range(N):
        db.execute(
            "INSERT INTO users (email, name) VALUES (?, ?)",
            (f"user{i+N}@example.com", f"User{i+N}")
        )
    db.execute("COMMIT")
    batch_time = time.time() - start

    # Batched should be 10-100x faster
    print(f"Individual: {individual_time:.2f}s, Batch: {batch_time:.2f}s")
    assert batch_time < individual_time / 10
```

## Common Mistakes

```python
# WRONG: Using on-disk database for tests (slow, cleanup needed)
conn = sqlite3.connect("test.db")  # Slow, leaves file behind

# CORRECT: Use in-memory database
conn = sqlite3.connect(":memory:")  # Fast, auto-cleaned


# WRONG: Not enabling foreign keys
conn = sqlite3.connect(":memory:")
# FK constraints silently ignored!

# CORRECT: Enable foreign keys after connection
conn = sqlite3.connect(":memory:")
conn.execute("PRAGMA foreign_keys = ON")


# WRONG: Shared in-memory database between tests (state leakage)
@pytest.fixture(scope="session")
def db():  # Same DB for all tests — tests affect each other!
    ...

# CORRECT: Fresh in-memory database per test
@pytest.fixture
def db():
    conn = sqlite3.connect(":memory:")
    yield conn
    conn.close()


# WRONG: Assuming SQLite SQL is identical to production
# Postgres: RETURNING clause
# SQLite newer versions support it, but not all features

# CORRECT: Know the SQLite dialect differences
# SQLite doesn't support:
#   - GRANT/REVOKE (no user system)
#   - RIGHT JOIN or FULL OUTER JOIN
#   - STORED PROCEDURES
#   - Window function RANGE mode (support varies)
# Test your actual queries early!


# WRONG: Not testing concurrency behavior
# Test runs single-threaded, but production uses connection pools

# CORRECT: Test with concurrent access (if production has it)
import threading
def test_concurrent_writes(db, schema):
    errors = []
    def writer():
        try:
            db.execute("INSERT INTO users (email, name) VALUES (?, ?)",
                      ("t@t.com", "Test"))
            db.commit()
        except Exception as e:
            errors.append(e)
    threads = [threading.Thread(target=writer) for _ in range(5)]
    for t in threads: t.start()
    for t in threads: t.join()
    assert len(errors) == 0  # SQLite is not great at concurrency!
```

## Gotchas
- **In-memory database is per-connection**: `:memory:` creates a private in-memory database for each connection. Two connections using `:memory:` see different databases. Use `file::memory:?cache=shared` for a shared in-memory database across connections.
- **SQLite version differences**: Production SQLite may be a different version than CI. Features like `STRICT` tables, `json_extract`, window functions, and `UPDATE FROM` require specific SQLite versions. Pin the version in CI to match production.
- **WAL mode in tests**: In-memory databases don't support WAL mode. If you need to test WAL-specific behavior, use a temporary file database (`sqlite3.connect("")` with empty string or `file::memory:?mode=memory&cache=shared`).
- **Thread safety**: Python's sqlite3 module has a "check same thread" default that prevents using the same connection from multiple threads. Use `check_same_thread=False` in connection for threaded tests, but be aware of SQLite's concurrency limitations.
- **Rollback vs transaction test isolation**: SQLite uses autocommit mode by default. Each DML statement is its own transaction. Use `BEGIN` + `COMMIT` explicitly to batch operations. The `isolation_level` parameter on the connection controls this behavior.
- **Time type differences**: SQLite has no native DATETIME type — it stores dates as TEXT, INTEGER (Unix timestamp), or REAL (Julian day). Queries using `NOW()`, `CURRENT_TIMESTAMP`, or date functions may behave differently than in PostgreSQL/MySQL.
- **Virtual tables and FTS**: Full-text search and other virtual table extensions might not be compiled into the SQLite library used in testing. Test FTS queries explicitly or skip them if the module isn't available.

## Related
- db/sqlite/production.md
- db/query-analysis.md
- db/mysql/basics.md
