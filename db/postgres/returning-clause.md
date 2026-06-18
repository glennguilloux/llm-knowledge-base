---
id: "db-postgres-returning-clause"
title: "PostgreSQL RETURNING Clause — Patterns and Use Cases"
language: "sql"
category: "db"
subcategory: "postgresql"
tags: ["sql", "postgresql", "returning", "insert", "update", "delete", "merge", "upsert", "data-modification"]
version: "14+"
retrieval_hint: "PostgreSQL RETURNING clause INSERT UPDATE DELETE UPSERT ON CONFLICT CTE data modification"
last_verified: "2026-05-25"
confidence: "high"
---

# PostgreSQL RETURNING Clause — Patterns and Use Cases

## When to Use
- Getting auto-generated IDs, defaults, or timestamps after INSERT
- Returning modified rows after UPDATE (e.g., confirming what changed)
- Archiving or logging deleted rows before they're removed
- Composing multiple data-modifying operations in a single CTE
- UPSERT (INSERT ON CONFLICT) where you need the resulting row state

## Standard Pattern

```sql
-- --- INSERT: Get auto-generated values ---
INSERT INTO users (name, email)
VALUES ('Alice', 'alice@example.com')
RETURNING id, created_at;
-- Returns: {id: 42, created_at: '2026-05-25 10:00:00'}

-- INSERT multiple rows, get all generated IDs
INSERT INTO users (name, email)
VALUES
    ('Bob', 'bob@example.com'),
    ('Carol', 'carol@example.com'),
    ('Dave', 'dave@example.com')
RETURNING id, name;
-- Returns:
--   {id: 43, name: 'Bob'}
--   {id: 44, name: 'Carol'}
--   {id: 45, name: 'Dave'}

-- INSERT with DEFAULT values
INSERT INTO audit_log (action, target)
VALUES ('login', 42)
RETURNING *;  -- Returns ALL columns, including defaults/timestamps

-- --- UPDATE: Return the modified row ---
UPDATE users
SET last_login = now(), login_count = login_count + 1
WHERE id = 42
RETURNING id, name, email, last_login, login_count;
-- Returns the row AS IT LOOKS AFTER the update

-- UPDATE with computed field
UPDATE inventory
SET quantity = quantity - 1
WHERE product_id = 100 AND quantity > 0
RETURNING id, product_id, quantity AS remaining_stock;

-- --- DELETE: Archive before removal ---
DELETE FROM sessions
WHERE expires_at < now()
RETURNING id, user_id, created_at, expires_at;
-- Returns the deleted rows — use for audit log or cache invalidation

-- DELETE with limit (using CTE)
WITH deleted AS (
    DELETE FROM notifications
    WHERE created_at < now() - interval '30 days'
    RETURNING id, user_id, content
)
INSERT INTO notification_archive (notification_id, user_id, content, deleted_at)
SELECT id, user_id, content, now() FROM deleted;

-- --- UPSERT with RETURNING ---
INSERT INTO leaderboard (player_id, score)
VALUES (42, 1500)
ON CONFLICT (player_id) DO UPDATE
SET score = leaderboard.score + EXCLUDED.score,
    updated_at = now()
RETURNING *;
-- Returns the final row state (inserted OR updated)

-- --- Conditional RETURNING with FILTER ---
-- Not directly supported, but you can use a CTE with conditions:
WITH updated AS (
    UPDATE orders
    SET status = 'shipped', shipped_at = now()
    WHERE id = 100 AND status = 'pending'
    RETURNING *
)
SELECT * FROM updated
UNION ALL
SELECT NULL::orders, 'not_found'::text  -- or handle in app
WHERE NOT EXISTS (SELECT 1 FROM updated);
```

## Common Mistakes

```sql
-- WRONG: Assuming RETURNING returns rows in a specific order
-- RETURNING does NOT guarantee order, especially for multi-row operations
INSERT INTO users (name) VALUES ('Zoe'), ('Alice'), ('Bob')
RETURNING id, name;
-- Might return (Zoe, 1), (Alice, 2), (Bob, 3) — order depends on physical storage

-- CORRECT: Add ORDER BY to RETURNING if order matters
INSERT INTO users (name) VALUES ('Zoe'), ('Alice'), ('Bob')
RETURNING id, name
ORDER BY name;  -- Now: Alice, Bob, Zoe

-- WRONG: Using RETURNING * with a table that has many columns
-- Returning unnecessary columns wastes bandwidth
UPDATE huge_table SET processed = true WHERE id = 42
RETURNING *;  -- Returns ALL columns (maybe 50+)

-- CORRECT: Be selective
UPDATE huge_table SET processed = true WHERE id = 42
RETURNING id, processed, updated_at;

-- WRONG: Expecting RETURNING with ON CONFLICT DO NOTHING
-- If the conflict causes DO NOTHING, ZERO rows are returned
INSERT INTO unique_users (email, name)
VALUES ('existing@example.com', 'New User')
ON CONFLICT (email) DO NOTHING
RETURNING id;
-- If email already exists: returns 0 rows (not the existing row!)

-- CORRECT: Use DO UPDATE to get the existing row
INSERT INTO unique_users (email, name)
VALUES ('existing@example.com', 'New User')
ON CONFLICT (email) DO UPDATE
SET name = EXCLUDED.name  -- Or SET name = unique_users.name to keep existing
RETURNING id;
-- Now it always returns a row

-- WRONG: Expecting RETURNING in a WHERE clause
-- RETURNING happens AFTER the DML, not during
DELETE FROM users WHERE id IN (
    SELECT id FROM users ORDER BY created_at LIMIT 1 RETURNING id
);
-- ERROR: RETURNING not allowed in subquery!
```

## Gotchas
- **RETURNING sees the FINAL state of the row:** After INSERT, triggers (BEFORE/AFTER) run, and RETURNING sees the final state (including trigger modifications). For UPDATE, RETURNING shows the post-update values, NOT the pre-update values.
- **No RETURNING for TRUNCATE:** `TRUNCATE` does not support RETURNING. Use `DELETE FROM table RETURNING *` if you need the removed rows, even though it's slower.
- **RETURNING in CTEs is extremely powerful:** You can chain multiple DML operations in a single statement using CTEs, each with RETURNING. This enables atomic multi-table operations:

```sql
WITH
    inserted AS (
        INSERT INTO orders (user_id, total) VALUES (42, 99.99)
        RETURNING id
    ),
    items AS (
        INSERT INTO order_items (order_id, product_id, quantity)
        SELECT inserted.id, unnest(ARRAY[1,2,3]), 1
        FROM inserted
        RETURNING order_id, product_id
    )
UPDATE inventory SET stock = stock - 1
WHERE product_id IN (SELECT product_id FROM items);
```

- **Triggers and RETURNING:** If a trigger modifies the row AFTER RETURNING conceptually fires, the returned values reflect the trigger's changes. The RETURNING clause sees the row as it exists after all BEFORE and AFTER triggers.
- **Empty result handling:** When `ON CONFLICT DO NOTHING` prevents an insert, RETURNING returns zero rows. Your application code must handle this case (check `ROW_COUNT` or the number of returned rows).

## Related
- db/postgres/transactions.md
- db/migrations-strategy.md
