---
id: "db-postgres-window-functions-advanced"
title: "Advanced Window Functions — Real-World Analytics Patterns"
language: "sql"
category: "db"
subcategory: "postgresql"
tags: ["sql", "postgresql", "window-functions", "analytics", "running-total", "moving-average", "gaps-and-islands", "sessionization"]
version: "14+"
retrieval_hint: "PostgreSQL advanced window functions gap detection island sessionization running total percentile"
last_verified: "2026-05-25"
confidence: "high"
---

# Advanced Window Functions — Real-World Analytics Patterns

## When to Use
- Detecting gaps in sequences (missing invoice numbers, dropped connections)
- Sessionizing event data (grouping activity into sessions by timeout)
- Computing running totals with reset conditions (e.g., per-month running total)
- Filling in missing dates with carry-forward values (last non-null carried forward)
- Lead/lag analysis across irregular intervals

## Standard Pattern

```sql
-- --- Gaps and Islands: Detect consecutive ranges ---
-- Given a table of check-ins, find consecutive date ranges per user
WITH numbered AS (
    SELECT
        user_id,
        checkin_date,
        checkin_date - ROW_NUMBER() OVER (
            PARTITION BY user_id ORDER BY checkin_date
        )::int AS grp
    FROM checkins
)
SELECT
    user_id,
    MIN(checkin_date) AS streak_start,
    MAX(checkin_date) AS streak_end,
    COUNT(*) AS days_in_streak
FROM numbered
GROUP BY user_id, grp
ORDER BY user_id, streak_start;

-- --- Sessionization: Group events by timeout (30 min gap) ---
WITH with_marker AS (
    SELECT
        user_id,
        event_time,
        event_type,
        CASE WHEN event_time - LAG(event_time) OVER (
            PARTITION BY user_id ORDER BY event_time
        ) > interval '30 minutes'
            THEN 1 ELSE 0
        END AS new_session
    FROM user_events
    WHERE user_id = 42
),
with_session AS (
    SELECT
        *,
        SUM(new_session) OVER (
            PARTITION BY user_id ORDER BY event_time
            ROWS UNBOUNDED PRECEDING
        ) AS session_id
    FROM with_marker
)
SELECT
    user_id,
    session_id,
    MIN(event_time) AS session_start,
    MAX(event_time) AS session_end,
    COUNT(*) AS events_in_session
FROM with_session
GROUP BY user_id, session_id
ORDER BY session_start;

-- --- Running total with monthly reset ---
SELECT
    date_trunc('month', order_date)::date AS month,
    order_date,
    amount,
    SUM(amount) OVER (
        PARTITION BY date_trunc('month', order_date)
        ORDER BY order_date
        ROWS UNBOUNDED PRECEDING
    ) AS running_total_this_month,
    SUM(amount) OVER (
        ORDER BY order_date
        ROWS UNBOUNDED PRECEDING
    ) AS grand_total
FROM orders
ORDER BY order_date;

-- --- Moving average with edge handling (7-day, minimum 3 days) ---
SELECT
    date,
    value,
    AVG(value) OVER (
        ORDER BY date
        ROWS BETWEEN 3 PRECEDING AND 3 FOLLOWING
    ) AS moving_avg_7day
FROM daily_metrics;

-- --- First/last value in a group with NULL handling ---
-- Fill forward: last non-null value carried forward
SELECT
    date,
    value,
    value IS NOT NULL AS has_value,
    LAST_VALUE(value) IGNORE NULLS OVER (
        ORDER BY date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS last_known_value
FROM sparse_data;
```

## Common Mistakes

```sql
-- WRONG: Using DISTINCT with window functions (inefficient)
-- DISTINCT evaluates AFTER the window function, forcing a full scan
SELECT DISTINCT
    department_id,
    AVG(salary) OVER (PARTITION BY department_id) AS dept_avg
FROM employees;

-- CORRECT: Use GROUP BY instead
SELECT
    department_id,
    AVG(salary) AS dept_avg
FROM employees
GROUP BY department_id;

-- WRONG: Incorrect frame for running total
-- Default frame is RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
-- RANGE can include ties (same order values), ROWS does not
SELECT
    order_date,
    amount,
    SUM(amount) OVER (ORDER BY order_date) AS running_total
FROM orders;
-- If two orders on same date, RANGE frame includes both in each row's total

-- CORRECT: Be explicit about frame
SELECT
    order_date,
    amount,
    SUM(amount) OVER (
        ORDER BY order_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_total_by_row
FROM orders;

-- WRONG: ROWS vs RANGE confusion for date-ordered data
-- ROWS 6 PRECEDING means exactly 6 rows, not 6 days
-- For a 7-day moving average by calendar days, use RANGE:

-- CORRECT: RANGE for date-based windows
SELECT
    date,
    value,
    AVG(value) OVER (
        ORDER BY date
        RANGE BETWEEN interval '3 days' PRECEDING AND interval '3 days' FOLLOWING
    ) AS moving_avg_calendar
FROM daily_metrics;
```

## Gotchas
- **ROWS vs RANGE vs GROUPS — major semantic differences:**
  - `ROWS`: Physical frame — exactly N rows before/after (fastest)
  - `RANGE`: Logical frame — rows with values within range of current (handles ties)
  - `GROUPS`: Like RANGE but groups ties as units, not individual rows
  - Never use `RANGE` unless you need tie-inclusive behavior — it's slower than `ROWS`
- **Window functions run AFTER WHERE, HAVING, and GROUP BY:** You cannot filter by window function results in WHERE. Use a subquery or CTE: `SELECT * FROM (SELECT ..., ROW_NUMBER() OVER (...) AS rn FROM t) sub WHERE rn = 1`
- **`IGNORE NULLS` support varies:** PostgreSQL supports `IGNORE NULLS` for `LAG`, `LEAD`, `FIRST_VALUE`, `LAST_VALUE` since PG 14. Older versions require `COALESCE` or subquery workarounds.
- **Frame exclusion clause (`EXCLUDE CURRENT ROW`, `EXCLUDE GROUP`, etc.) is PG 14+:** `EXCLUDE CURRENT ROW` is useful for "average of peers excluding self" but less efficient than using separate aggregates.
- **`PERCENT_RANK` and `CUME_DIST` are expensive:** These compute relative positions across the entire partition. For approximate percentiles, use `ntile()` or `percentile_cont()` ordered-set aggregate instead.

## Related
- db/postgres/window-functions.md
- db/postgres/query-optimization.md
