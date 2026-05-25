---
id: "db-migrations-strategy"
title: "Database Migrations: Planning, Safety, Rollback"
language: "sql"
category: "db"
tags: ["sql", "migrations", "schema-changes", "rollback", "zero-downtime"]
version: "n/a"
retrieval_hint: "database migrations schema changes zero-downtime rollback expand-contract backward compatibility"
last_verified: "2026-05-24"
confidence: "high"
---

# Database Migrations: Planning, Safety, Rollback

## When to Use
- Evolving database schemas in production
- Adding, modifying, or removing columns and tables
- Ensuring safe rollback paths for schema changes
- Coordinating schema changes with application deployments

## Standard Pattern

```sql
-- === Expand-Contract Pattern (Zero-Downtime) ===

-- Phase 1: EXPAND (deploy first, no application change)
ALTER TABLE users ADD COLUMN display_name VARCHAR(255);
-- Create index on new column
CREATE INDEX idx_users_display_name ON users (display_name);
-- Write to BOTH old and new fields in application
-- Old code reads old field, new code can read either

-- Phase 2: MIGRATE (backfill data)
UPDATE users SET display_name = username WHERE display_name IS NULL;

-- Phase 3: CONTRACT (remove old after confirming stability)
-- After all app instances use new column and data is verified:
-- ALTER TABLE users DROP COLUMN username;
-- (Requires full confidence — hard to reverse!)


-- === Migration Versioning ===

CREATE TABLE schema_migrations (
    version     BIGINT PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    applied_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    checksum    VARCHAR(64),
    duration_ms INT
);

INSERT INTO schema_migrations (version, name, checksum)
VALUES (20250523001, 'add_display_name_to_users', 'sha256hash...');


-- === Safe Migration Patterns ===

-- 1. Add column with default (can lock large tables!)
-- PostgreSQL 11+: default without rewriting table
ALTER TABLE users ADD COLUMN role VARCHAR(50) NOT NULL DEFAULT 'user';

-- MySQL: Adding DEFAULT to existing column rewrites table
-- Safe on MySQL 8.0 with INSTANT ADD COLUMN:
ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'user',
    ALGORITHM=INSTANT;

-- 2. Add column initially nullable, then backfill, then NOT NULL
ALTER TABLE users ADD COLUMN timezone VARCHAR(50);
UPDATE users SET timezone = 'UTC' WHERE timezone IS NULL;
ALTER TABLE users ALTER COLUMN timezone SET NOT NULL;

-- 3. Rename column (safe with dual-write)
-- Step 1: Add new column
ALTER TABLE users ADD COLUMN full_name VARCHAR(255);

-- Step 2: Backfill
UPDATE users SET full_name = name WHERE full_name IS NULL;

-- Step 3: Deploy code using full_name instead of name

-- Step 4: Remove old column (separate deploy)
-- ALTER TABLE users DROP COLUMN name;


-- === Index Creation (avoid locking) ===

-- PostgreSQL: CONCURRENTLY (non-blocking)
CREATE INDEX CONCURRENTLY idx_orders_created ON orders (created_at);
-- Takes longer but doesn't block writes

-- MySQL 8.0: Online DDL
CREATE INDEX idx_orders_created ON orders (created_at) ALGORITHM=INPLACE, LOCK=NONE;

-- SQLite: CREATE INDEX never locks in WAL mode
CREATE INDEX idx_orders_created ON orders (created_at);


-- === Rollback Pattern ===

-- Each migration has:
--   up: the forward migration
--   down: the rollback migration

-- Example migration file:
-- -- 20250523001_add_display_name.up.sql
-- ALTER TABLE users ADD COLUMN display_name VARCHAR(255);
--
-- -- 20250523001_add_display_name.down.sql
-- ALTER TABLE users DROP COLUMN display_name;
```

## Common Mistakes

```sql
-- WRONG: Adding NOT NULL column without default (locks table!)
ALTER TABLE users ADD COLUMN role VARCHAR(50) NOT NULL;
-- In Postgres < 11: rewrites entire table, takes lock
-- In MySQL: scans full table to fill default

-- CORRECT: Add nullable, backfill, then add constraint
ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'user';
-- Backfill in batches
UPDATE users SET role = 'user' WHERE role IS NULL AND id BETWEEN ? AND ?
ALTER TABLE users ALTER COLUMN role SET NOT NULL;


-- WRONG: Removing a column that old application code still references
ALTER TABLE users DROP COLUMN username;
-- Old app instances crash with "column doesn't exist"!

-- CORRECT: Expand-contract — remove column only after
-- ALL instances have been updated and stable


-- WRONG: Long-running migration without timeout
UPDATE users SET bio = '' WHERE bio IS NULL;
-- On a 10M row table, this could take hours and block replication

-- CORRECT: Batch in chunks
UPDATE users SET bio = '' WHERE bio IS NULL AND id BETWEEN 1 AND 10000;
-- Repeat until done


-- WRONG: Dropping a column that has FK references
ALTER TABLE orders DROP COLUMN user_id;
-- Fails with: "cannot drop column: other objects depend on it"

-- CORRECT: Drop constraints first
ALTER TABLE orders DROP CONSTRAINT fk_orders_user_id;
ALTER TABLE orders DROP COLUMN user_id;


-- WRONG: Renaming a table without considering views, triggers, FKs
ALTER TABLE users RENAME TO user_profiles;
-- All references to "users" in views, procs, and app code break!

-- CORRECT: Use views for backwards compatibility
ALTER TABLE users RENAME TO user_profiles;
CREATE VIEW users AS SELECT * FROM user_profiles;
-- Then gradually migrate references and drop view
```

## Gotchas
- **Lock timeouts in high concurrency**: DDL statements in MySQL and PostgreSQL require locks. `ALTER TABLE` on a busy table may wait for existing transactions or deadlock. Use `LOCK_TIMEOUT` and `statement_timeout` to avoid blocking production traffic indefinitely.
- **Replication lag during migrations**: Long-running DDL on the primary replicates to replicas. The replica may fall behind. Monitor lag and throttle writes during DDL if needed.
- **Migration order matters**: Rollbacks must run in reverse order of applies. Implement a migration system that tracks the apply order and can reverse migrations cleanly.
- **Data type migrations are high risk**: Changing INT to BIGINT, or VARCHAR to TEXT, often rewrites the entire table. Test on a copy of production data first and have rollback ready.
- **NOT NULL with DEFAULT in MySQL**: In MySQL, adding a NOT NULL column with DEFAULT uses INSTANT algorithm (MySQL 8.0.12+) only for the ADD step. The real table rewrite happens if you ADD without DEFAULT then ALTER.
- **Index creation with concurrent writes**: Even with CONCURRENTLY (Postgres) or INPLACE (MySQL), long-running index creation increases autovacuum/undo pressure. Schedule during low traffic.
- **Application cache invalidation**: Schema changes can invalidate ORM metadata caches. Restart application instances or flush connection pool after migration to refresh prepared statements and column mappings.

## Related
- db/mysql/basics.md
- db/sqlite/production.md
- db/query-analysis.md
