---
id: "python-db-redis-basics"
title: "Redis Basics with redis-py"
language: "python"
category: "db"
subcategory: "cache"
tags: ["redis", "cache", "key-value", "session", "pub-sub"]
version: "3.10+"
retrieval_hint: "Redis cache key-value session pub-sub expire"
last_verified: "2026-05-24"
confidence: "high"
---

# Redis Basics with redis-py

## When to Use
- Caching frequently accessed data
- Session storage
- Rate limiting
- Pub/Sub messaging
- Distributed locks

## Standard Pattern

```python
import json
from datetime import timedelta
import redis


def create_redis_client(url: str = "redis://localhost:6379") -> redis.Redis:
    """Create a Redis client with connection pooling."""
    return redis.from_url(url, decode_responses=True)


r = create_redis_client()


# Basic operations
r.set("key", "value")
r.set("key", "value", ex=3600)  # Expires in 1 hour
r.set("key", "value", px=60000)  # Expires in 60 seconds
value = r.get("key")  # Returns str or None
r.delete("key")


# JSON storage
def cache_json(r: redis.Redis, key: str, data: dict, ttl: int = 3600) -> None:
    r.set(key, json.dumps(data), ex=ttl)


def get_cached_json(r: redis.Redis, key: str) -> dict | None:
    data = r.get(key)
    return json.loads(data) if data else None


# Hash operations (for structured data)
r.hset("user:1", mapping={"name": "Alice", "email": "alice@example.com"})
r.hget("user:1", "name")  # "Alice"
r.hgetall("user:1")  # {"name": "Alice", "email": "..."}
r.hdel("user:1", "email")


# List operations (for queues)
r.lpush("queue", "task1", "task2")
r.rpop("queue")  # "task1" (FIFO)


# Set operations
r.sadd("tags:post:1", "python", "fastapi")
r.smembers("tags:post:1")  # {"python", "fastapi"}
r.sismember("tags:post:1", "python")  # True


# Rate limiting
def is_rate_limited(r: redis.Redis, key: str, limit: int, window: int) -> bool:
    """Check if rate limit is exceeded."""
    current = r.incr(key)
    if current == 1:
        r.expire(key, window)
    return current > limit
```

## Common Mistakes

```python
# WRONG: Not setting expiration
r.set("cache:data", json.dumps(data))  # Lives forever, memory leak!

# CORRECT: Always set TTL for cache data
r.set("cache:data", json.dumps(data), ex=3600)

# WRONG: Storing complex objects directly
r.set("user", user_object)  # TypeError: can't serialize

# CORRECT: Serialize to JSON first
r.set("user", json.dumps(user_object.__dict__))

# WRONG: Not using connection pooling
for i in range(1000):
    r = redis.Redis()  # New connection each time!
    r.get(f"key:{i}")

# CORRECT: Reuse client (has built-in connection pooling)
r = redis.Redis()
for i in range(1000):
    r.get(f"key:{i}")
```

## Gotchas
- `decode_responses=True` returns strings instead of bytes
- `r.set(key, value, ex=seconds)` for expiration
- `r.get()` returns `None` for missing keys (no exception)
- Redis is single-threaded — operations are atomic
- Use `r.pipeline()` for batch operations (reduces round trips)
- Hash operations are more memory-efficient than JSON for small fields
- Use `r.exists(key)` to check if key exists without fetching value

## Related
- python/web/fastapi/basics.md
- python/patterns/retry-logic.md
