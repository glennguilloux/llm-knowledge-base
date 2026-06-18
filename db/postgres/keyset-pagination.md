---
id: "db-postgres-keyset-pagination"
title: "Keyset Pagination in PostgreSQL — Efficient Cursor-Based Paging"
language: "sql"
category: "db"
subcategory: "postgresql"
tags: ["sql", "postgresql", "pagination", "keyset", "cursor", "offset", "performance", "seek"]
version: "14+"
retrieval_hint: "PostgreSQL keyset pagination cursor-based offset performance seek method efficient paging"
last_verified: "2026-05-25"
confidence: "high"
---

# Keyset Pagination in PostgreSQL — Efficient Cursor-Based Paging

## When to Use
- Paginating large datasets where OFFSET becomes slow (past page ~100)
- Real-time data where new rows inserted at the start would shift pages
- Infinite scroll UIs where cursor-based pagination is the native pattern
- API endpoints where stable, repeatable page boundaries matter
- Any query where you care about consistent performance regardless of page depth

## Standard Pattern

```sql
-- --- THE PROBLEM: OFFSET pagination gets slower with depth ---
-- Each OFFSET 10000 still reads and discards 10000 rows
SELECT * FROM users
ORDER BY created_at DESC, id DESC
LIMIT 20
OFFSET 10000;  -- Slow! Reads 10020 rows, returns 20

-- --- THE SOLUTION: Keyset (seek) pagination ---
-- Page 1: Get the first page (same as regular query, no keyset yet)
SELECT id, name, email, created_at
FROM users
ORDER BY created_at DESC, id DESC
LIMIT 20;

-- Page 2+: Use the last row's values as the cursor
SELECT id, name, email, created_at
FROM users
WHERE (created_at, id) < ('2026-05-20 14:30:00', 12345)
ORDER BY created_at DESC, id DESC
LIMIT 20;

-- --- Generic keyset pagination function ---
-- Use ROW values for composite keyset (PostgreSQL supports this natively)
CREATE OR REPLACE FUNCTION paginate_users(
    p_cursor_created_at timestamptz DEFAULT NULL,
    p_cursor_id bigint DEFAULT NULL,
    p_limit int DEFAULT 20,
    p_direction text DEFAULT 'next'  -- 'next' or 'prev'
)
RETURNS SETOF users AS $$
BEGIN
    IF p_direction = 'next' THEN
        IF p_cursor_id IS NULL THEN
            -- First page
            RETURN QUERY
            SELECT * FROM users
            ORDER BY created_at DESC, id DESC
            LIMIT p_limit;
        ELSE
            -- Subsequent pages
            RETURN QUERY
            SELECT * FROM users
            WHERE (created_at, id) < (p_cursor_created_at, p_cursor_id)
            ORDER BY created_at DESC, id DESC
            LIMIT p_limit;
        END IF;
    ELSE
        -- Previous page (reverse direction)
        IF p_cursor_id IS NOT NULL THEN
            RETURN QUERY
            SELECT * FROM users
            WHERE (created_at, id) > (p_cursor_created_at, p_cursor_id)
            ORDER BY created_at ASC, id ASC  -- Reverse order
            LIMIT p_limit;
        END IF;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Usage:
-- Page 1: SELECT * FROM paginate_users(NULL, NULL, 20, 'next');
-- Page 2: SELECT * FROM paginate_users('2026-05-20 14:30:00', 12345, 20, 'next');
-- Prev:   SELECT * FROM paginate_users('2026-05-20 14:20:00', 12340, 20, 'prev');

-- --- Simple keyset with a single column ---
-- When ordering by a single unique column:
SELECT id, name, score
FROM leaderboard
ORDER BY score DESC, id ASC  -- id is tiebreaker
LIMIT 20;

-- Next page:
SELECT id, name, score
FROM leaderboard
WHERE (score, id) < (9500, 42)  -- Last row had score=9500, id=42
ORDER BY score DESC, id ASC
LIMIT 20;

-- --- Keyset with filters applied ---
SELECT id, name, email, status
FROM users
WHERE status = 'active'
  AND (created_at, id) < ('2026-05-20', 12345)
ORDER BY created_at DESC, id DESC
LIMIT 20;

-- The filter on status is applied BEFORE the keyset condition.
-- The composite index (status, created_at, id) makes this fast.
```

## Common Mistakes

```sql
-- WRONG: Keyset on a column that isn't unique (ties cause missing/duplicate rows)
-- If created_at has duplicates, you can skip or repeat rows
SELECT * FROM users
WHERE created_at < '2026-05-20'
ORDER BY created_at DESC
LIMIT 20;

-- CORRECT: Always include a unique tiebreaker (usually id)
SELECT * FROM users
WHERE (created_at, id) < ('2026-05-20', 99999)
ORDER BY created_at DESC, id DESC
LIMIT 20;

-- WRONG: NULL values in the sort column
-- NULLs sort differently with NULLS FIRST/LAST
SELECT * FROM users
WHERE updated_at < '2026-05-20'  -- NULLs are NOT < '2026-05-20'
ORDER BY updated_at DESC NULLS LAST
LIMIT 20;

-- CORRECT: Handle NULLs explicitly
SELECT * FROM users
WHERE (updated_at IS NOT NULL AND updated_at < '2026-05-20')
   OR updated_at IS NULL
ORDER BY updated_at DESC NULLS LAST, id DESC
LIMIT 20;

-- WRONG: Using DESC on the keyset column without matching ORDER BY
-- If ORDER BY is (score DESC, id ASC), the keyset comparison must match
SELECT * FROM leaderboard
WHERE score < 9500  -- Wrong! DESC means "less than" goes the other way
ORDER BY score DESC, id ASC
LIMIT 20;

-- CORRECT: For DESC first column, comparison is also DESC
SELECT * FROM leaderboard
WHERE (score, id) < (9500, 42)  -- Correct: "less than" in DESC order
ORDER BY score DESC, id ASC
LIMIT 20;
```

## Gotchas
- **Composite index order matters:** For `WHERE (status, created_at, id) < ('active', '2026-05-20', 12345) ORDER BY status, created_at DESC, id DESC`, the ideal index is `(status, created_at DESC, id DESC)`. Without a matching index, PostgreSQL uses a bitmap scan or sequential scan.
- **Keyset does NOT support random page access:** Unlike OFFSET, you cannot jump to "page 50". Keyset is inherently sequential — you start from the beginning and page forward. For "jump to page N", you need OFFSET (or estimate based on distribution). Hybrid approaches use OFFSET for the first few pages, keyset for deep pages.
- **Direction reversal (prev/next) requires opposite ORDER BY:** For "previous page", reverse the sort order (`ASC` instead of `DESC`) and flip the comparison (`>` instead of `<`). Then reverse the result set client-side. This doubles the query complexity.
- **Row value comparison follows SQL semantics:** `(a, b) < (x, y)` means `a < x OR (a = x AND b < y)`. PostgreSQL uses B-tree comparison semantics for row values. This is efficient because it matches the index structure.
- **Caching cursor values:** The cursor values (last seen sort column values) are naturally cacheable. Include them in API responses as an opaque `cursor` string (base64-encoded JSON). The client sends it back for the next page.

## Related
- db/postgres/query-optimization.md
- db/postgres/indexes.md
