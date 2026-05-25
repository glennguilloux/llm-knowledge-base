---
id: "db-query-analysis"
title: "Query Analysis: EXPLAIN Plans, Performance Tuning, Slow Queries"
language: "sql"
category: "db"
tags: ["sql", "query-analysis", "explain", "performance", "indexing", "optimization"]
version: "n/a"
retrieval_hint: "sql query analysis EXPLAIN EXPLAIN ANALYZE query plans performance tuning index optimization slow queries"
last_verified: "2026-05-24"
confidence: "high"
---

# Query Analysis: EXPLAIN Plans, Performance Tuning, Slow Queries

## When to Use
- Diagnosing slow or inefficient queries
- Understanding how the database executes a query
- Validating index usage and join strategies
- Optimizing query performance

## Standard Pattern

```sql
-- === EXPLAIN Plans ===

-- PostgreSQL
EXPLAIN SELECT * FROM orders WHERE user_id = 42;
-- Output:
-- Seq Scan on orders  (cost=0.00..1000.00 rows=1 width=100)
--   Filter: (user_id = 42)

-- With actual execution time (executes the query!)
EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 42;

-- JSON format (more details)
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) SELECT * FROM orders WHERE user_id = 42;


-- MySQL
EXPLAIN SELECT * FROM orders WHERE user_id = 42\G;
-- Output columns: id, select_type, table, type, possible_keys, key,
--                 key_len, ref, rows, Extra

-- With actual execution (MySQL 8.0.18+)
EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 42;


-- SQLite
EXPLAIN QUERY PLAN SELECT * FROM orders WHERE user_id = 42;
-- Output: SCAN orders


-- === Understanding Query Plan Metrics ===

-- cost=0.00..1000.00
--   First number: startup cost (index seeks, etc.)
--   Second number: total cost to return all rows

-- rows=1
--   Estimated number of rows (may be inaccurate with stale statistics)

-- width=100
--   Average row width in bytes

-- Key scan types (best to worst):
--   Const / system     → single row by PK (fastest)
--   Ref                → non-unique index lookup
--   Range              → index range scan
--   Index              → full index scan
--   Seq Scan           → full table scan (slowest)


-- === Common Optimization Patterns ===

-- 1. Missing index (Seq Scan on large table)
-- Seq Scan on orders  (cost=0.00..10000.00 rows=1 width=200)
--   Filter: (status = 'pending')
-- Solution: CREATE INDEX idx_orders_status ON orders (status);

-- 2. Bad index order (composite index with wrong column order)
-- Index: (status, created_at)
-- Query: WHERE created_at > '2024-01-01' AND status = 'active'
--         ↑ Can't use index efficiently (skips leftmost column)
-- Solution: Reorder index to (status, created_at) ← put high-selectivity first

-- 3. Function wrapping prevents index use
-- WHERE YEAR(created_at) = 2024     → Seq Scan always!
-- WHERE created_at >= '2024-01-01' AND created_at < '2025-01-01'  → Index Scan

-- 4. Implicit type conversion
-- WHERE phone = 1234567890          → No index use (phone is VARCHAR)
-- WHERE phone = '1234567890'        → Index used

-- 5. JOIN without proper indexes
-- Hash Join (large inner table with no index)
--   → Add index on the join column of the inner table


-- === Slow Query Diagnosis Steps ===

-- 1. Enable slow query log
-- PostgreSQL: SET log_min_duration_statement = 200;  (ms)
-- MySQL:      SET GLOBAL slow_query_log = 1;
--             SET GLOBAL long_query_time = 0.2;

-- 2. Read the plan
-- If Seq Scan on large table → add index
-- If estimated rows >> actual rows → update statistics

-- 3. Update statistics
-- PostgreSQL: ANALYZE;
-- MySQL:      ANALYZE TABLE orders;
-- SQLite:     ANALYZE;

-- 4. Check for N+1
-- 100 queries instead of 1 with JOIN → use eager loading

-- 5. Use LIMIT
-- SELECT * FROM orders LIMIT 20  → can stop early with Index Scan
```

## Common Mistakes

```sql
-- WRONG: Only looking at execution time, not plan
-- 100ms query → "it's fine" — but it scans 1M rows!

-- CORRECT: Always check the query plan
EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM orders WHERE status = 'pending';
-- If you see Seq Scan on a large table, the problem will grow with data


-- WRONG: Adding an index without checking if queries use it
CREATE INDEX idx_users_email_domain ON users (SUBSTRING_INDEX(email, '@', -1));
-- EXPLAIN shows: Seq Scan — the function index syntax is wrong for MySQL

-- CORRECT: Verify index is used in the query plan
EXPLAIN SELECT * FROM users WHERE SUBSTRING_INDEX(email, '@', -1) = 'example.com';
-- If it shows "Index Scan" → index is being used


-- WRONG: Ignoring estimated vs actual row counts
EXPLAIN ANALYZE SELECT * FROM orders WHERE status = 'pending';
-- Estimated: 100 rows  Actual: 100000 rows
-- Stale statistics! Run ANALYZE.

-- CORRECT: Keep statistics up to date
ANALYZE;


-- WRONG: Fixing slow queries by throwing hardware at them
-- A query scanning 50M rows will always be slow, even on fast hardware

-- CORRECT: Fix the root cause — add indexes, rewrite query, or cache


-- WRONG: Using subqueries where JOIN would be better
SELECT * FROM users WHERE id IN (SELECT user_id FROM orders WHERE total > 1000);
-- Many databases execute this as a correlated subquery (row by row!)

-- CORRECT: Use JOIN or EXISTS
SELECT DISTINCT u.* FROM users u
JOIN orders o ON u.id = o.user_id AND o.total > 1000;
```

## Gotchas
- **Statistics staleness**: After bulk inserts/deletes, statistics become stale. PostgreSQL's autovacuum handles this automatically, but ANALYZE after bulk operations ensures optimal plans.
- **Parallel query plans**: PostgreSQL can parallelize Seq Scans but not some index scans. A parallel Seq Scan may be faster than a serial Index Scan for queries returning a significant fraction of rows. Don't blindly assume "Index Scan = always better".
- **Parameterized queries and plan caching**: PostgreSQL caches query plans for parameterized queries. The first execution's plan is reused even if parameters change. For skewed data distributions, this can produce bad plans — use `PREPARE` or adaptive query optimization.
- **LIMIT with ORDER BY**: `SELECT * FROM users ORDER BY created_at DESC LIMIT 10` without index on `created_at` scans the entire table and sorts before applying the limit. An index on `(created_at)` lets the planner read the index in order and stop after 10 rows.
- **UDF and ORM abstraction**: ORMs generate queries you may not expect. Always capture and EXPLAIN the actual SQL the ORM sends. The Rails/ActiveRecord query log or Django debug toolbar can show raw SQL.
- **EXPLAIN in production**: `EXPLAIN ANALYZE` executes the query. For write-heavy production databases, use `EXPLAIN` (without ANALYZE) or run on a replica to avoid side effects.
- **Buffer cache and cold starts**: First execution of a query may read from disk (cold cache), while subsequent executions read from memory. Run the query twice when benchmarking to measure hot-cache performance.

## Related
- db/mysql/basics.md
- db/migrations-strategy.md
- db/sqlite/production.md
