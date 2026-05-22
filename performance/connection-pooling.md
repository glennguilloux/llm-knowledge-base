---
id: "performance-connection-pooling"
title: "Database Connection Pooling"
language: "multi"
category: "performance"
tags: ["connection-pool", "database", "performance", "pool-size", "async", "pgbouncer"]
version: "n/a"
retrieval_hint: "connection pool database performance pool size pgbouncer asyncpg SQLAlchemy"
last_verified: "2026-05-22"
confidence: "high"
---

# Database Connection Pooling

## When to Use
- Production database connections (not per-request creation)
- High-concurrency applications with many simultaneous users
- Preventing database connection exhaustion
- Optimizing database connection overhead

## Standard Pattern

```python
# --- SQLAlchemy async pool ---
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/db",
    pool_size=20,           # Persistent connections in pool
    max_overflow=10,        # Extra connections when pool exhausted
    pool_timeout=30,        # Seconds to wait for connection
    pool_recycle=3600,      # Recycle connections after 1 hour
    pool_pre_ping=True,     # Check connection health before use
)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Usage
async def get_user(user_id: int):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

# --- Python sync pool (psycopg) ---
from psycopg import Pool

pool = Pool(
    conninfo="postgresql://user:pass@localhost/db",
    min_size=5,
    max_size=20,
)

with pool.connection() as conn:
    conn.execute("SELECT * FROM users WHERE id = %s", [user_id])

# --- Node.js (pg pool) ---
# import { Pool } from 'pg';
# const pool = new Pool({
#   connectionString: process.env.DATABASE_URL,
#   max: 20,
#   idleTimeoutMillis: 30000,
#   connectionTimeoutMillis: 2000,
# });
# const { rows } = await pool.query('SELECT * FROM users WHERE id = $1', [userId]);
```

## Common Mistakes

```python
# WRONG: Creating connection per request
async def get_user(user_id: int):
    engine = create_async_engine("postgresql+asyncpg://...")  # New pool each time!
    async with engine.connect() as conn:
        ...

# CORRECT: Reuse engine (module-level singleton)
engine = create_async_engine("postgresql+asyncpg://...", pool_size=20)

async def get_user(user_id: int):
    async with engine.connect() as conn:
        ...

# WRONG: Pool size too large
engine = create_async_engine(url, pool_size=100)  # DB has max 100 connections total!

# CORRECT: Pool size = (CPU cores * 2) + disk spindles, typically 10-20
engine = create_async_engine(url, pool_size=20, max_overflow=10)

# WRONG: Not recycling connections
engine = create_async_engine(url)  # Connections may go stale

# CORRECT: Recycle periodically
engine = create_async_engine(url, pool_recycle=3600, pool_pre_ping=True)

# WRONG: Not closing sessions
async def get_user(user_id: int):
    session = async_session()
    return await session.execute(...)  # Connection never returned to pool!

# CORRECT: Use context manager
async def get_user(user_id: int):
    async with async_session() as session:
        return await session.execute(...)
```

## Gotchas
- Default pool size varies by library — SQLAlchemy defaults to 5, which is too low for production
- `pool_pre_ping=True` checks if the connection is alive before using it — handles stale connections
- `max_overflow` allows temporary connections beyond `pool_size` — they're discarded when idle
- PgBouncer in transaction mode can reduce the effective pool size needed
- Too many connections to PostgreSQL wastes memory (~10MB per connection)
- `pool_recycle` prevents connections from going stale after database restarts
- Connection pool size should be tuned based on database capacity and concurrency needs

## Related
- db/postgres/indexes.md
- db/postgres/transactions.md
- patterns/api-design.md
