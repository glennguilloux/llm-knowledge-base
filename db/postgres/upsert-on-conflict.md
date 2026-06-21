---
id: "db-postgres-upsert-on-conflict"
title: "UPSERT with ON CONFLICT"
language: "sql"
category: "db"
subcategory: "postgres"
tags: ["sql", "postgresql", "upsert", "insert", "on-conflict", "excluded", "unique-constraint", "partial-index", "idempotency"]
version: "14+"
retrieval_hint: "PostgreSQL UPSERT INSERT ON CONFLICT DO UPDATE EXCLUDED unique constraint partial index idempotent write"
last_verified: "2026-05-24"
confidence: "medium"
---

# UPSERT with ON CONFLICT

## When to Use
- Making `INSERT` operations idempotent when a unique constraint defines the natural key
- Updating an existing row or inserting a new row in one statement
- Maintaining counters, latest-state records, or cache tables from event streams
- Avoiding race conditions between separate `SELECT`, `INSERT`, and `UPDATE` checks
- Applying conditional updates only when the new value is newer, higher, or more specific

## Standard Pattern

```sql
-- Basic upsert using a unique constraint
INSERT INTO users (id, email, name, updated_at)
VALUES (42, 'alice@example.test', 'Alice', NOW())
ON CONFLICT (id)
DO UPDATE SET
    email = EXCLUDED.email,
    name = EXCLUDED.name,
    updated_at = NOW()
RETURNING id, email, name, updated_at;

-- Use a named unique constraint for clarity
ALTER TABLE users ADD CONSTRAINT users_email_unique UNIQUE (email);

INSERT INTO users (email, name, updated_at)
VALUES ('alice@example.test', 'Alice', NOW())
ON CONFLICT ON CONSTRAINT users_email_unique
DO UPDATE SET
    name = EXCLUDED.name,
    updated_at = NOW()
RETURNING id, email, name;

-- Conditional upsert: only update when incoming value is newer
INSERT INTO user_profiles (user_id, last_seen_at, country, updated_at)
VALUES (42, TIMESTAMP '2026-06-20 10:00:00', 'US', NOW())
ON CONFLICT (user_id)
DO UPDATE SET
    last_seen_at = EXCLUDED.last_seen_at,
    country = EXCLUDED.country,
    updated_at = NOW()
WHERE EXCLUDED.last_seen_at > user_profiles.last_seen_at
RETURNING user_id, last_seen_at, country;

-- Upsert with a partial unique index
CREATE UNIQUE INDEX users_active_email_unique
ON users (email)
WHERE deleted_at IS NULL;

INSERT INTO users (email, name, deleted_at)
VALUES ('alice@example.test', 'Alice', NULL)
ON CONFLICT (email)
WHERE deleted_at IS NULL
DO UPDATE SET
    name = EXCLUDED.name,
    deleted_at = NULL
RETURNING id, email, name, deleted_at;
```

## Common Mistakes

```sql
-- WRONG: Upserting without a matching unique constraint or unique index
INSERT INTO users (email, name)
VALUES ('alice@example.test', 'Alice')
ON CONFLICT (email)
DO UPDATE SET name = EXCLUDED.name;
-- ERROR: there is no unique or exclusion constraint matching the ON CONFLICT specification

-- CORRECT: Create the unique constraint first, then upsert
ALTER TABLE users ADD CONSTRAINT users_email_unique UNIQUE (email);
INSERT INTO users (email, name)
VALUES ('alice@example.test', 'Alice')
ON CONFLICT ON CONSTRAINT users_email_unique
DO UPDATE SET name = EXCLUDED.name;

-- WRONG: Updating the row even when the incoming value is stale
INSERT INTO user_profiles (user_id, last_seen_at, updated_at)
VALUES (42, TIMESTAMP '2026-01-01 00:00:00', NOW())
ON CONFLICT (user_id)
DO UPDATE SET
    last_seen_at = EXCLUDED.last_seen_at,
    updated_at = NOW();
-- Older event overwrites newer last_seen_at

-- CORRECT: Add a WHERE clause so stale events do not regress state
INSERT INTO user_profiles (user_id, last_seen_at, updated_at)
VALUES (42, TIMESTAMP '2026-01-01 00:00:00', NOW())
ON CONFLICT (user_id)
DO UPDATE SET
    last_seen_at = EXCLUDED.last_seen_at,
    updated_at = NOW()
WHERE EXCLUDED.last_seen_at > user_profiles.last_seen_at;

-- WRONG: Referencing target table columns without a table qualifier in complex upserts
INSERT INTO leaderboard (player_id, score)
VALUES (42, 1500)
ON CONFLICT (player_id)
DO UPDATE SET score = score + EXCLUDED.score;
-- Ambiguous: score could mean leaderboard.score or EXCLUDED.score

-- CORRECT: Qualify target columns for clarity
INSERT INTO leaderboard (player_id, score)
VALUES (42, 1500)
ON CONFLICT (player_id)
DO UPDATE SET score = leaderboard.score + EXCLUDED.score;

-- WRONG: Assuming ON CONFLICT DO NOTHING returns the existing row
INSERT INTO users (email, name)
VALUES ('alice@example.test', 'Alice')
ON CONFLICT (email) DO NOTHING
RETURNING id;
-- If the row already exists, zero rows are returned

-- CORRECT: Use DO UPDATE when the caller needs the final row
INSERT INTO users (email, name)
VALUES ('alice@example.test', 'Alice')
ON CONFLICT (email)
DO UPDATE SET name = users.name
RETURNING id, email, name;
```

## Gotchas
- `ON CONFLICT` requires a unique constraint, primary key, or unique index that matches the conflict target.
- `EXCLUDED` is a pseudo-table containing the row proposed for insertion.
- `ON CONFLICT DO NOTHING` returns no row when a conflict is skipped; use `DO UPDATE` if the caller needs the existing row.
- A `WHERE` clause in `DO UPDATE` can make the statement idempotent and prevent stale updates.
- Partial unique indexes require matching `ON CONFLICT (...) WHERE ...` predicates.
- Concurrent upserts are safe for a single row but can still deadlock when multiple rows are touched in different orders.
- Heavy `ON CONFLICT DO UPDATE` work can turn writes into contention hot spots; batch and order writes when possible.

## Related
- db/postgres/transactions.md
- db/postgres/returning-clause.md
- db/postgres/indexes.md
