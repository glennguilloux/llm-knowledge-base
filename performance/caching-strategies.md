---
id: "performance-caching-strategies"
title: "Caching Strategies and Patterns"
language: "multi"
category: "performance"
tags: ["performance", "caching", "redis", "cdn", "cache-aside", "ttl"]
version: "n/a"
retrieval_hint: "caching strategy Redis CDN cache-aside TTL invalidation write-through"
last_verified: "2026-05-22"
confidence: "high"
---

# Caching Strategies and Patterns

## When to Use
- Reducing database load for frequently-read data
- Speeding up API response times
- Reducing external API calls
- Serving static assets efficiently

## Standard Pattern

```python
import redis
import json
from functools import wraps
from datetime import timedelta

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

# === Cache-Aside (Lazy Loading) ===
# Read: check cache → miss → read DB → write cache → return
# Write: update DB → invalidate cache
def get_user(user_id: int) -> dict | None:
    cache_key = f"user:{user_id}"
    cached = r.get(cache_key)
    if cached:
        return json.loads(cached)

    user = db.query("SELECT * FROM users WHERE id = %s", (user_id,))
    if user:
        r.setex(cache_key, timedelta(minutes=5), json.dumps(user))
    return user

def update_user(user_id: int, data: dict):
    db.execute("UPDATE users SET name=%s WHERE id=%s", (data["name"], user_id))
    r.delete(f"user:{user_id}")  # Invalidate cache

# === Write-Through ===
# Write: update cache AND DB simultaneously
def update_user_writethrough(user_id: int, data: dict):
    db.execute("UPDATE users SET name=%s WHERE id=%s", (data["name"], user_id))
    r.setex(f"user:{user_id}", timedelta(minutes=5), json.dumps(data))  # Update cache

# === Cache with Decorator ===
def cached(ttl: timedelta, key_prefix: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}:{args}:{kwargs}"
            result = r.get(cache_key)
            if result:
                return json.loads(result)
            result = func(*args, **kwargs)
            r.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator

@cached(ttl=timedelta(minutes=10), key_prefix="products")
def get_product(product_id: int) -> dict:
    return db.query("SELECT * FROM products WHERE id = %s", (product_id,))

# === Cache Stampede Prevention ===
# Use lock to prevent multiple processes from rebuilding the same cache
def get_with_lock(key: str, fetch_fn, ttl: int = 300):
    value = r.get(key)
    if value:
        return json.loads(value)

    lock_key = f"lock:{key}"
    if r.set(lock_key, "1", nx=True, ex=10):  # Acquired lock
        try:
            value = fetch_fn()
            r.setex(key, ttl, json.dumps(value))
            return value
        finally:
            r.delete(lock_key)
    else:
        # Another process is building — wait and retry
        import time
        time.sleep(0.1)
        return get_with_lock(key, fetch_fn, ttl)

# === Cache Invalidation Patterns ===
# TTL-based: cache expires automatically
r.setex("config:settings", 3600, json.dumps(settings))  # 1 hour TTL

# Event-based: invalidate on data change
def on_user_updated(user_id: int):
    r.delete(f"user:{user_id}")  # Immediate invalidation
```

```python
# === HTTP Caching ===
from fastapi import FastAPI, Response

app = FastAPI()

@app.get("/api/users/{user_id}")
async def get_user(user_id: int, response: Response):
    user = await fetch_user(user_id)

    # ETag: hash of response content
    etag = hashlib.md5(json.dumps(user).encode()).hexdigest()
    response.headers["ETag"] = f'"{etag}"'
    response.headers["Cache-Control"] = "private, max-age=60"  # 1 minute browser cache

    return user

# CDN caching for public content
@app.get("/api/products")
async def list_products(response: Response):
    response.headers["Cache-Control"] = "public, max-age=300, s-maxage=600"
    # s-maxage for CDN, max-age for browser
    return await fetch_products()
```

```javascript
// === Client-Side Caching with SWR ===
import useSWR from 'swr';

function UserProfile({ userId }) {
    const { data, error } = useSWR(`/api/users/${userId}`, fetcher, {
        revalidateOnFocus: true,     // Refetch when window gets focus
        revalidateOnReconnect: true,  // Refetch on network reconnect
        dedupingInterval: 5000,       // Dedupe requests within 5s
    });
    if (error) return <div>Error</div>;
    if (!data) return <div>Loading...</div>;
    return <div>{data.name}</div>;
}
```

## Common Mistakes

```python
# WRONG: Caching user-specific data with public cache
response.headers["Cache-Control"] = "public, max-age=3600"  # User A sees User B's data

# CORRECT: Use "private" for user-specific data
response.headers["Cache-Control"] = "private, max-age=60"

# WRONG: No cache invalidation on data change
r.setex(f"user:{user_id}", 3600, json.dumps(user))
# User updates their profile — cache serves stale data for up to 1 hour

# CORRECT: Invalidate on write
def update_user(user_id, data):
    db.update(user_id, data)
    r.delete(f"user:{user_id}")

# WRONG: Caching without TTL (memory leak)
r.set("config", json.dumps(data))  # Lives forever

# CORRECT: Always set TTL
r.setex("config", 3600, json.dumps(data))

# WRONG: Caching everything (cache pollution)
r.setex(f"user:{user_id}:temp_calc", 60, json.dumps(expensive_result))
# Low hit rate wastes Redis memory

# CORRECT: Cache only frequently-accessed, expensive-to-compute data

# WRONG: Large values in Redis
r.set("all_users", json.dumps(million_users))  # 100MB+ in Redis

# CORRECT: Cache individual items or small collections
for user in users:
    r.setex(f"user:{user['id']}", 300, json.dumps(user))
```

## Gotchas
- Cache-Aside is the most common pattern — simple, flexible, and well-understood
- Write-Through ensures cache consistency but adds write latency
- Write-Behind (write-back) is fastest but risks data loss on cache failure
- TTL is the simplest invalidation — choose based on staleness tolerance
- Cache stampede (thundering herd) happens when many requests rebuild the same cache — use locks
- ETags enable conditional requests (`If-None-Match`) — returns 304 Not Modified
- `s-maxage` controls CDN cache; `max-age` controls browser cache — set both
- `Vary: Authorization` header prevents serving one user's cached response to another
- Redis eviction policies (`allkeys-lru`, `volatile-lru`) matter when memory is full
- Monitor cache hit rate — below 80% means the cache isn't helping

## Related
- api-design/rest-conventions.md
- performance/anti-patterns.md
- csharp/db/entity-framework.md
