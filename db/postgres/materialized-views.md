---
id: "db-postgres-materialized-views"
title: "Materialized Views for Query Caching"
language: "sql"
category: "db"
subcategory: "postgres"
tags: ["sql", "postgresql", "materialized-view", "refresh", "query-cache", "summary", "reporting", "precompute"]
version: "14+"
retrieval_hint: "PostgreSQL materialized view refresh concurrently summary query cache reporting precomputed aggregate"
last_verified: "2026-05-24"
confidence: "medium"
---

# Materialized Views for Query Caching

## When to Use
- Precomputing expensive aggregates for dashboards, reports, or analytics pages
- Caching joins across large tables when exact real-time freshness is not required
- Reducing repeated work for read-heavy queries with stable summary windows
- Supporting offline or delayed reporting where stale data for minutes or hours is acceptable
- Materializing complex filters, ranking, or text-search vectors for faster reads

## Standard Pattern

```sql
-- Create a materialized summary for reporting
CREATE MATERIALIZED VIEW daily_order_summary AS
SELECT
    DATE_TRUNC('day', created_at)::date AS order_date,
    status,
    COUNT(*) AS order_count,
    SUM(total_amount) AS revenue,
    AVG(total_amount) AS avg_order_amount
FROM orders
GROUP BY 1, 2
WITH DATA;

-- Query the precomputed result
SELECT *
FROM daily_order_summary
WHERE order_date >= DATE '2026-01-01'
ORDER BY order_date, status;

-- Add an index to speed up the reporting query
CREATE INDEX idx_daily_order_summary_date_status
ON daily_order_summary (order_date, status);

-- Refresh after source data changes; readers may be blocked during refresh
REFRESH MATERIALIZED VIEW daily_order_summary;

-- Create a unique index to enable concurrent refresh
CREATE UNIQUE INDEX idx_daily_order_summary_unique
ON daily_order_summary (order_date, status);

-- Concurrent refresh avoids blocking readers, but requires a unique index
REFRESH MATERIALIZED VIEW CONCURRENTLY daily_order_summary;

-- Schedule refresh around low-traffic periods from application or job scheduler logic
-- REFRESH MATERIALIZED VIEW daily_order_summary;
```

## Common Mistakes

```sql
-- WRONG: Expecting a materialized view to stay current automatically
SELECT * FROM daily_order_summary;
-- The view contains data from the last REFRESH, not the latest base-table rows

-- CORRECT: Refresh explicitly when the reporting window can tolerate stale data
REFRESH MATERIALIZED VIEW daily_order_summary;

-- WRONG: Using CONCURRENTLY without a unique index
REFRESH MATERIALIZED VIEW CONCURRENTLY daily_order_summary;
-- ERROR: cannot refresh materialized view "daily_order_summary" concurrently because it does not have a unique index

-- CORRECT: Add a unique index that covers every row before concurrent refresh
CREATE UNIQUE INDEX idx_daily_order_summary_unique
ON daily_order_summary (order_date, status);
REFRESH MATERIALIZED VIEW CONCURRENTLY daily_order_summary;

-- WRONG: Refreshing a large materialized view on every write
REFRESH MATERIALIZED VIEW daily_order_summary;
-- Frequent refresh can cost more than the original query, especially for large summaries

-- CORRECT: Refresh on a schedule or when a batch load completes
-- Application/job logic:
-- after nightly load finishes, run REFRESH MATERIALIZED VIEW daily_order_summary;

-- WRONG: Using a non-unique index for CONCURRENTLY
CREATE INDEX idx_daily_order_summary_date ON daily_order_summary (order_date);
REFRESH MATERIALIZED VIEW CONCURRENTLY daily_order_summary;
-- Still fails: the index must be unique and contain enough columns to identify every row

-- CORRECT: Use a unique index and then refresh concurrently
CREATE UNIQUE INDEX idx_daily_order_summary_unique
ON daily_order_summary (order_date, status);
REFRESH MATERIALIZED VIEW CONCURRENTLY daily_order_summary;
```

## Gotchas
- Materialized views store query results on disk; they do not automatically follow base-table changes.
- `REFRESH MATERIALIZED VIEW` can block readers; `REFRESH MATERIALIZED VIEW CONCURRENTLY` avoids reader blocking but requires a unique index.
- `CONCURRENTLY` cannot be combined with `WITH NO DATA` in the initial `CREATE MATERIALIZED VIEW` statement.
- Choose refresh frequency based on freshness requirements, write volume, and refresh duration.
- Index the materialized view for the reporting predicates and sort keys you actually query.
- Large materialized views can consume significant storage and increase backup size.
- If the defining query changes, recreate or replace the materialized view carefully because existing data remains from the old definition until refresh.

## Related
- db/postgres/query-optimization.md
- db/postgres/ctes.md
- db/postgres/indexes.md
