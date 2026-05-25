---
id: "db-postgres-migrations"
title: "PostgreSQL Migration Patterns"
language: "multi"
category: "db"
subcategory: "migrations"
tags: ["postgres", "migration", "schema", "alter", "index"]
version: "n/a"
retrieval_hint: "PostgreSQL migration schema alter table index"
last_verified: "2026-05-24"
confidence: "high"
---

# PostgreSQL Migration Patterns

## When to Use
- Adding/removing columns
- Creating indexes
- Changing column types
- Data migrations

## Standard Pattern

```sql
-- Add column (safe)
ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255);

-- Add column with default (safe for large tables in PG 11+)
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;

-- Create index concurrently (non-blocking)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users(email);

-- Add unique constraint
ALTER TABLE users ADD CONSTRAINT uq_users_email UNIQUE (email);

-- Rename column (careful!)
ALTER TABLE users RENAME COLUMN name TO full_name;

-- Change column type (may lock table)
ALTER TABLE users ALTER COLUMN age TYPE BIGINT;

-- Add NOT NULL constraint (requires default for existing rows)
ALTER TABLE users ALTER COLUMN email SET NOT NULL;

-- Drop column (careful!)
ALTER TABLE users DROP COLUMN IF EXISTS deprecated_field;

-- Create table
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    total DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Data migration
UPDATE users SET email = LOWER(TRIM(email)) WHERE email != LOWER(TRIM(email));
```

## Common Mistakes

```sql
-- WRONG: Adding NOT NULL without default (fails on existing rows)
ALTER TABLE users ADD COLUMN email VARCHAR(255) NOT NULL;

-- CORRECT: Add with default, then set NOT NULL
ALTER TABLE users ADD COLUMN email VARCHAR(255) DEFAULT '';
UPDATE users SET email = 'unknown' WHERE email = '';
ALTER TABLE users ALTER COLUMN email SET NOT NULL;

-- WRONG: Creating index without CONCURRENTLY (locks table)
CREATE INDEX idx_users_email ON users(email);  -- Blocks writes!

-- CORRECT: Use CONCURRENTLY
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);

-- WRONG: Dropping a column without checking dependencies
ALTER TABLE users DROP COLUMN email;  # Breaks views, indexes, code!

-- CORRECT: Check dependencies first, then use CASCADE if intentional
-- SELECT * FROM information_schema.view_column_usage WHERE column_name = 'email';
ALTER TABLE users DROP COLUMN email CASCADE;
```

## Gotchas
- `CONCURRENTLY` avoids locking but can't run in a transaction
- `IF NOT EXISTS` / `IF EXISTS` makes migrations idempotent
- Always test migrations on a copy of production data
- Use `ALTER TABLE ... ADD COLUMN ... DEFAULT ...` (PG 11+) for safe defaults
- Foreign keys create implicit indexes on the referencing column
- `ON DELETE CASCADE` automatically deletes related rows

## Related
- db/postgres/indexes.md
- db/postgres/json-queries.md
- python/db/sqlalchemy-2.0/migrations-alembic.md
