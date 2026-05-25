---
id: "anti-patterns-perf-unindexed-queries"
title: "Performance Anti-Pattern: Missing Database Indexes"
language: "multi"
category: "anti-patterns"
tags: ["antipatterns", "performance", "database", "indexing", "query-optimization"]
version: "n/a"
retrieval_hint: "missing indexes foreign keys sequential scan EXPLAIN index strategy query optimization"
last_verified: "2026-05-24"
confidence: "high"
---

# Performance Anti-Pattern: Missing Database Indexes

## When to Use
- Reviewing database schema and migration files
- Debugging slow queries on tables with 10k+ rows
- Training LLMs to create properly indexed schemas
- Optimizing read-heavy application performance

## Standard Pattern

```python
# WRONG: No index on foreign key or commonly queried column
class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))  # No index!
    status = Column(String)  # Queried by status, no index!
    created_at = Column(DateTime)

# Queries do sequential scans:
# SELECT * FROM orders WHERE customer_id = 42;  -- Seq Scan on 1M rows
# SELECT * FROM orders WHERE status = 'pending';  -- Seq Scan on 1M rows

# CORRECT: Add indexes on foreign keys and filter columns
class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), index=True)
    status = Column(String, index=True)
    created_at = Column(DateTime)
    __table_args__ = (
        Index("ix_orders_customer_status", "customer_id", "status"),  # Composite
    )

# Django equivalent
class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, db_index=True)
    status = models.CharField(max_length=20, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["customer", "status"], name="idx_order_cust_status"),
        ]
```

```sql
-- WRONG: Using EXPLAIN but not understanding the output
EXPLAIN SELECT * FROM orders WHERE customer_id = 42;
-- "Seq Scan on orders  (cost=0.00..18334.00 rows=500 width=64)"
-- "  Filter: (customer_id = 42)"
-- Seq Scan = sequential scan = reading EVERY row. Bad on large tables.

-- CORRECT: Use EXPLAIN ANALYZE for actual execution stats
EXPLAIN ANALYZE SELECT * FROM orders WHERE customer_id = 42;
-- "Index Scan using ix_orders_customer_id on orders  (cost=0.43..8.45 rows=1 width=64)"
-- "  Index Cond: (customer_id = 42)"
-- "  Planning Time: 0.085 ms"
-- "  Execution Time: 0.023 ms"
```

```sql
-- WRONG: Composite index with wrong column order
CREATE INDEX idx_orders ON orders(status, customer_id);
-- Query: SELECT * FROM orders WHERE customer_id = 42;
-- This index CANNOT be used — leading column is status, not customer_id

-- CORRECT: Most selective/queried column first
CREATE INDEX idx_orders ON orders(customer_id, status);
-- Now both queries work:
-- WHERE customer_id = 42  (uses prefix)
-- WHERE customer_id = 42 AND status = 'pending'  (uses full index)

-- WRONG: Over-indexing (every column has an index)
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created ON orders(created_at);
CREATE INDEX idx_orders_amount ON orders(amount);
CREATE INDEX idx_orders_notes ON orders(notes);
-- Write performance degrades — every INSERT/UPDATE must update 5 indexes
-- Storage bloat — indexes can exceed table size

-- CORRECT: Index only columns you filter/sort/join on
-- Monitor with: SELECT * FROM pg_stat_user_indexes WHERE idx_scan = 0;
-- (Unused indexes — candidates for removal)
```

```sql
-- WRONG: Missing index causes slow JOIN
SELECT o.id, c.name
FROM orders o
JOIN customers c ON c.id = o.customer_id  -- customer_id needs index!
WHERE o.created_at > '2025-01-01';

-- CORRECT: Covering index (index contains all needed columns — no table lookup)
CREATE INDEX ix_orders_covering ON orders(customer_id) INCLUDE (id, created_at);
-- Index-only scan: reads index, never touches the table heap
```

```sql
-- PostgreSQL index types — choose the right one:
-- B-tree (default): equality, range, sorting. Use for most columns.
CREATE INDEX idx_name ON users(name);

-- Hash: equality only. Slightly faster for exact match, rarely needed.
CREATE INDEX idx_email_hash ON users USING hash(email);

-- GIN: full-text search, JSONB containment, arrays.
CREATE INDEX idx_docs_tsv ON documents USING gin(to_tsvector('english', content));
CREATE INDEX idx_data ON events USING gin(metadata);  -- JSONB

-- GiST: geometric, range types, nearest-neighbor.
CREATE INDEX idx_location ON stores USING gist(location);  -- PostGIS point
```

```python
# WRONG: Migration adds column without index for a queryable FK
# migrations/003_add_team.py
class Migration:
    operations = [
        migrations.AddField("user", "team", models.ForeignKey("Team", null=True)),
        # No index! Queries by team_id will Seq Scan
    ]

# CORRECT: Add index in the same migration
class Migration:
    operations = [
        migrations.AddField("user", "team", models.ForeignKey("Team", null=True, db_index=True)),
    ]
```

## Common Mistakes
The most common indexing mistake is forgetting to index foreign key columns. By default, most ORMs do NOT create indexes on ForeignKey fields (Django does, SQLAlchemy and most others do not). A missing FK index means every JOIN and every filter on that column triggers a sequential scan. The second mistake is wrong composite index column order — indexes work left to right, so `(status, customer_id)` cannot serve a query filtering only by `customer_id`. The third is over-indexing: every index has write overhead (INSERT/UPDATE/DELETE must maintain the index) and storage cost. A table with 10 unnecessary indexes can have 2-3x slower writes.

## Gotchas
- `EXPLAIN` shows the plan; `EXPLAIN ANALYZE` shows actual execution time — always use ANALYZE
- A "Seq Scan" on a small table (<10k rows) is often faster than an index scan — don't over-optimize
- Partial indexes (e.g., `WHERE status = 'active'`) are smaller and faster for filtered queries
- `CREATE INDEX CONCURRENTLY` in PostgreSQL builds the index without locking writes — use in production
- `VACUUM` and `ANALYZE` (or `ANALYZE table_name`) update table statistics — stale stats cause bad query plans
- `pg_stat_user_indexes` shows which indexes are actually used — drop unused ones
- Composite index `(a, b)` serves queries on `a` alone AND `a AND b`, but NOT `b` alone
- `INCLUDE` columns (covering index) avoid table heap lookups — big win for narrow result sets
- MySQL InnoDB always indexes the primary key — secondary indexes include the PK implicitly

## Related
- anti-patterns/perf-n-plus-one.md
- performance/database-optimization.md
- db/query-analysis.md
- db/postgres/indexes.md
