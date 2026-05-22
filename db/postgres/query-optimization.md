---
id: "db-postgres-query-optimization"
title: "Query Optimization Patterns"
language: "sql"
category: "db"
tags: ["sql", "postgresql", "optimization", "explain", "performance", "query-plan"]
version: "14+"
retrieval_hint: "EXPLAIN ANALYZE query plan optimization slow query N+1"
last_verified: "2026-05-22"
confidence: "high"
---

# Query Optimization Patterns

## When to Use
- Diagnosing slow queries
- Understanding execution plans
- Optimizing JOIN-heavy queries
- Detecting and fixing N+1 query problems
- Tuning PostgreSQL configuration for performance

## Standard Pattern

```sql
-- EXPLAIN ANALYZE: see actual execution plan
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT u.name, COUNT(o.id)
FROM users u
JOIN orders o ON o.user_id = u.id
WHERE u.created_at > '2024-01-01'
GROUP BY u.name;

-- Reading the output:
-- Seq Scan on users: sequential scan — no index used
-- Index Scan on orders: index used — good
-- actual time=0.010..0.020: first row / all rows time in ms
-- rows=1000: estimated rows
-- loops=1: number of times this node executed
-- Buffers: shared hit=50 read=10: 50 from cache, 10 from disk

-- Detecting N+1 queries (application-level)
-- Bad: 1 query for users + N queries for orders
SELECT * FROM users;
-- For each user:
SELECT * FROM orders WHERE user_id = ?;

-- Good: single JOIN query
SELECT u.*, o.*
FROM users u
LEFT JOIN orders o ON o.user_id = u.id
WHERE u.status = 'active';

-- Good: batch with IN clause
SELECT * FROM orders WHERE user_id IN (1, 2, 3, 4, 5);

-- pg_stat_statements: find slow queries
SELECT
    calls,
    total_exec_time / 1000 AS total_seconds,
    mean_exec_time / 1000 AS mean_seconds,
    rows,
    query
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;

-- Reset stats
SELECT pg_stat_statements_reset();

-- Common join algorithms (PostgreSQL chooses automatically)
-- Nested Loop: good for small inner table with index
-- Hash Join: good for medium tables, no index on join column
-- Merge Join: good for pre-sorted data

-- Force join strategy (for testing, not production)
SET enable_nestloop = off;
SET enable_hashjoin = off;
SET enable_mergejoin = off;

-- CTE optimization (PG 12+)
-- NOT MATERIALIZED allows predicate pushdown
WITH active AS NOT MATERIALIZED (
    SELECT id, name FROM users WHERE status = 'active'
)
SELECT * FROM active WHERE name LIKE 'A%';
-- The LIKE filter is pushed into the CTE

-- Batch updates instead of row-by-row
-- Bad:
UPDATE users SET last_login = NOW() WHERE id = 1;
UPDATE users SET last_login = NOW() WHERE id = 2;
-- Good:
UPDATE users SET last_login = NOW() WHERE id IN (1, 2, 3);

-- Use EXISTS instead of IN for subqueries
-- Slower:
SELECT * FROM users WHERE id IN (SELECT user_id FROM orders);
-- Faster:
SELECT * FROM users u WHERE EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id);
```

## Common Mistakes

```sql
-- WRONG: SELECT * when only some columns needed
SELECT * FROM large_table WHERE id = 1;
-- Reads all columns including large TEXT/JSONB fields

-- CORRECT: Select only needed columns
SELECT id, name, email FROM large_table WHERE id = 1;
-- Enables covering index if columns are in index

-- WRONG: Function on indexed column prevents index use
SELECT * FROM users WHERE LOWER(email) = 'test@example.com';
-- Index on (email) is NOT used

-- CORRECT: Create expression index
CREATE INDEX idx_users_lower_email ON users (LOWER(email));
-- Now the index is used

-- WRONG: Implicit type cast prevents index use
SELECT * FROM users WHERE id = '123';  -- id is integer, '123' is text
-- May cause sequential scan

-- CORRECT: Match types
SELECT * FROM users WHERE id = 123;

-- WRONG: OR prevents index use in some cases
SELECT * FROM users WHERE status = 'active' OR email LIKE '%@test.com';
-- May do sequential scan

-- CORRECT: Use UNION for different index conditions
SELECT * FROM users WHERE status = 'active'
UNION
SELECT * FROM users WHERE email LIKE '%@test.com';

-- WRONG: Large OFFSET for pagination
SELECT * FROM orders ORDER BY id LIMIT 20 OFFSET 100000;
-- PostgreSQL must scan and discard 100000 rows

-- CORRECT: Keyset pagination
SELECT * FROM orders WHERE id > 100000 ORDER BY id LIMIT 20;
-- Uses index directly — O(1) instead of O(N)
```

## Gotchas
- `EXPLAIN` shows estimated plan; `EXPLAIN ANALYZE` runs the query and shows actual times
- `BUFFERS` option shows cache hits vs disk reads — critical for I/O analysis
- `Seq Scan` is not always bad — it's faster than Index Scan for small tables or large result sets
- `Index Only Scan` is the fastest — all data comes from the index, no heap access
- `Sort` nodes can be expensive — ensure ORDER BY matches index order
- `HashAggregate` is faster than `Sort + GroupAggregate` for large groups
- `pg_stat_statements` requires the extension — enable in `postgresql.conf`
- N+1 queries are an application-level problem — use JOINs or batch queries
- Keyset pagination (`WHERE id > ?`) is O(1); offset pagination is O(N)
- `ANALYZE` command updates table statistics — run after large data changes
- `VACUUM` reclaims dead tuples — run regularly or enable autovacuum

## Related
- db/postgres/indexing-strategies.md
- db/postgres/window-functions.md
- db/postgres/ctes.md
