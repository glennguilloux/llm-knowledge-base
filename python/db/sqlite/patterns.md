---
id: "python-db-sqlite-patterns"
title: "SQLite Patterns for Python"
language: "python"
category: "db"
subcategory: "sqlite"
tags: ["sqlite", "database", "embedded", "lightweight", "testing", "file"]
version: "3.10+"
retrieval_hint: "SQLite embedded database file-based testing in-memory connection"
last_verified: "2026-05-24"
confidence: "high"
---

# SQLite Patterns for Python

## When to Use
- Embedded applications, CLI tools, or desktop apps needing a local database
- Testing with an in-memory database (no external dependencies)
- Prototyping before migrating to PostgreSQL/MySQL
- Small to medium applications with low concurrent write requirements
- Data processing scripts that need structured querying of local data

## Standard Pattern

```python
import sqlite3
from pathlib import Path
from contextlib import contextmanager


# --- Connection management ---
@contextmanager
def get_db(db_path: str = "app.db"):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Access columns by name
    conn.execute("PRAGMA journal_mode=WAL")      # Better concurrent reads
    conn.execute("PRAGMA foreign_keys=ON")        # Enforce FK constraints
    conn.execute("PRAGMA busy_timeout=5000")      # Wait 5s on lock
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# --- Schema setup ---
def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            author_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_posts_author ON posts(author_id);
    """)


# --- CRUD operations ---
def create_user(conn: sqlite3.Connection, name: str, email: str) -> int:
    cursor = conn.execute("INSERT INTO users (name, email) VALUES (?, ?)", (name, email))
    return cursor.lastrowid


def get_user(conn: sqlite3.Connection, user_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def list_users(conn: sqlite3.Connection, limit: int = 20) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM users ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()


def search_users(conn: sqlite3.Connection, query: str) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM users WHERE name LIKE ? OR email LIKE ?",
        (f"%{query}%", f"%{query}%"),
    ).fetchall()


# --- In-memory database for testing ---
def create_test_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    init_db(conn)
    return conn


# --- Bulk insert ---
def bulk_insert_users(conn: sqlite3.Connection, users: list[tuple]) -> None:
    conn.executemany("INSERT INTO users (name, email) VALUES (?, ?)", users)
```

## Common Mistakes

```python
# WRONG: String formatting in SQL (SQL injection!)
conn.execute(f"SELECT * FROM users WHERE id = {user_id}")

# CORRECT: Use parameterized queries
conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))

# WRONG: Not using WAL mode for concurrent reads
conn = sqlite3.connect("app.db")  # Default journal mode = DELETE (locks on writes)

# CORRECT: Enable WAL for better concurrency
conn.execute("PRAGMA journal_mode=WAL")

# WRONG: Not enabling foreign keys
conn = sqlite3.connect("app.db")
conn.execute("INSERT INTO posts (author_id) VALUES (999)")  # Succeeds even if user 999 doesn't exist!

# CORRECT: Enable foreign keys (off by default in SQLite)
conn.execute("PRAGMA foreign_keys=ON")

# WRONG: Fetching all rows into memory
rows = conn.execute("SELECT * FROM huge_table").fetchall()  # OOM risk

# CORRECT: Iterate over cursor for large results
for row in conn.execute("SELECT * FROM huge_table"):
    process(row)
```

## Gotchas
- `PRAGMA foreign_keys=ON` must be set per-connection — it resets on every new connection
- WAL mode allows concurrent reads during writes but only one writer at a time
- SQLite has no user authentication — security is file-system level
- `:memory:` databases are per-connection — each connection gets its own empty database
- Use `?` placeholders, not `%s` (that's MySQL/psycopg style)
- `row_factory = sqlite3.Row` enables dict-like access: `row["name"]` instead of `row[0]`
- SQLite doesn't enforce `TEXT` length limits — use application-level validation
- `lastrowid` is only valid for `INSERT` with `AUTOINCREMENT` or `INTEGER PRIMARY KEY`

## Related
- python/db/sqlalchemy-2.0/models.md
- python/testing/pytest-basics.md
- python/web/flask/basics.md
