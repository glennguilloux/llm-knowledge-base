---
id: "performance-database-indexing"
title: "Database Indexing Strategy"
language: "multi"
category: "performance"
tags: ["database", "indexing", "query-plan", "sql", "performance", "composite-index", "covering-index"]
version: "n/a"
retrieval_hint: "database indexing strategy query plan performance composite index covering index partial index explain analyze"
last_verified: "2026-06-20"
confidence: "medium"
---

# Database Indexing Strategy

## When to Use
- Designing indexes for read-heavy query patterns
- Improving slow lookups, joins, sorting, and filtering
- Reducing table scans for frequently accessed columns
- Supporting pagination, reporting filters, or tenant-scoped queries

## Standard Pattern

```sql
-- === Start with the query shape ===
-- SELECT id, status, created_at
-- FROM orders
-- WHERE tenant_id = :tenant_id
--   AND status = :status
-- ORDER BY created_at DESC
-- LIMIT :limit;

-- CORRECT: Composite index matching filter and sort order
CREATE INDEX idx_orders_tenant_status_created_at
ON orders (tenant_id, status, created_at DESC);
```

```sql
-- === Equality lookups and uniqueness ===
-- CORRECT: Unique index for identity lookup
CREATE UNIQUE INDEX idx_users_email_key
ON users (lower(email));

-- CORRECT: Partial index for active records
CREATE INDEX idx_active_users_email
ON users (email)
WHERE active = true;
```

```sql
-- === Covering index for hot read paths ===
-- CORRECT: Include columns needed by the query without making the key wider than necessary
CREATE INDEX idx_orders_covering
ON orders (tenant_id, created_at DESC)
INCLUDE (id, status);
```

```sql
-- === Verify with the database's plan tool ===
EXPLAIN ANALYZE
SELECT id, status, created_at
FROM orders
WHERE tenant_id = 'tenant-a'
  AND status = 'paid'
ORDER BY created_at DESC
LIMIT 10;
```

## Common Mistakes

```sql
-- WRONG: Adding indexes without matching real query patterns
CREATE INDEX idx_random_column ON users (favorite_color);

-- CORRECT: Index columns used by frequent filters, joins, and sorts
CREATE INDEX idx_orders_tenant_status_created_at
ON orders (tenant_id, status, created_at DESC);
```

```sql
-- WRONG: Creating one huge composite index for every column
CREATE INDEX idx_everything ON orders (
  tenant_id, status, created_at, user_id, total_amount,
  updated_at, currency, source, channel
);

-- CORRECT: Keep indexes narrow and query-specific
CREATE INDEX idx_orders_tenant_status_created_at
ON orders (tenant_id, status, created_at DESC);
```

```sql
-- WRONG: Expecting a composite index to help when the leading column is skipped
-- Query filters created_at only, but index starts with tenant_id
CREATE INDEX idx_orders_created_at_late ON orders (tenant_id, created_at);

-- CORRECT: Put the most selective or always-filtered column first for the query
CREATE INDEX idx_orders_created_at ON orders (created_at DESC);
```

```sql
-- WRONG: Forgetting that indexes slow writes
-- Every insert or update touching indexed columns also updates indexes

-- CORRECT: Balance read benefit against write cost and remove unused indexes
CREATE INDEX idx_orders_tenant_status_created_at
ON orders (tenant_id, status, created_at DESC);
```

## Gotchas
- Composite index order matters because databases can usually use a left prefix efficiently
- Partial indexes are useful when queries often target a stable subset of rows
- Covering indexes can reduce table lookups but make indexes wider and more expensive to maintain
- Functions in predicates need matching expression indexes or normalized columns to be useful
- Indexes do not replace good schema design, pagination, or query shape improvements
- Production plans can differ from local plans because data distribution and statistics differ

## Related
- performance/database-optimization.md
- performance/n-plus-one-prevention.md
- performance/connection-pooling.md
