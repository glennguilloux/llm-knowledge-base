---
id: "db-postgres-transactions"
title: "Transaction Patterns and Isolation Levels"
language: "sql"
category: "db"
tags: ["sql", "postgresql", "transactions", "isolation", "acid", "locking"]
version: "14+"
retrieval_hint: "transaction BEGIN COMMIT ROLLBACK isolation level deadlock"
last_verified: "2026-05-22"
confidence: "high"
---

# Transaction Patterns and Isolation Levels

## When to Use
- Ensuring multiple operations succeed or fail atomically
- Preventing race conditions in concurrent updates
- Implementing optimistic or pessimistic locking
- Managing complex business logic across multiple tables

## Standard Pattern

```sql
-- Basic transaction
BEGIN;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;

-- ROLLBACK on error
BEGIN;
INSERT INTO orders (user_id, total) VALUES (42, 99.99);
INSERT INTO order_items (order_id, product_id, qty) VALUES (currval('orders_id_seq'), 1, 2);
-- If any step fails:
ROLLBACK;

-- Savepoints (partial rollback)
BEGIN;
INSERT INTO audit_log (action) VALUES ('start');
SAVEPOINT sp1;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
-- Something went wrong, rollback to savepoint
ROLLBACK TO sp1;
-- Continue from here — audit_log insert is preserved
UPDATE accounts SET balance = balance - 50 WHERE id = 1;
COMMIT;

-- Isolation levels
-- READ COMMITTED (default): each statement sees latest committed data
BEGIN ISOLATION LEVEL READ COMMITTED;
SELECT balance FROM accounts WHERE id = 1;  -- 1000
-- Another transaction commits a change to balance = 900
SELECT balance FROM accounts WHERE id = 1;  -- 900 (changed!)
COMMIT;

-- REPEATABLE READ: snapshot at transaction start
BEGIN ISOLATION LEVEL REPEATABLE READ;
SELECT balance FROM accounts WHERE id = 1;  -- 1000
-- Another transaction commits a change to balance = 900
SELECT balance FROM accounts WHERE id = 1;  -- 1000 (same!)
COMMIT;

-- SERIALIZABLE: strictest, detects anomalies
BEGIN ISOLATION LEVEL SERIALIZABLE;
-- All operations behave as if executed serially
-- PostgreSQL will abort if serialization anomaly detected
COMMIT;

-- Pessimistic locking (SELECT FOR UPDATE)
BEGIN;
SELECT * FROM accounts WHERE id = 1 FOR UPDATE;
-- Row is locked — other transactions block on this row
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
COMMIT;

-- Optimistic locking (version column)
-- Schema: accounts(id, balance, version)
UPDATE accounts
SET balance = balance - 100, version = version + 1
WHERE id = 1 AND version = 5;
-- If affected_rows = 0, someone else modified it — retry

-- Advisory locks (application-level locking)
SELECT pg_advisory_lock(12345);  -- Block until acquired
-- Do work
SELECT pg_advisory_unlock(12345);

-- Non-blocking advisory lock
SELECT pg_try_advisory_lock(12345);  -- Returns true/false
```

## Common Mistakes

```sql
-- WRONG: Long-running transaction (holds locks)
BEGIN;
SELECT * FROM large_table;  -- Takes 30 seconds
-- Other transactions block waiting for locks
COMMIT;

-- CORRECT: Keep transactions short
-- Do heavy computation outside the transaction
BEGIN;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
COMMIT;

-- WRONG: Missing transaction for multi-statement operation
UPDATE inventory SET qty = qty - 1 WHERE product_id = 1;
INSERT INTO orders (product_id) VALUES (1);
-- If the server crashes between these, inventory is wrong

-- CORRECT: Wrap in transaction
BEGIN;
UPDATE inventory SET qty = qty - 1 WHERE product_id = 1;
INSERT INTO orders (product_id) VALUES (1);
COMMIT;

-- WRONG: SELECT FOR UPDATE without WHERE (locks entire table)
SELECT * FROM accounts FOR UPDATE;

-- CORRECT: Lock only needed rows
SELECT * FROM accounts WHERE id = 1 FOR UPDATE;

-- WRONG: Ignoring deadlock detection
-- PostgreSQL automatically detects deadlocks and aborts one transaction

-- CORRECT: Order locks consistently to prevent deadlocks
-- Always lock accounts in order of id
BEGIN;
SELECT * FROM accounts WHERE id = LEAST(1, 2) FOR UPDATE;
SELECT * FROM accounts WHERE id = GREATEST(1, 2) FOR UPDATE;
COMMIT;

-- WRONG: Not handling serialization failures
BEGIN ISOLATION LEVEL SERIALIZABLE;
-- ... operations ...
COMMIT;  -- May fail with serialization_failure

-- CORRECT: Retry on serialization failure
-- Application code:
-- loop:
--   BEGIN ISOLATION LEVEL SERIALIZABLE;
--   ... operations ...
--   COMMIT; (catch serialization_failure, retry)
```

## Gotchas
- Default isolation level is `READ COMMITTED` — sufficient for most applications
- `REPEATABLE READ` gives a snapshot at transaction start — may see stale data
- `SERIALIZABLE` is strictest but has performance overhead — use only when needed
- `SELECT FOR UPDATE` blocks other transactions from modifying the row until COMMIT/ROLLBACK
- `FOR UPDATE NOWAIT` raises an error immediately instead of blocking
- `FOR UPDATE SKIP LOCKED` skips locked rows — useful for job queues
- Deadlocks are automatically detected and resolved — one transaction is aborted
- Always acquire locks in a consistent order to prevent deadlocks
- Advisory locks are application-level — not tied to table rows
- `SET LOCAL` sets a parameter for the current transaction only
- Autocommit in most tools means each statement is its own transaction
- Long transactions hold locks and prevent vacuuming — keep them short

## Related
- db/postgres/query-optimization.md
- db/postgres/indexing-strategies.md
- db/postgres/ctes.md
