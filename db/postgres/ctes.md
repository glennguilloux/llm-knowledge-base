---
id: "db-postgres-ctes"
title: "Common Table Expressions (CTEs)"
language: "sql"
category: "db"
tags: ["sql", "postgresql", "cte", "with-clause", "recursive", "readability"]
version: "14+"
retrieval_hint: "CTE WITH clause recursive query common table expression"
last_verified: "2026-05-24"
confidence: "high"
---

# Common Table Expressions (CTEs)

## When to Use
- Breaking complex queries into readable, logical steps
- Referencing the same subquery multiple times
- Recursive queries (hierarchical data, graph traversal)
- Replacing deeply nested subqueries for readability

## Standard Pattern

```sql
-- Basic CTE: improve readability
WITH active_users AS (
    SELECT id, name, email
    FROM users
    WHERE status = 'active'
    AND last_login > NOW() - INTERVAL '30 days'
)
SELECT u.name, COUNT(o.id) AS order_count
FROM active_users u
JOIN orders o ON o.user_id = u.id
GROUP BY u.name;

-- Multiple CTEs: chain logic
WITH monthly_revenue AS (
    SELECT
        DATE_TRUNC('month', order_date) AS month,
        SUM(amount) AS revenue
    FROM orders
    GROUP BY 1
),
revenue_with_growth AS (
    SELECT
        month,
        revenue,
        LAG(revenue) OVER (ORDER BY month) AS prev_month_revenue
    FROM monthly_revenue
)
SELECT
    month,
    revenue,
    prev_month_revenue,
    ROUND((revenue - prev_month_revenue) / prev_month_revenue * 100, 2) AS growth_pct
FROM revenue_with_growth
ORDER BY month;

-- CTE vs subquery: CTE is reusable
-- Without CTE (duplicate subquery):
SELECT * FROM (SELECT * FROM active_users) a JOIN orders o ON o.user_id = a.id;
SELECT * FROM (SELECT * FROM active_users) a JOIN products p ON p.seller_id = a.id;

-- With CTE (defined once):
WITH active AS (SELECT * FROM active_users WHERE status = 'active')
SELECT * FROM active a JOIN orders o ON o.user_id = a.id;
SELECT * FROM active a JOIN products p ON p.seller_id = a.id;

-- Data-modifying CTE (PostgreSQL-specific)
WITH deleted AS (
    DELETE FROM sessions WHERE expires_at < NOW()
    RETURNING id
)
SELECT COUNT(*) AS deleted_sessions FROM deleted;

-- Upsert with CTE
WITH upserted AS (
    INSERT INTO user_stats (user_id, login_count)
    VALUES (42, 1)
    ON CONFLICT (user_id)
    DO UPDATE SET login_count = user_stats.login_count + 1
    RETURNING *
)
SELECT * FROM upserted;

-- CTE for data generation
WITH RECURSIVE dates AS (
    SELECT '2024-01-01'::DATE AS date
    UNION ALL
    SELECT date + 1 FROM dates WHERE date < '2024-12-31'
)
SELECT date FROM dates;
```

## Common Mistakes

```sql
-- WRONG: Using CTE when a simple subquery suffices (overhead)
WITH single_use AS (
    SELECT COUNT(*) FROM orders
)
SELECT * FROM single_use;
-- Just write: SELECT COUNT(*) FROM orders;

-- CORRECT: Use CTEs for multi-use or readability
WITH order_stats AS (
    SELECT user_id, COUNT(*) AS cnt, SUM(amount) AS total
    FROM orders GROUP BY user_id
)
SELECT u.name, os.cnt, os.total
FROM users u JOIN order_stats os ON os.user_id = u.id;

-- WRONG: Recursive CTE without termination (infinite loop)
WITH RECURSIVE chain AS (
    SELECT id, parent_id FROM categories WHERE id = 1
    UNION ALL
    SELECT c.id, c.parent_id FROM categories c
    JOIN chain ch ON c.id = ch.parent_id
    -- Missing WHERE to stop recursion
)
SELECT * FROM chain;

-- CORRECT: Always include a termination condition
WITH RECURSIVE chain AS (
    SELECT id, parent_id, 1 AS depth FROM categories WHERE id = 1
    UNION ALL
    SELECT c.id, c.parent_id, ch.depth + 1
    FROM categories c
    JOIN chain ch ON c.id = ch.parent_id
    WHERE ch.depth < 10  -- Termination condition
)
SELECT * FROM chain;

-- WRONG: Assuming CTE is always optimized (pre-PostgreSQL 12)
-- In PG 11 and earlier, CTEs are optimization fences (always materialized)
WITH expensive AS (
    SELECT * FROM large_table WHERE complex_condition
)
SELECT * FROM expensive WHERE simple_filter;
-- The simple_filter is NOT pushed into the CTE

-- CORRECT: In PG 12+, use MATERIALIZED / NOT MATERIALIZED hints
WITH expensive AS NOT MATERIALIZED (
    SELECT * FROM large_table WHERE complex_condition
)
SELECT * FROM expensive WHERE simple_filter;
-- simple_filter is now pushed down into the CTE
```

## Gotchas
- CTEs are named with the `WITH` clause and referenced like a table in the main query
- Each CTE can reference previously defined CTEs in the same `WITH` clause
- Recursive CTEs require `UNION ALL` between the base case and recursive case
- PostgreSQL 12+ no longer materializes CTEs by default — optimizer may inline them
- Use `MATERIALIZED` to force materialization (when the CTE is referenced multiple times)
- Data-modifying CTEs (`INSERT`/`UPDATE`/`DELETE` with `RETURNING`) are PostgreSQL-specific
- Recursive CTEs can infinite-loop — always include a depth limit or termination condition
- CTEs improve readability but don't automatically improve performance
- `LATERAL` joins can sometimes replace CTEs with better performance
- CTEs in PostgreSQL are executed every time they are referenced (unless materialized)

## Related
- db/postgres/window-functions.md
- db/postgres/query-optimization.md
- db/postgres/transactions.md
