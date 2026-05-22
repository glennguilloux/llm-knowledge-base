---
id: "db-postgres-replication"
title: "PostgreSQL Streaming and Logical Replication"
language: "sql"
category: "db"
subcategory: "postgresql"
tags: ["postgresql", "replication", "streaming", "logical", "ha", "failover"]
version: "latest"
retrieval_hint: "PostgreSQL replication streaming logical pg_basebackup hot standby failover replica"
last_verified: "2026-05-22"
confidence: "high"
---

# PostgreSQL Streaming and Logical Replication

## When to Use
- High availability: standby servers that take over on primary failure
- Read scaling: routing read queries to replicas to reduce primary load
- Data distribution: selectively replicating tables to different systems
- Zero-downtime migrations: logical replication to a new major version

## Standard Pattern

### Streaming Replication Setup

```sql
-- On PRIMARY server (postgresql.conf)
-- wal_level = replica          (or 'logical' for logical replication)
-- max_wal_senders = 5          (max concurrent replication connections)
-- wal_keep_size = '1GB'        (retain WAL for replica catch-up)
-- hot_standby = on              (allow read queries on standby)

-- Create replication user
CREATE ROLE replicator WITH REPLICATION LOGIN PASSWORD 'secure_password';

-- pg_hba.conf — allow replication connections from standby IP
-- host  replication  replicator  10.0.2.10/32  scram-sha-256
```

```bash
# On STANDBY server — base backup from primary
pg_basebackup -h 10.0.1.10 -U replicator -D /var/lib/postgresql/16/main \
  -Fp -Xs -P -R

# The -R flag creates standby.signal and sets primary_conninfo in postgresql.auto.conf
# Start standby
sudo systemctl start postgresql
```

```sql
-- Verify replication status on PRIMARY
SELECT client_addr, state, sent_lsn, write_lsn, flush_lsn, replay_lsn,
       pg_wal_lsn_diff(sent_lsn, replay_lsn) AS lag_bytes
FROM pg_stat_replication;

-- Verify standby is receiving on STANDBY
SELECT status, receive_start_lsn, received_lsn, last_msg_send_time
FROM pg_stat_wal_receiver;
```

### Logical Replication

```sql
-- On PUBLISHER (source)
-- wal_level = logical  (required for logical replication)
CREATE PUBLICATION my_pub FOR TABLE orders, customers;
-- Or all tables: CREATE PUBLICATION my_pub FOR ALL TABLES;

-- On SUBSCRIBER (target) — tables must exist with same schema
CREATE SUBSCRIPTION my_sub
  CONNECTION 'host=10.0.1.10 dbname=mydb user=replicator password=secure_password'
  PUBLICATION my_pub;

-- Monitor logical replication
SELECT subname, subenabled, received_lsn, last_msg_send_time,
       pg_wal_lsn_diff(received_lsn, latest_end_lsn) AS lag_bytes
FROM pg_stat_subscription;

-- Add a table to existing publication
ALTER PUBLICATION my_pub ADD TABLE payments;

-- Refresh subscription to pick up new tables
ALTER SUBSCRIPTION my_sub REFRESH PUBLICATION;
```

### Failover with pg_promote

```sql
-- On standby — promote to primary after primary failure
SELECT pg_promote();
-- Or: pg_ctl promote

-- After promotion, point application to new primary
-- Update connection strings or use a virtual IP / DNS failover
```

## Common Mistakes

```sql
-- WRONG: Setting wal_level after server starts — requires restart
ALTER SYSTEM SET wal_level = 'logical';
-- wal_level changes require: sudo systemctl restart postgresql

-- CORRECT: Set wal_level before first start or restart immediately
ALTER SYSTEM SET wal_level = 'logical';
-- Then: sudo systemctl restart postgresql
-- Verify: SHOW wal_level;
```

```sql
-- WRONG: No monitoring — replica silently falls behind primary
-- Primary fails, standby promoted with missing transactions

-- CORRECT: Monitor replication lag and alert on threshold
-- Add to monitoring system:
SELECT pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn) AS lag_bytes
FROM pg_stat_replication
WHERE client_addr = '10.0.2.10';
-- Alert if lag_bytes > 10485760 (10MB)
```

```sql
-- WRONG: Logical replication with different schemas — subscriber errors silently
CREATE SUBSCRIPTION my_sub CONNECTION '...' PUBLICATION my_pub;
-- ERROR: relation "orders" does not exist on subscriber

-- CORRECT: Create matching schema on subscriber first
-- pg_dump --schema-only -f schema.sql mydb
-- psql -d mydb_subscriber -f schema.sql
-- Then create subscription
```

## Gotchas
- Streaming replication is all-or-nothing — you replicate the entire database cluster; logical replication lets you pick specific tables
- `pg_basebackup` locks the primary briefly for consistency — run during low-traffic windows on large databases
- Standby servers cannot accept writes (`default_transaction_read_only = on` by default) — any write attempt returns an error
- Replication slots prevent WAL cleanup — if a replica goes down with a slot active, WAL accumulates and can fill your disk; drop unused slots
- Logical replication does NOT replicate DDL — `ALTER TABLE` must be run on both publisher and subscriber manually
- Cascading replication (standby replicating from another standby) reduces primary load but adds latency at each hop
- `hot_standby = on` allows read queries on standby, but long-running queries can delay WAL replay and increase lag
- Promoting a standby is irreversible — the old primary cannot rejoin as a standby without re-creating it from a base backup

## Related
- db/postgres/migrations.md
- db/postgres/indexes.md
- db/postgres/transactions.md
