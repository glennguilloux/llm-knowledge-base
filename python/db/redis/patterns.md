---
id: "python-db-redis-patterns"
title: "Redis Caching and Pub/Sub Patterns"
language: "python"
category: "db"
subcategory: "cache"
tags: ["redis", "cache", "pubsub", "rate-limit", "session", "async"]
version: "3.10+"
retrieval_hint: "Redis cache pub/sub rate limiting session TTL invalidation"
last_verified: "2026-05-24"
confidence: "high"
---

# Redis Caching and Pub/Sub Patterns

## When to Use
- Caching expensive database queries or API responses
- Rate limiting API endpoints (token bucket, sliding window)
- Real-time messaging between services via Pub/Sub
- Session storage, OTP codes, or temporary tokens with TTL

## Standard Pattern

```python
import redis
import json
import time
from typing import Any
from functools import wraps

# --- Connection ---
r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# --- Basic caching with TTL ---
def cache_get(key: str) -> Any | None:
    data = r.get(key)
    return json.loads(data) if data else None


def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    r.setex(key, ttl, json.dumps(value))


def cache_delete(key: str) -> None:
    r.delete(key)


# --- Cache decorator ---
def cached(prefix: str, ttl: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{prefix}:{hash(str(args) + str(kwargs))}"
            result = cache_get(cache_key)
            if result is not None:
                return result
            result = await func(*args, **kwargs)
            cache_set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator


@cached("user", ttl=600)
async def get_user(user_id: int) -> dict:
    # Expensive DB query
    return await db.fetch_user(user_id)


# --- Rate limiting (sliding window) ---
def is_rate_limited(key: str, limit: int, window: int) -> bool:
    """Returns True if rate limit exceeded."""
    now = time.time()
    pipe = r.pipeline()
    pipe.zremrangebyscore(key, 0, now - window)  # Remove old entries
    pipe.zadd(key, {str(now): now})              # Add current request
    pipe.zcard(key)                               # Count requests in window
    pipe.expire(key, window)                      # Auto-cleanup
    results = pipe.execute()
    return results[2] > limit


# --- Pub/Sub ---
def publish_event(channel: str, data: dict) -> None:
    r.publish(channel, json.dumps(data))


def subscribe_events(channel: str, callback):
    pubsub = r.pubsub()
    pubsub.subscribe(channel)
    for message in pubsub.listen():
        if message["type"] == "message":
            data = json.loads(message["data"])
            callback(data)


# --- Distributed lock ---
def acquire_lock(name: str, timeout: int = 10) -> bool:
    return r.set(f"lock:{name}", "1", nx=True, ex=timeout)


def release_lock(name: str) -> None:
    r.delete(f"lock:{name}")


# --- Async Redis (with redis.asyncio) ---
import redis.asyncio as aioredis

async_r = aioredis.Redis(host="localhost", port=6379, decode_responses=True)


async def async_cache_get(key: str) -> Any | None:
    data = await async_r.get(key)
    return json.loads(data) if data else None
```

## Common Mistakes

```python
# WRONG: Caching without TTL (memory leak)
r.set("user:1", json.dumps(user_data))  # Lives forever, Redis runs out of memory

# CORRECT: Always set TTL
r.setex("user:1", 300, json.dumps(user_data))  # Expires in 5 minutes

# WRONG: Cache stampede — many requests miss cache simultaneously
async def get_data(key: str):
    cached = r.get(key)
    if cached:
        return json.loads(cached)
    # 100 requests hit this line at once when cache expires
    result = await expensive_query()
    r.setex(key, 300, json.dumps(result))
    return result

# CORRECT: Use lock to prevent stampede
async def get_data(key: str):
    cached = r.get(key)
    if cached:
        return json.loads(cached)
    if r.set(f"lock:{key}", "1", nx=True, ex=10):  # Only one request fetches
        result = await expensive_query()
        r.setex(key, 300, json.dumps(result))
        r.delete(f"lock:{key}")
        return result
    await asyncio.sleep(0.1)  # Other requests wait and retry
    return await get_data(key)

# WRONG: Using WRONG data type for rate limiting
r.incr(f"rate:{ip}")  # Counter never resets properly

# CORRECT: Use sliding window with sorted sets
def is_rate_limited(key: str, limit: int, window: int) -> bool:
    now = time.time()
    r.zremrangebyscore(key, 0, now - window)
    r.zadd(key, {str(now): now})
    return r.zcard(key) > limit
```

## Gotchas
- `decode_responses=True` returns strings instead of bytes — set it at connection level
- Redis Pub/Sub is fire-and-forget — messages are not persisted; use Streams for durability
- `SET key value NX EX ttl` is atomic — use for distributed locks, not `SETNX` + `EXPIRE`
- Pipeline batches commands to reduce round trips — always use for multi-key operations
- Redis single-threaded — long-running Lua scripts block all clients
- Use `SCAN` instead of `KEYS` in production (`KEYS *` blocks the server)
- `redis.asyncio` is the async client (Python 3.10+); `aioredis` is deprecated

## Related
- python/db/sqlalchemy-2.0/async-sessions.md
- python/web/fastapi/dependency-injection.md
- performance/caching-strategies.md
