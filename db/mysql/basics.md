---
id: "db-mysql-basics"
title: "MySQL: Schema Design, Indexes, Transactions, Common Queries"
language: "sql"
category: "db"
tags: ["mysql", "sql", "schema", "indexes", "transactions", "queries"]
version: "n/a"
retrieval_hint: "mysql schema design indexes b-tree transactions ACID isolation levels common queries"
last_verified: "2026-05-24"
confidence: "high"
---

# MySQL: Schema Design, Indexes, Transactions, Common Queries

## When to Use
- Building relational data models for web applications
- Optimizing query performance with proper indexes
- Ensuring data integrity through transactions
- Writing efficient SELECT, JOIN, and aggregation queries

## Standard Pattern

```sql
-- === Schema Design ===

-- Table with conventions
CREATE TABLE users (
    id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    email       VARCHAR(255) NOT NULL,
    username    VARCHAR(100) NOT NULL,
    status      ENUM('active','inactive','suspended') NOT NULL DEFAULT 'active',
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE INDEX idx_users_email (email),
    INDEX idx_users_status (status),
    INDEX idx_users_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- === Indexes ===

-- Composite index (leftmost prefix rule applies)
CREATE INDEX idx_orders_user_status ON orders (user_id, status, created_at);
-- Queries that can use this index:
--   WHERE user_id = ?                          ✓
--   WHERE user_id = ? AND status = ?           ✓
--   WHERE user_id = ? AND status = ? AND ...   ✓
--   WHERE status = ?                           ✗ (skips leftmost column)

-- Covering index (all columns in query are in index)
CREATE INDEX idx_orders_covering ON orders (user_id, total, status);
SELECT user_id, total FROM orders WHERE user_id = 100;
-- Only index needed — no table lookup

-- Partial index (MySQL 8.0+)
CREATE INDEX idx_email_domain ON users ((SUBSTRING_INDEX(email, '@', -1)));

-- INCLUDE columns (MySQL 8.0.21+)
CREATE INDEX idx_users_status ON users (status) INCLUDE (email, username);


-- === Transactions ===

-- Explicit transaction
START TRANSACTION;

UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;

COMMIT;
-- On error: ROLLBACK;

-- Savepoints (nested rollback)
START TRANSACTION;
SAVEPOINT before_update;
UPDATE inventory SET stock = stock - 1 WHERE id = 10;
IF (SELECT stock FROM inventory WHERE id = 10) < 0 THEN
    ROLLBACK TO SAVEPOINT before_update;
END IF;
COMMIT;


-- === Isolation Levels ===

-- Set for session
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;

-- READ UNCOMMITTED  — dirty reads possible
-- READ COMMITTED    — no dirty reads (default in some systems)
-- REPEATABLE READ   — consistent snapshot (MySQL default)
-- SERIALIZABLE      — full serialization, slowest


-- === Common Query Patterns ===

-- Pagination (keyset/cursor-based — efficient for large offsets)
-- BAD: SELECT * FROM orders ORDER BY id LIMIT 100000, 20;
-- GOOD: Keyset pagination
SELECT * FROM orders
WHERE id > 100000
ORDER BY id
LIMIT 20;

-- Upsert
INSERT INTO page_views (page_id, view_count, date)
VALUES (42, 1, CURDATE())
ON DUPLICATE KEY UPDATE view_count = view_count + 1;

-- Locking read (prevent race conditions)
START TRANSACTION;
SELECT stock FROM products WHERE id = 1 FOR UPDATE;
-- Other transactions will wait for this row lock
UPDATE products SET stock = stock - 1 WHERE id = 1;
COMMIT;

-- Hierarchical query (CTE, MySQL 8.0+)
WITH RECURSIVE org_tree AS (
    SELECT id, name, parent_id, 1 AS level
    FROM employees WHERE parent_id IS NULL
    UNION ALL
    SELECT e.id, e.name, e.parent_id, ot.level + 1
    FROM employees e
    INNER JOIN org_tree ot ON e.parent_id = ot.id
)
SELECT * FROM org_tree;
```

## Common Mistakes

```sql
-- WRONG: No index on foreign key (row-level locking escalates)
-- DELETE FROM orders WHERE user_id = 100;
-- Scans full table, locks all rows!

-- CORRECT: Index foreign key columns
CREATE INDEX idx_orders_user_id ON orders (user_id);


-- WRONG: Using SELECT * in production queries
SELECT * FROM users WHERE email = 'test@example.com';
-- Returns unnecessary columns, prevents covering index usage

-- CORRECT: Select only needed columns
SELECT id, email, username FROM users WHERE email = 'test@example.com';


-- WRONG: Integer type too small (overflow!)
ALTER TABLE votes ADD count TINYINT;  -- Max 255, overflows easily

-- CORRECT: Use appropriate integer size
ALTER TABLE votes ADD count INT UNSIGNED DEFAULT 0;


-- WRONG: VARCHAR without length limit
ALTER TABLE posts ADD content VARCHAR(65535);  -- Always allocates max

-- CORRECT: Use appropriate types
ALTER TABLE posts ADD content TEXT;  -- For large text


-- WRONG: Table scan on large dataset
SELECT * FROM logs WHERE YEAR(created_at) = 2024 AND MONTH(created_at) = 5;
-- Wraps created_at in function — index can't be used!

-- CORRECT: Use range condition
SELECT * FROM logs
WHERE created_at >= '2024-05-01' AND created_at < '2024-06-01';


-- WRONG: Implicit type conversion preventing index use
SELECT * FROM users WHERE phone = 1234567890;  -- phone is VARCHAR

-- CORRECT: Use string literal
SELECT * FROM users WHERE phone = '1234567890';
```

## Gotchas
- **utf8mb4 vs utf8**: MySQL's `utf8` is actually utf8mb3 (max 3 bytes). It cannot store emoji or some CJK characters. Always use `utf8mb4` with `utf8mb4_unicode_ci` collation.
- **InnoDB vs MyISAM**: InnoDB is the default and supports transactions, foreign keys, and row-level locking. MyISAM only has table-level locking and is not crash-safe. Never use MyISAM for new projects.
- **AUTO_INCREMENT gaps**: MySQL does not guarantee gapless AUTO_INCREMENT. Rolled-back transactions, INSERT ON DUPLICATE KEY UPDATE, and server restarts can all leave gaps.
- **max_allowed_packet**: Default is 64MB. Large BLOB inserts or queries with many rows can exceed this limit. Set to a larger value in my.cnf for data-intensive workloads.
- **EXPLAIN output**: Use `EXPLAIN ANALYZE` (MySQL 8.0.18+) for actual execution times. `EXPLAIN FORMAT=JSON` shows detailed cost estimates. Always check `type` and `rows` columns for full table scans.
- **Connection pooling**: Opening a MySQL connection per request is expensive. Use a connection pool (HikariCP, pgbouncer-style `mysql.connector.pooling`) with a max of 10-20 connections per app instance.
- **ROW_FORMAT=DYNAMIC**: Modern InnoDB uses DYNAMIC row format by default. COMPACT can cause overflow issues with large VARCHARs and BLOBs. Explicitly set `ROW_FORMAT=DYNAMIC` for consistency.

## Related
- db/query-analysis.md
- db/migrations-strategy.md
- db/sqlite/production.md
