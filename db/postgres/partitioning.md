---
id: "db-postgres-partitioning"
title: "Declarative Partitioning, Pruning, and Maintenance"
language: "sql"
category: "db"
tags: ["sql", "postgresql", "partitioning", "partition-pruning", "range-partition", "list-partition", "hash-partition", "maintenance", "indexes"]
version: "14+"
retrieval_hint: "PostgreSQL declarative partitioning partition pruning range list hash partition key maintenance indexes constraints"
last_verified: "2026-06-20"
confidence: "medium"
---

# Declarative Partitioning, Pruning, and Maintenance

## When to Use
- Splitting very large append-heavy tables by time, tenant, region, or status.
- Improving query performance when predicates consistently include the partition key.
- Archiving or dropping old data by detaching whole partitions instead of deleting many rows.
- Reducing index bloat and vacuum work on inactive historical partitions.
- Isolating noisy tenants or high-volume categories into separate physical partitions.

## Standard Pattern

```sql
-- RANGE partitioning is a common fit for time-series or retention windows.
CREATE TABLE orders (
    order_id bigint NOT NULL,
    customer_id bigint NOT NULL,
    created_at timestamptz NOT NULL,
    status text NOT NULL,
    amount numeric(12, 2) NOT NULL
) PARTITION BY RANGE (created_at);

CREATE TABLE orders_2026_06
    PARTITION OF orders
    FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');

CREATE TABLE orders_2026_07
    PARTITION OF orders
    FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');

-- LIST partitioning isolates stable categories or tenants.
CREATE TABLE events_by_type (
    event_id bigint NOT NULL,
    event_type text NOT NULL,
    payload jsonb NOT NULL,
    created_at timestamptz NOT NULL
) PARTITION BY LIST (event_type);

CREATE TABLE events_clicks
    PARTITION OF events_by_type
    FOR VALUES IN ('click', 'impression');

CREATE TABLE events_purchases
    PARTITION OF events_by_type
    FOR VALUES IN ('purchase', 'refund');

-- HASH partitioning spreads a high-cardinality key across fixed-size partitions.
CREATE TABLE tenant_events (
    tenant_id bigint NOT NULL,
    event_id bigint NOT NULL,
    created_at timestamptz NOT NULL
) PARTITION BY HASH (tenant_id);

CREATE TABLE tenant_events_p0
    PARTITION OF tenant_events
    FOR VALUES WITH (MODULUS 4, REMAINDER 0);

-- Queries that include the partition key can prune irrelevant partitions.
SELECT COUNT(*)
FROM orders
WHERE created_at >= DATE '2026-06-01'
  AND created_at < DATE '2026-07-01';

EXPLAIN (COSTS OFF)
SELECT *
FROM events_by_type
WHERE event_type = 'purchase';

-- Maintenance inspection: list child partitions and their bounds.
SELECT
    child.inhrelid::regclass AS partition_name,
    pg_get_expr(parent.relpartbound, child.inhrelid) AS partition_bound
FROM pg_inherits child
JOIN pg_class parent ON parent.oid = child.inhparent
WHERE parent.oid = 'orders'::regclass
ORDER BY partition_name;
```

## Common Mistakes

```sql
-- WRONG: Querying without the partition key prevents effective pruning.
SELECT COUNT(*)
FROM orders
WHERE status = 'paid';
-- PostgreSQL may need to scan every orders_* partition.

-- CORRECT: Include a predicate on the partition key.
SELECT COUNT(*)
FROM orders
WHERE created_at >= DATE '2026-06-01'
  AND created_at < DATE '2026-07-01'
  AND status = 'paid';
```

```sql
-- WRONG: Applying a function to the partition key can block pruning.
SELECT COUNT(*)
FROM orders
WHERE DATE_TRUNC('month', created_at) = DATE '2026-06-01';

-- CORRECT: Use a sargable range predicate.
SELECT COUNT(*)
FROM orders
WHERE created_at >= TIMESTAMP '2026-06-01'
  AND created_at < TIMESTAMP '2026-07-01';
```

```sql
-- WRONG: Choosing a high-churn partition key creates hot partitions.
-- Partitioning every hour for a write-heavy table can concentrate all writes in one partition.

-- CORRECT: Choose a stable key that balances pruning and write distribution.
-- For time-series writes, daily or monthly partitions often reduce hotspot risk.
CREATE TABLE orders_2026_06
    PARTITION OF orders
    FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');
```

```sql
-- WRONG: Letting the default partition absorb unknown values forever.
CREATE TABLE events_default
    PARTITION OF events_by_type
    DEFAULT;
-- Over time this partition can become large and slow to manage.

-- CORRECT: Monitor the default partition and create explicit partitions for recurring values.
SELECT
    relname,
    n_live_tup,
    last_vacuum
FROM pg_stat_user_tables
WHERE relname = 'events_default';
```

```sql
-- WRONG: Assuming every unique constraint works like an unpartitioned table.
ALTER TABLE orders ADD CONSTRAINT orders_order_id_unique UNIQUE (order_id);
-- Fails unless the unique constraint includes the partition key.

-- CORRECT: Include the partition key in unique constraints on partitioned tables.
ALTER TABLE orders
    ADD CONSTRAINT orders_created_order_unique UNIQUE (created_at, order_id);
```

## Gotchas
- Partition pruning only helps when predicates can be matched to partition bounds; functions, casts, or expressions on the partition key can prevent pruning.
- Too many partitions increase planner overhead, catalog size, and maintenance work; choose a partition count that matches query and retention patterns.
- A default partition is useful for safety, but it must be monitored because unexpected values can hide data-quality problems.
- Unique and primary-key constraints on partitioned tables must include the partition key in PostgreSQL.
- Indexes created on the partitioned parent propagate to new partitions, but existing partitions may need indexes added explicitly.
- Detaching old partitions is usually cheaper than deleting old rows, but plan for locks, replication, and backup retention.
- HASH partitioning requires choosing a modulus carefully; changing it later usually requires rebuilding partitions and moving data.

## Related
- db/postgres/indexes.md
- db/postgres/query-optimization.md
- db/postgres/transactions.md
