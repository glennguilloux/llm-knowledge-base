---
id: "db-postgres-indexes"
title: "PostgreSQL Index Strategies"
language: "multi"
category: "db"
subcategory: "performance"
tags: ["postgres", "index", "btree", "gin", "gist", "performance"]
version: "n/a"
retrieval_hint: "PostgreSQL index btree gin gist performance query"
last_verified: "2026-05-24"
confidence: "high"
---

# PostgreSQL Index Strategies

## When to Use
- Speeding up queries on large tables
- Filtering and sorting optimization
- Full-text search
- JSON/JSONB queries

## Standard Pattern

```sql
-- B-tree index (default, most common)
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at DESC);

-- Composite index (order matters!)
CREATE INDEX idx_orders_user_status ON orders(user_id, status);

-- Partial index (index only subset of rows)
CREATE INDEX idx_active_users ON users(email) WHERE is_active = true;

-- Unique index
CREATE UNIQUE INDEX idx_users_email_unique ON users(email);

-- GIN index for full-text search
CREATE INDEX idx_posts_content_fts ON posts USING gin(to_tsvector('english', content));

-- GIN index for JSONB
CREATE INDEX idx_metadata ON items USING gin(metadata);

-- GIN index for arrays
CREATE INDEX idx_tags ON posts USING gin(tags);

-- GiST index for geometric/range data
CREATE INDEX idx_locations ON places USING gist(location);

-- Concurrent index creation (non-blocking)
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);

-- Expression index
CREATE INDEX idx_users_lower_email ON users(LOWER(email));

-- Covering index (includes extra columns)
CREATE INDEX idx_orders_user ON orders(user_id) INCLUDE (total, status);
```

## Common Mistakes

```sql
-- WRONG: Index on low-cardinality column
CREATE INDEX idx_users_gender ON users(gender);  -- Only 2-3 values!

-- CORRECT: Composite index with high-cardinality column
CREATE INDEX idx_users_gender_email ON users(gender, email);

-- WRONG: Wrong index order for query pattern
CREATE INDEX idx_orders_status_user ON orders(status, user_id);
-- Query: SELECT * FROM orders WHERE user_id = 123;
-- Index not used!

-- CORRECT: Match index order to query pattern
CREATE INDEX idx_orders_user_status ON orders(user_id, status);

-- WRONG: Over-indexing
CREATE INDEX idx1 ON users(email);
CREATE INDEX idx2 ON users(email, name);
CREATE INDEX idx3 ON users(email, name, age);
-- idx1 is redundant if idx2 exists!

-- CORRECT: Consolidate indexes
CREATE INDEX idx_users_email_name_age ON users(email, name, age);
```

## Gotchas
- B-tree is default and works for equality and range queries
- GIN is best for full-text search, JSONB, and arrays
- `CONCURRENTLY` can't run inside a transaction
- Index order matters for composite indexes
- Use `EXPLAIN ANALYZE` to verify index usage
- Partial indexes are smaller and faster
- `INCLUDE` columns avoid table lookups (covering index)

## Related
- db/postgres/json-queries.md
- db/postgres/full-text-search.md
- db/postgres/migrations.md
