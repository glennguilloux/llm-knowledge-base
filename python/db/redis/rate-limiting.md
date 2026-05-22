---
id: "python-db-redis-rate-limiting"
title: "Redis Rate Limiting Patterns"
language: "python"
category: "db"
subcategory: "cache"
tags: ["redis", "rate-limit", "token-bucket", "sliding-window", "throttle"]
version: "3.10+"
retrieval_hint: "Redis rate limiting token bucket sliding window throttle API limit"
last_verified: "2026-05-22"
confidence: "high"
---

# Redis Rate Limiting Patterns

## When to Use
- API rate limiting (requests per minute per user/IP)
- Protecting backend services from overload
- Implementing fair usage policies for SaaS APIs
- Throttling webhook delivery or external API calls

## Standard Pattern

```python
import redis
import time
from functools import wraps
from fastapi import HTTPException, Request

r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)


# --- Sliding Window (sorted sets) ---
def is_rate_limited_sliding(key: str, limit: int, window_seconds: int) -> tuple[bool, dict]:
    """Returns (is_limited, info_dict)."""
    now = time.time()
    window_start = now - window_seconds

    pipe = r.pipeline()
    pipe.zremrangebyscore(key, 0, window_start)  # Remove expired entries
    pipe.zadd(key, {f"{now}:{id(object())}": now})  # Add current request
    pipe.zcard(key)  # Count in window
    pipe.expire(key, window_seconds)  # Auto-cleanup
    _, _, count, _ = pipe.execute()

    remaining = max(0, limit - count)
    return count > limit, {
        "limit": limit,
        "remaining": remaining,
        "reset": int(now + window_seconds),
    }


# --- Token Bucket ---
def is_rate_limited_token_bucket(key: str, capacity: int, refill_rate: float) -> tuple[bool, dict]:
    """Token bucket: allows bursts up to capacity, refills over time."""
    now = time.time()

    lua_script = """
    local key = KEYS[1]
    local capacity = tonumber(ARGV[1])
    local refill_rate = tonumber(ARGV[2])
    local now = tonumber(ARGV[3])

    local data = redis.call('HMGET', key, 'tokens', 'last_refill')
    local tokens = tonumber(data[1]) or capacity
    local last_refill = tonumber(data[2]) or now

    -- Refill tokens
    local elapsed = now - last_refill
    tokens = math.min(capacity, tokens + elapsed * refill_rate)

    local allowed = tokens >= 1
    if allowed then
        tokens = tokens - 1
    end

    redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
    redis.call('EXPIRE', key, math.ceil(capacity / refill_rate) * 2)

    return {allowed and 1 or 0, tokens}
    """
    result = r.eval(lua_script, 1, key, capacity, refill_rate, now)
    allowed = result[0] == 1
    tokens = result[1]

    return not allowed, {
        "limit": capacity,
        "remaining": int(tokens),
    }


# --- Fixed Window (simplest) ---
def is_rate_limited_fixed(key: str, limit: int, window_seconds: int) -> tuple[bool, dict]:
    """Simple counter per window. Less smooth than sliding window."""
    current = r.get(key)
    if current and int(current) >= limit:
        return True, {"limit": limit, "remaining": 0}

    pipe = r.pipeline()
    pipe.incr(key)
    pipe.expire(key, window_seconds)  # Set expiry only on first increment
    count, _ = pipe.execute()

    return False, {"limit": limit, "remaining": limit - count}


# --- FastAPI middleware ---
def rate_limit_middleware(limit: int = 100, window: int = 60):
    def dependency(request: Request):
        client_ip = request.client.host
        key = f"rate:{client_ip}"
        limited, info = is_rate_limited_sliding(key, limit, window)
        if limited:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Remaining": str(info["remaining"]),
                    "X-RateLimit-Reset": str(info["reset"]),
                    "Retry-After": str(window),
                },
            )
    return dependency
```

## Common Mistakes

```python
# WRONG: Using INCR without TTL (counter never resets)
r.incr(f"rate:{ip}")
# Counter grows forever, rate limiting becomes permanent

# CORRECT: Set TTL on first increment
pipe = r.pipeline()
pipe.incr(f"rate:{ip}")
pipe.expire(f"rate:{ip}", 60)
count, _ = pipe.execute()

# WRONG: Race condition in check-then-set
count = int(r.get(f"rate:{ip}") or 0)
if count < limit:  # Another request could increment between check and set
    r.incr(f"rate:{ip}")

# CORRECT: Use atomic operations (INCR returns new count)
count = r.incr(f"rate:{ip}")
if count == 1:
    r.expire(f"rate:{ip}", 60)
if count > limit:
    raise HTTPException(status_code=429)

# WRONG: Using KEYS command to find rate limit keys
keys = r.keys("rate:*")  # Blocks Redis — O(n) scan!

# CORRECT: Use specific keys, never scan
key = f"rate:{client_ip}"
```

## Gotchas
- Sliding window with sorted sets is the most accurate but uses more memory
- Token bucket allows bursts — good for APIs with variable traffic patterns
- Fixed window has edge cases at window boundaries (2x burst possible)
- Lua scripts are atomic in Redis — use for complex multi-step operations
- `INCR` + `EXPIRE` has a race condition on first request — use pipeline or Lua
- Rate limit by IP, user ID, or API key depending on your use case
- Return `429 Too Many Requests` with `Retry-After` header for HTTP APIs
- Redis memory: sorted sets grow with requests — always set `EXPIRE` on keys

## Related
- python/db/redis/patterns.md
- python/web/fastapi/middleware.md
- patterns/rate-limiting.md
