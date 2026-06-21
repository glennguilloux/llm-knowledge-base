---
id: "db-postgres-explain-analyze"
title: "EXPLAIN ANALYZE Query Plan Debugging"
language: "sql"
category: "db"
subcategory: "postgres"
tags: ["sql", "postgresql", "explain", "analyze", "buffers", "query-plan", "performance", "index-scan", "seq-scan"]
version: "14+"
retrieval_hint: "PostgreSQL EXPLAIN ANALYZE BUFFERS query plan index scan sequential scan slow query performance"
last_verified: "2026-05-24"
confidence: "medium"
---

# EXPLAIN ANALYZE Query Plan Debugging

## When to Use
- Diagnosing slow PostgreSQL queries before adding indexes or rewriting SQL
- Comparing estimated planner costs with actual execution times
- Checking whether a query uses an intended index, join strategy, or sort method
- Investigating buffer usage and disk I/O for expensive filters, joins, or aggregations
- Verifying query-plan changes after `ANALYZE`, index creation, or SQL refactoring

## Standard Pattern

```sql
-- Start with an estimated plan: does not execute the query
EXPLAIN (FORMAT TEXT)
SELECT u.id, u.email, COUNT(o.id) AS order_count
FROM users u
JOIN orders o ON o.user_id = u.id
WHERE u.created_at >= DATE '2025-01-01'
GROUP BY u.id, u.email
ORDER BY order_count DESC
LIMIT 20;

-- Run the query and collect actual timing plus buffer usage
EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
SELECT u.id, u.email, COUNT(o.id) AS order_count
FROM users u
JOIN orders o ON o.user_id = u.id
WHERE u.created_at >= DATE '2025-01-01'
GROUP BY u.id, u.email
ORDER BY order_count DESC
LIMIT 20;

-- Use JSON output when a tool needs structured plan data
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
SELECT user_id, created_at
FROM orders
WHERE status = 'paid'
ORDER BY created_at DESC
LIMIT 50;

-- Check a plan after refreshing table statistics
ANALYZE orders;
EXPLAIN (ANALYZE, BUFFERS)
SELECT COUNT(*)
FROM orders
WHERE status = 'paid'
AND created_at >= NOW() - INTERVAL '30 days';

-- Compare alternatives inside a transaction and roll back any planner setting side effects
BEGIN;
SET LOCAL enable_seqscan = off;
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM orders
WHERE user_id = 42
ORDER BY created_at DESC
LIMIT 10;
ROLLBACK;
```

## Common Mistakes

```sql
-- WRONG: Treating EXPLAIN as the same as EXPLAIN ANALYZE
EXPLAIN SELECT * FROM orders WHERE user_id = 42;
-- Shows only planner estimates; it does not run the query or report actual time

-- CORRECT: Use EXPLAIN ANALYZE for real timing and row counts
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM orders WHERE user_id = 42;

-- WRONG: Assuming Seq Scan is always bad
EXPLAIN (ANALYZE)
SELECT COUNT(*) FROM small_lookup_table;
-- A sequential scan can be faster for tiny tables or queries returning most rows

-- CORRECT: Judge scans by actual time, rows, and buffers
EXPLAIN (ANALYZE, BUFFERS)
SELECT COUNT(*) FROM small_lookup_table;
-- If actual time is low and buffers are small, the plan may be appropriate

-- WRONG: Forgetting that EXPLAIN ANALYZE executes data-modifying statements
EXPLAIN (ANALYZE)
UPDATE orders SET processed_at = NOW()
WHERE processed_at IS NULL;
-- This UPDATE runs and changes data

-- CORRECT: Wrap destructive checks in a transaction and roll back after inspecting the plan
BEGIN;
EXPLAIN (ANALYZE, BUFFERS)
UPDATE orders SET processed_at = NOW()
WHERE processed_at IS NULL;
ROLLBACK;

-- WRONG: Reading only the top node as if it were the total cost
EXPLAIN (ANALYZE)
SELECT * FROM orders WHERE status = 'paid';
-- The top node includes child-node time, but child nodes show where time is spent

-- CORRECT: Inspect the slowest child nodes and their actual rows vs planned rows
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM orders WHERE status = 'paid';
-- Focus on nodes with high actual time, high buffer reads, or large row estimate errors
```

## Gotchas
- `EXPLAIN` shows the planner's estimated plan; `EXPLAIN ANALYZE` executes the query and reports actual timing.
- `BUFFERS` reports cache hits and disk reads, which is often more useful than wall-clock time alone.
- `EXPLAIN ANALYZE` can modify data; use a transaction and `ROLLBACK` for `INSERT`, `UPDATE`, or `DELETE`.
- A sequential scan is not automatically wrong; it can be optimal for small tables or broad filters.
- Large differences between estimated rows and actual rows often point to stale statistics or missing indexes.
- `ANALYZE` updates planner statistics; run it after large data changes or before judging plan quality.
- Planner settings such as `enable_seqscan` are useful for experiments but should not be left changed globally.

## Related
- db/postgres/query-optimization.md
- db/postgres/indexes.md
- db/postgres/transactions.md
