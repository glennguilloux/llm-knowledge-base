---
id: "db-postgres-indexing-strategies"
title: "Indexing Strategies in PostgreSQL"
language: "sql"
category: "db"
tags: ["sql", "postgresql", "index", "btree", "gin", "gist", "performance"]
version: "14+"
retrieval_hint: "index btree gin gist partial index covering index EXPLAIN"
last_verified: "2026-05-24"
confidence: "high"
---

# Indexing Strategies in PostgreSQL

## When to Use
- Speeding up queries on large tables (millions of rows)
- Optimizing WHERE, JOIN, and ORDER BY clauses
- Supporting uniqueness constraints
- Full-text search and JSONB queries

## Standard Pattern

```sql
-- B-tree index (default, most common)
-- Best for: equality, range queries, sorting, pattern matching (LIKE 'foo%')
CREATE INDEX idx_users_email ON users (email);
CREATE INDEX idx_orders_date ON orders (order_date DESC);

-- Composite index (multi-column)
-- Column order matters: leftmost prefix is used
CREATE INDEX idx_orders_user_date ON orders (user_id, order_date DESC);
-- Used by: WHERE user_id = ?, WHERE user_id = ? AND order_date > ?
-- NOT used by: WHERE order_date > ? (missing leftmost column)

-- Partial index (index only matching rows)
-- Smaller index, faster updates
CREATE INDEX idx_active_users ON users (email) WHERE status = 'active';
-- Only indexes active users — smaller and faster

-- Covering index (INCLUDE columns)
-- Index-only scan — no table access needed
CREATE INDEX idx_orders_covering ON orders (user_id) INCLUDE (amount, status);
-- SELECT amount, status FROM orders WHERE user_id = ? uses index-only scan

-- GIN index (Generalized Inverted Index)
-- Best for: full-text search, JSONB, arrays, hstore
CREATE INDEX idx_docs_search ON documents USING GIN (to_tsvector('english', content));
CREATE INDEX idx_data_jsonb ON events USING GIN (metadata);
-- Supports: @>, ?, ?|, ?& operators

-- GiST index (Generalized Search Tree)
-- Best for: geometric data, range types, full-text search (alternative to GIN)
CREATE INDEX idx_locations_geo ON places USING GST (location);
CREATE INDEX idx_ranges ON reservations USING GIST (during);

-- BRIN index (Block Range Index)
-- Best for: naturally ordered data (timestamps, sequences), very large tables
CREATE INDEX idx_logs_created ON logs USING BRIN (created_at);
-- Tiny index size, great for append-only tables

-- Unique index
CREATE UNIQUE INDEX idx_users_email_unique ON users (email);

-- Expression index (functional index)
CREATE INDEX idx_users_lower_email ON users (LOWER(email));
-- Supports: WHERE LOWER(email) = 'test@example.com'

-- Check index usage
EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM users WHERE email = 'test@example.com';

-- List indexes on a table
SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'users';

-- Index size
SELECT indexname, pg_size_pretty(pg_relation_size(indexname::regclass))
FROM pg_indexes WHERE tablename = 'users';
```

## Common Mistakes

```sql
-- WRONG: Indexing every column (write overhead)
CREATE INDEX idx_a ON t (a);
CREATE INDEX idx_b ON t (b);
CREATE INDEX idx_c ON t (c);
-- Each INSERT/UPDATE must update all indexes

-- CORRECT: Index columns used in WHERE, JOIN, ORDER BY
-- Analyze query patterns first with pg_stat_statements

-- WRONG: Wrong column order in composite index
CREATE INDEX idx ON orders (order_date, user_id);
-- Not used by: SELECT * FROM orders WHERE user_id = 123;

-- CORRECT: Most selective / most-queried column first
CREATE INDEX idx ON orders (user_id, order_date);
-- Used by both: WHERE user_id = ? and WHERE user_id = ? AND order_date > ?

-- WRONG: Not using EXPLAIN ANALYZE
-- Assume an index is needed without checking

-- CORRECT: Always verify with EXPLAIN
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM orders WHERE user_id = 123 AND order_date > '2024-01-01';
-- Look for: Index Scan vs Seq Scan, actual rows, planning time

-- WRONG: Index on small table
CREATE INDEX idx ON countries (name);  -- 200 rows — SeqScan is faster

-- CORRECT: Only index tables with significant row counts
-- Rule of thumb: >10,000 rows for B-tree

-- WRONG: Using GIN for simple equality
CREATE INDEX idx ON users USING GIN (email);  -- Overkill

-- CORRECT: Use B-tree for equality/range, GIN for full-text/JSONB/arrays

-- WRONG: Ignoring index bloat
-- Indexes fragment over time, especially on frequently-updated tables

-- CORRECT: REINDEX or pg_repack periodically
REINDEX INDEX idx_users_email;
```

## Gotchas
- Indexes speed up reads but slow down writes (INSERT/UPDATE/DELETE must maintain indexes)
- B-tree is the default and best for 90% of use cases — start here
- Composite index only works if the query uses the leftmost prefix columns
- Partial indexes are smaller and faster — use when queries always filter on the same condition
- Covering indexes enable index-only scans — no heap access needed
- GIN indexes are best for multi-value columns (arrays, JSONB, full-text)
- BRIN indexes are tiny but only work well on naturally ordered data
- `EXPLAIN (ANALYZE, BUFFERS)` shows actual execution time and buffer usage
- `pg_stat_user_indexes` shows which indexes are used and how often
- Unused indexes waste disk space and slow writes — drop them with `DROP INDEX`
- Index creation acquires a lock — use `CREATE INDEX CONCURRENTLY` in production

## Real-World Example

### E-Commerce Schema with Strategic Indexes and Query Plans

```sql
-- Schema with proper indexes for an e-commerce app
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE orders (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    total_cents INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE order_items (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES orders(id),
    product_id BIGINT NOT NULL,
    quantity INTEGER NOT NULL,
    price_cents INTEGER NOT NULL
);

-- Strategic indexes
CREATE INDEX CONCURRENTLY idx_orders_user_created
    ON orders(user_id, created_at DESC);

CREATE INDEX CONCURRENTLY idx_orders_status_created
    ON orders(status, created_at DESC)
    WHERE status IN ('pending', 'processing');

CREATE INDEX CONCURRENTLY idx_order_items_order
    ON order_items(order_id);

-- Common query: recent orders for a user (uses idx_orders_user_created)
EXPLAIN ANALYZE
SELECT id, status, total_cents, created_at
FROM orders
WHERE user_id = 123
ORDER BY created_at DESC
LIMIT 20;

-- Common query: pending orders for admin dashboard (partial index)
EXPLAIN ANALYZE
SELECT o.id, u.email, o.total_cents, o.created_at
FROM orders o
JOIN users u ON u.id = o.user_id
WHERE o.status = 'pending'
ORDER BY o.created_at ASC
LIMIT 50;

-- Composite covering index for order detail page
CREATE INDEX CONCURRENTLY idx_order_items_cover
    ON order_items(order_id)
    INCLUDE (product_id, quantity, price_cents);
```

## Related
- db/postgres/query-optimization.md
- db/postgres/json-advanced.md
- db/postgres/window-functions.md
