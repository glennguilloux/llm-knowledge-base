---
id: "antipatterns-database"
title: "Database Anti-Patterns: SELECT *, N+1 Queries, and Missing Indexes"
language: "multi"
category: "anti-patterns"
tags: ["antipatterns", "database", "sql", "select-star", "n-plus-one", "indexes", "connection-pooling"]
version: "n/a"
retrieval_hint: "database antipatterns SELECT implicit type casting no indexes on FK string concatenation for queries not using transactions ignoring connection pooling"
last_verified: "2026-05-24"
confidence: "high"
---

# Database Anti-Patterns: SELECT *, N+1 Queries, and Missing Indexes

## When to Use
- Reviewing database access code
- Training LLMs to avoid common SQL mistakes
- Performance optimization
- Code review checklist for database operations

## Standard Pattern

```sql
-- WRONG: SELECT * (retrieves all columns, wastes bandwidth)
SELECT * FROM users WHERE id = 1;

-- CORRECT: Select only needed columns
SELECT id, name, email FROM users WHERE id = 1;

-- WRONG: N+1 query problem (application code)
-- for user in users:
--     orders = db.query("SELECT * FROM orders WHERE user_id = ?", user.id)
-- One query for users + N queries for orders = N+1 queries!

-- CORRECT: Use JOIN or IN clause
SELECT u.id, u.name, o.id AS order_id, o.total
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.active = 1;

-- Or fetch in two queries:
-- users = db.query("SELECT * FROM users WHERE active = 1")
-- user_ids = [u.id for u in users]
-- orders = db.query("SELECT * FROM orders WHERE user_id IN (?)", user_ids)

-- WRONG: String concatenation for SQL (SQL injection!)
-- query = "SELECT * FROM users WHERE name = '" + user_input + "'"

-- CORRECT: Use parameterized queries
-- query = "SELECT * FROM users WHERE name = ?"
-- cursor.execute(query, (user_input,))

-- WRONG: No index on foreign key
CREATE TABLE orders (
    id INT PRIMARY KEY,
    user_id INT,  -- No index!
    total DECIMAL(10,2)
);

-- CORRECT: Index foreign keys
CREATE TABLE orders (
    id INT PRIMARY KEY,
    user_id INT,
    total DECIMAL(10,2),
    INDEX idx_user_id (user_id)
);

-- WRONG: Implicit type casting (prevents index usage)
SELECT * FROM users WHERE phone_number = 1234567890;
-- phone_number is VARCHAR, comparing to INT causes full table scan

-- CORRECT: Match types
SELECT * FROM users WHERE phone_number = '1234567890';

-- WRONG: Not using transactions for related operations
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
-- If this fails, the second query runs without the first!
UPDATE accounts SET balance = balance + 100 WHERE id = 2;

-- CORRECT: Use transactions
BEGIN TRANSACTION;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;

-- WRONG: Ignoring connection pooling
-- Creating new connection for every query!

-- CORRECT: Use connection pooling
-- Python: psycopg2.pool, SQLAlchemy pool
-- Java: HikariCP
-- Node.js: pg-pool

-- WRONG: Fetching all rows into memory
SELECT * FROM large_table;  -- Millions of rows!

-- CORRECT: Use pagination
SELECT * FROM large_table ORDER BY id LIMIT 100 OFFSET 0;
-- Or use keyset pagination for better performance:
SELECT * FROM large_table WHERE id > last_id ORDER BY id LIMIT 100;
```

## Common Mistakes
- SELECT * — retrieves all columns, wastes bandwidth, breaks when schema changes
- N+1 query problem — one query for the list plus N queries for related data
- String concatenation for SQL — SQL injection vulnerability, use parameterized queries
- No indexes on foreign keys — slow joins, full table scans
- Implicit type casting — prevents index usage, causes full table scans
- Not using transactions — related operations may partially succeed, corrupting data
- Ignoring connection pooling — creating connections is expensive, pool and reuse
- Fetching all rows — loads entire table into memory, use pagination

## Gotchas
- `SELECT *` breaks when columns are added/removed. Always specify columns explicitly.
- N+1 queries are the #1 performance problem in ORM-based applications. Use eager loading.
- Foreign keys should ALWAYS have indexes. Most databases don't auto-index FKs.
- Parameterized queries prevent SQL injection AND allow query plan caching.
- Connection pooling is essential for performance. Creating connections is expensive.
- Keyset pagination (`WHERE id > last_id`) is faster than OFFSET for large datasets.
- Implicit type casting on indexed columns prevents index usage (full table scan).
- Always use transactions for operations that must succeed or fail together.
- `EXPLAIN ANALYZE` your queries to understand performance characteristics.

## Related
- db/postgres/json-queries.md
- anti-patterns/api-antipatterns.md
- anti-patterns/testing-antipatterns.md
