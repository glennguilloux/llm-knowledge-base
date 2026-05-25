---
id: "db-sqlite-production"
title: "SQLite in Production: WAL Mode, Concurrency, Performance"
language: "sql"
category: "db"
tags: ["sqlite", "wal", "concurrency", "performance", "embedded-database"]
version: "n/a"
retrieval_hint: "sqlite production WAL mode concurrency performance pragmas backup embedded database"
last_verified: "2026-05-24"
confidence: "high"
---

# SQLite in Production: WAL Mode, Concurrency, Performance

## When to Use
- Embedded databases for desktop and mobile applications
- Read-heavy workloads with moderate write volume
- Development and testing environments
- Data analysis and ETL pipelines

## Standard Pattern

```sql
-- === WAL Mode (Write-Ahead Log) ===

-- Enable WAL mode (much better concurrency)
PRAGMA journal_mode=WAL;

-- Benefits:
--   ✓ Concurrent reads during writes
--   ✓ Faster writes (sequential WAL writes instead of random)
--   ✓ No need for VACUUM after deletes
-- Tradeoffs:
--   ✗ Slightly larger disk usage
--   ✗ Readers may block checkpointing

-- WAL checkpoint settings
PRAGMA wal_autocheckpoint=1000;     -- Checkpoint every 1000 pages
PRAGMA wal_checkpoint(TRUNCATE);     -- Manual checkpoint, truncates WAL


-- === Performance Pragmas ===

-- Typical production configuration
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;           -- Good balance (default FULL)
PRAGMA cache_size=-64000;            -- 64MB cache (negative = KB)
PRAGMA temp_store=MEMORY;            -- Temp tables in RAM
PRAGMA mmap_size=268435456;          -- 256MB memory-mapped I/O
PRAGMA page_size=4096;               -- 4KB pages (must set before creating DB)

-- Foreign keys (off by default for backward compatibility)
PRAGMA foreign_keys=ON;

-- Busy timeout (milliseconds to wait before SQLITE_BUSY)
PRAGMA busy_timeout=5000;


-- === Schema Optimizations ===

-- WITHOUT ROWID tables (when explicit primary key)
CREATE TABLE lookup (
    code    TEXT PRIMARY KEY,
    value   TEXT NOT NULL
) WITHOUT ROWID;
-- Stores data in the B-tree by primary key directly
-- Saves space (no implicit rowid) and is faster for PK lookups

-- STRICT tables (SQLite 3.37+)
CREATE TABLE users (
    id    INTEGER PRIMARY KEY,
    name  TEXT NOT NULL,
    age   INTEGER NOT NULL
) STRICT;
-- Enforces type checking — rejects mismatched types


-- === Concurrency Pattern ===

-- Writer queue pattern (prevent SQLITE_BUSY)
-- Application code (pseudo):
-- conn = sqlite3.connect("app.db", timeout=5)
-- conn.execute("BEGIN IMMEDIATE")
-- # Writes
-- conn.commit()

-- Read-only connections can read while writer is active (in WAL)
-- Each reader sees the database state when the read started


-- === Backup ===

-- Online backup (while database is in use)
-- $ sqlite3 app.db ".backup app.backup.db"

-- Programmatic backup
-- backup = sqlite3_backup_init(dst_db, "main", src_db, "main")
-- backup.step(-1)  # Copy all pages
-- backup.finish()


-- === Full-Text Search (FTS5) ===

CREATE VIRTUAL TABLE posts_fts USING fts5(
    title, content,
    content=posts,                      -- Sync with external table
    content_rowid=rowid
);

-- Triggers to keep FTS in sync
CREATE TRIGGER posts_ai AFTER INSERT ON posts BEGIN
    INSERT INTO posts_fts(rowid, title, content)
    VALUES (new.rowid, new.title, new.content);
END;

-- Search
SELECT * FROM posts_fts WHERE posts_fts MATCH 'sqlite';
```

## Common Mistakes

```sql
-- WRONG: Using default journal mode (rollback journal)
-- Reads block writes and writes block reads. Terrible concurrency.

-- CORRECT: Always set WAL mode for production
PRAGMA journal_mode=WAL;


-- WRONG: No busy timeout (immediate SQLITE_BUSY on contention)
-- Second writer fails immediately if first is active

-- CORRECT: Set busy timeout
PRAGMA busy_timeout=5000;
-- SQLite will retry writes for up to 5 seconds


-- WRONG: Not using transactions for multiple writes
INSERT INTO log VALUES (...);  -- Auto-commit
INSERT INTO log VALUES (...);  -- Auto-commit — 2x fsyncs!

-- CORRECT: Batch in explicit transaction
BEGIN;
INSERT INTO log VALUES (...);
INSERT INTO log VALUES (...);
COMMIT;


-- WRONG: Using TEXT for data that could be INTEGER
CREATE TABLE prices (
    id INTEGER PRIMARY KEY,
    amount TEXT  -- Sorting "9.99" < "10.00" fails!
);

-- CORRECT: Use appropriate types
CREATE TABLE prices (
    id INTEGER PRIMARY KEY,
    amount REAL
);


-- WRONG: Opening a new connection per HTTP request
-- Every connection opens and locks the database file

-- CORRECT: Use a single shared connection (or pool of 1-4)
-- SQLite works best with one writer, many readers


-- WRONG: VACUUM on a large database during peak hours
VACUUM;  -- Locks database, rewrites entire file, takes seconds/minutes

-- CORRECT: Schedule VACUUM during maintenance windows
-- Or use auto_vacuum (incremental)
PRAGMA auto_vacuum=INCREMENTAL;
```

## Gotchas
- **WAL file grows unbounded**: If readers stay open for long periods, the WAL file grows because SQLite can't checkpoint (readers might need old pages). Close idle readers or use `wal_checkpoint(TRUNCATE)` periodically.
- **NFS/network filesystems**: SQLite relies on POSIX advisory locks which are broken on most NFS implementations. Never store SQLite databases on network filesystems. Use client-server databases (PostgreSQL, MySQL) for network storage.
- **Page size must be set before creation**: `PRAGMA page_size` only affects new databases. Changing it on an existing database requires `VACUUM` or `sqlite3 db.sqlite ".page_size 8192"`. Default 4096 is fine for most workloads.
- **64-bit and file sizes**: SQLite supports databases up to 281 TB. The `page_count` pragma limitation means databases with many small pages are more constrained. Use 8192+ page sizes for large databases.
- **Thread safety**: SQLite can be compiled in single-thread, multi-thread, or serialized mode. The default Python/Go drivers use serialized mode (safe for shared connections). C drivers may need `SQLITE_CONFIG_SERIALIZED`.
- **ALTER TABLE limitations**: SQLite supports only `ADD COLUMN`, `RENAME COLUMN`, and `DROP COLUMN` (3.35.0+). You cannot add foreign keys, add NOT NULL, or change column types after creation. You must recreate the table for structural changes.
- **UPSERT syntax**: SQLite supports `INSERT ... ON CONFLICT DO UPDATE SET ...` (similar to Postgres). Avoid `REPLACE INTO` which does a DELETE+INSERT and resets AUTOINCREMENT.

## Related
- db/sqlite/testing.md
- db/query-analysis.md
- db/migrations-strategy.md
