---
id: "antipatterns-performance"
title: "Performance Anti-Patterns"
language: "multi"
category: "anti-patterns"
tags: ["antipatterns", "performance", "n-plus-one", "pagination", "caching"]
version: "n/a"
retrieval_hint: "performance antipatterns N+1 query pagination connection pooling"
last_verified: "2026-05-24"
confidence: "high"
---

# Performance Anti-Patterns

## When to Use
- Performance code reviews
- Training LLMs to write efficient code
- Identifying bottlenecks before production
- Optimizing database-heavy applications

## Standard Pattern

```python
# WRONG: N+1 query problem
users = db.query("SELECT * FROM users")  # 1 query
for user in users:
    orders = db.query(f"SELECT * FROM orders WHERE user_id = {user.id}")  # N queries!
    user.orders = orders

# CORRECT: Eager loading with JOIN
users = db.query("""
    SELECT u.*, o.* FROM users u
    LEFT JOIN orders o ON u.id = o.user_id
""")  # 1 query

# WRONG: Unbounded collection loading
all_users = db.query("SELECT * FROM users")  # Loads millions of rows into memory

# CORRECT: Pagination
def get_users(page: int = 1, per_page: int = 50):
    offset = (page - 1) * per_page
    return db.query("SELECT * FROM users LIMIT %s OFFSET %s", (per_page, offset))

# WRONG: Synchronous blocking in async code
async def get_data():
    result = requests.get("https://api.example.com")  # Blocks event loop!

# CORRECT: Use async HTTP
async def get_data():
    async with httpx.AsyncClient() as client:
        result = await client.get("https://api.example.com")
    return result.json()

# WRONG: No connection pooling
def query(sql):
    conn = psycopg2.connect(DSN)  # New connection every call
    cursor = conn.execute(sql)
    conn.close()

# CORRECT: Connection pool
from psycopg2 import pool
db_pool = pool.ThreadedConnectionPool(1, 20, DSN)

def query(sql):
    conn = db_pool.getconn()
    try:
        cursor = conn.execute(sql)
        return cursor.fetchall()
    finally:
        db_pool.putconn(conn)
```

```typescript
// WRONG: Not using batch operations
for (const id of ids) {
  await db.query("DELETE FROM items WHERE id = $1", [id]);  // N round trips
}

// CORRECT: Batch delete
await db.query("DELETE FROM items WHERE id = ANY($1)", [ids]);  // 1 round trip

// WRONG: Memory leak from event listeners
function createWidget() {
  const handler = () => console.log("click");
  document.addEventListener("click", handler);
  // handler never removed — leaked on every createWidget() call
}

// CORRECT: Clean up event listeners
function createWidget() {
  const handler = () => console.log("click");
  document.addEventListener("click", handler);
  return () => document.removeEventListener("click", handler);
}
```

```java
// WRONG: String concatenation in hot path
String result = "";
for (Item item : largeList) {
    result += item.toString();  // O(n^2) — new String each iteration
}

// CORRECT: StringBuilder
StringBuilder sb = new StringBuilder();
for (Item item : largeList) {
    sb.append(item.toString());
}
String result = sb.toString();
```

## Common Mistakes
The most expensive performance anti-patterns are N+1 queries (multiply DB round trips by data size), unbounded collections (OOM on large datasets), and missing indexes (full table scans). Synchronous blocking in async code defeats concurrency. String concatenation in loops is O(n^2). Missing connection pooling creates TCP overhead on every request.

## Gotchas
- N+1 queries are often invisible in development with small data — only appear in production
- `SELECT *` returns all columns including large text/blob fields — select only what you need
- Pagination without `ORDER BY` returns inconsistent results between pages
- `LIMIT` without index still scans all rows — PostgreSQL stops early but still reads
- Connection pools need sizing — too small causes waiting, too large exhausts DB connections
- Caching stale data is worse than no cache — design invalidation strategy upfront
- `async` functions that call sync I/O block the entire event loop
- Memory leaks from closures capturing large objects are hard to detect

## Related
- db/postgres/indexing-strategies.md
- db/postgres/query-optimization.md
- performance/caching-strategies.md
- python/stdlib/asyncio-basics.md
