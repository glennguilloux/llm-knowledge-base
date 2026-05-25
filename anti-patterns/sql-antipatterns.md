---
id: "anti-patterns-sql"
title: "SQL Anti-Patterns"
language: "sql"
category: "anti-patterns"
subcategory: "database"
tags: ["sql", "anti-pattern", "select-star", "n-plus-one", "index", "performance"]
version: ""
retrieval_hint: "SQL anti-pattern SELECT * N+1 implicit casting no index foreign key"
last_verified: "2026-05-24"
confidence: "high"
---

# SQL Anti-Patterns

## When to Use
- Database query optimization
- Schema design review
- Preventing production performance issues
- Code review for SQL-heavy applications

## Standard Pattern

See Common Mistakes below for WRONG/CORRECT code pairs.

## Common Mistakes

```sql
-- WRONG: SELECT * (fetches all columns, breaks on schema changes)
SELECT * FROM users WHERE active = true;

-- CORRECT: Select only needed columns
SELECT id, name, email FROM users WHERE active = true;

-- WRONG: No index on foreign key (slow JOINs)
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),  -- No index!
    total DECIMAL
);
SELECT * FROM orders o JOIN users u ON o.user_id = u.id;  -- Full table scan

-- CORRECT: Index foreign keys
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    total DECIMAL
);
CREATE INDEX idx_orders_user_id ON orders(user_id);

-- WRONG: Implicit type casting (prevents index usage)
SELECT * FROM users WHERE age::text = '25';  -- Cast defeats index

-- CORRECT: Compare matching types
SELECT * FROM users WHERE age = 25;

-- WRONG: N+1 query pattern (in application code)
-- users = SELECT * FROM users
-- for user in users:
--     orders = SELECT * FROM orders WHERE user_id = user.id  -- N queries!

-- CORRECT: JOIN or IN clause
SELECT u.*, o.*
FROM users u
LEFT JOIN orders o ON o.user_id = u.id;

-- Or with IN:
SELECT * FROM orders WHERE user_id IN (SELECT id FROM users WHERE active = true);

-- WRONG: LIKE with leading wildcard (can't use index)
SELECT * FROM users WHERE name LIKE '%alice%';  -- Full table scan

-- CORRECT: Use full-text search or prefix match
SELECT * FROM users WHERE name LIKE 'alice%';  -- Can use index
-- Or: SELECT * FROM users WHERE to_tsvector('english', name) @@ to_tsquery('alice');

-- WRONG: No LIMIT on unbounded queries
SELECT * FROM orders ORDER BY created_at DESC;  -- Returns millions of rows

-- CORRECT: Always paginate
SELECT * FROM orders ORDER BY created_at DESC LIMIT 20 OFFSET 0;

-- WRONG: OR on different columns (slow)
SELECT * FROM users WHERE email = 'alice@test.com' OR name = 'Alice';

-- CORRECT: Use UNION for different indexes
SELECT * FROM users WHERE email = 'alice@test.com'
UNION
SELECT * FROM users WHERE name = 'Alice';
```

## Gotchas
- `SELECT *` fetches all columns — breaks when schema changes, wastes bandwidth
- Foreign keys need indexes — JOINs without indexes do full table scans
- Implicit type casting (`WHERE varchar_col = 123`) prevents index usage
- N+1 queries: use JOINs or batch queries instead of looping in application code
- `LIKE '%prefix%'` can't use B-tree indexes — use full-text search for text search
- Always use `LIMIT` for user-facing queries — unbounded results can OOM
- `OR` across different columns often can't use indexes — consider `UNION`
- `NOT IN (NULL)` returns empty — use `NOT EXISTS` or `IS NOT NULL`

## Related
- python/db/sqlalchemy-2.0/queries.md
- java/spring/spring-data/queries.md
- patterns/observability.md
