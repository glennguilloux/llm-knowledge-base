---
id: "db-postgres-window-functions"
title: "Window Functions in PostgreSQL"
language: "sql"
category: "db"
tags: ["sql", "postgresql", "window-functions", "analytics", "ranking"]
version: "14+"
retrieval_hint: "window function ROW_NUMBER RANK LAG LEAD OVER PARTITION BY"
last_verified: "2026-05-22"
confidence: "high"
---

# Window Functions in PostgreSQL

## When to Use
- Ranking rows within groups (top N per category)
- Computing running totals, moving averages, or cumulative sums
- Comparing a row to adjacent rows (previous/next values)
- Assigning sequential numbers to rows
- Percentile and distribution calculations

## Standard Pattern

```sql
-- ROW_NUMBER: unique sequential integer per partition
SELECT
    department,
    employee_name,
    salary,
    ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) AS dept_rank
FROM employees;

-- RANK: same rank for ties, gaps after ties
SELECT
    department,
    employee_name,
    salary,
    RANK() OVER (PARTITION BY department ORDER BY salary DESC) AS dept_rank
FROM employees;

-- DENSE_RANK: same rank for ties, no gaps
SELECT
    department,
    employee_name,
    salary,
    DENSE_RANK() OVER (PARTITION BY department ORDER BY salary DESC) AS dept_rank
FROM employees;

-- LAG / LEAD: access previous/next row values
SELECT
    order_date,
    amount,
    LAG(amount, 1) OVER (ORDER BY order_date) AS prev_amount,
    LEAD(amount, 1) OVER (ORDER BY order_date) AS next_amount,
    amount - LAG(amount, 1) OVER (ORDER BY order_date) AS change
FROM orders;

-- FIRST_VALUE / LAST_VALUE
SELECT
    department,
    employee_name,
    salary,
    FIRST_VALUE(employee_name) OVER (
        PARTITION BY department ORDER BY salary DESC
    ) AS highest_paid
FROM employees;

-- NTILE: divide rows into N equal groups
SELECT
    student_name,
    score,
    NTILE(4) OVER (ORDER BY score DESC) AS quartile
FROM students;

-- Running total with frame clause
SELECT
    order_date,
    amount,
    SUM(amount) OVER (
        ORDER BY order_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_total
FROM orders;

-- Moving average (3-row window)
SELECT
    order_date,
    amount,
    AVG(amount) OVER (
        ORDER BY order_date
        ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING
    ) AS moving_avg_3
FROM orders;

-- Named window specification
SELECT
    department,
    employee_name,
    salary,
    RANK() OVER dept_window AS dept_rank,
    SUM(salary) OVER dept_window AS cumulative_salary
FROM employees
WINDOW dept_window AS (PARTITION BY department ORDER BY salary DESC);
```

## Common Mistakes

```sql
-- WRONG: Using GROUP BY when you need row-level detail
SELECT department, MAX(salary) FROM employees GROUP BY department;
-- Loses individual employee rows

-- CORRECT: Window function preserves all rows
SELECT department, employee_name, salary,
    MAX(salary) OVER (PARTITION BY department) AS dept_max_salary
FROM employees;

-- WRONG: Forgetting ORDER BY in window (undefined row order)
SELECT amount, SUM(amount) OVER () AS running_total FROM orders;
-- running_total is the same for every row (total sum)

-- CORRECT: Always specify ORDER BY for cumulative functions
SELECT amount,
    SUM(amount) OVER (ORDER BY order_date) AS running_total
FROM orders;

-- WRONG: LAST_VALUE without frame (default frame is ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
SELECT department, employee_name, salary,
    LAST_VALUE(employee_name) OVER (ORDER BY salary DESC) AS lowest_paid
FROM employees;
-- Always returns current row, not the actual last value

-- CORRECT: Specify frame to include all rows
SELECT department, employee_name, salary,
    LAST_VALUE(employee_name) OVER (
        ORDER BY salary DESC
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) AS lowest_paid
FROM employees;

-- WRONG: Filtering on window function result in WHERE
SELECT *, ROW_NUMBER() OVER (ORDER BY id) AS rn FROM employees WHERE rn > 5;
-- ERROR: column "rn" does not exist (WHERE executes before window functions)

-- CORRECT: Use a subquery or CTE
SELECT * FROM (
    SELECT *, ROW_NUMBER() OVER (ORDER BY id) AS rn FROM employees
) sub WHERE rn > 5;
```

## Gotchas
- Window functions execute AFTER `WHERE`, `GROUP BY`, and `HAVING` — filter rows first
- Default frame is `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` — not the same as `ROWS`
- `RANGE` mode groups peers (same ORDER BY value) together; `ROWS` treats each row individually
- `RANK()` skips numbers after ties (1, 2, 2, 4); `DENSE_RANK()` does not (1, 2, 2, 3)
- `ROW_NUMBER()` is non-deterministic for ties — add a tiebreaker column to `ORDER BY`
- `LAG`/`LEAD` return `NULL` when there is no previous/next row — use default value parameter
- `PARTITION BY` is optional — without it, the window is the entire result set
- Window functions cannot appear in `WHERE` or `GROUP BY` — wrap in a subquery
- Multiple window functions with the same window can share a `WINDOW` clause for clarity
- `NTILE` distributes rows as evenly as possible — larger groups come first

## Related
- db/postgres/ctes.md
- db/postgres/query-optimization.md
- db/postgres/indexing-strategies.md
