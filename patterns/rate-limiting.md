---
id: "patterns-rate-limiting"
title: "Rate Limiting Patterns"
language: "multi"
category: "patterns"
subcategory: "api-design"
tags: ["rate-limiting", "token-bucket", "sliding-window", "throttle", "api"]
version: ""
retrieval_hint: "Rate limiting token bucket sliding window throttle API 429"
last_verified: "2026-05-22"
confidence: "high"
---

# Rate Limiting Patterns

## When to Use
- Protecting APIs from abuse and overload
- Enforcing fair usage policies (SaaS rate limits)
- Preventing brute-force attacks on authentication endpoints
- Throttling webhook delivery or external API calls

## Standard Pattern

```python
# --- Sliding Window (Redis) ---
import time
import redis

r = redis.Redis()

def is_rate_limited(key: str, limit: int, window: int) -> tuple[bool, dict]:
    now = time.time()
    pipe = r.pipeline()
    pipe.zremrangebyscore(key, 0, now - window)
    pipe.zadd(key, {f"{now}": now})
    pipe.zcard(key)
    pipe.expire(key, window)
    _, _, count, _ = pipe.execute()
    return count > limit, {"limit": limit, "remaining": max(0, limit - count)}

# --- Token Bucket (allows bursts) ---
# Capacity: max tokens, Refill: tokens per second
# Allows bursts up to capacity, then throttles to refill rate
```

```typescript
// --- Express middleware ---
import rateLimit from "express-rate-limit";

const limiter = rateLimit({
  windowMs: 60 * 1000,     // 1 minute
  max: 100,                 // 100 requests per window
  standardHeaders: true,    // Return rate limit info in headers
  legacyHeaders: false,
  message: { error: "Too many requests" },
});

app.use("/api/", limiter);

// --- Per-user rate limiting ---
const userLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: 1000,
  keyGenerator: (req) => req.user?.id || req.ip,
});
```

```go
// --- Go middleware with Redis ---
func rateLimitMiddleware(rdb *redis.Client, limit int, window time.Duration) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            key := fmt.Sprintf("rate:%s", r.RemoteAddr)
            count, _ := rdb.Incr(r.Context(), key).Result()
            if count == 1 {
                rdb.Expire(r.Context(), key, window)
            }
            if count > int64(limit) {
                w.Header().Set("Retry-After", fmt.Sprintf("%d", int(window.Seconds())))
                http.Error(w, "Rate limit exceeded", 429)
                return
            }
            w.Header().Set("X-RateLimit-Limit", fmt.Sprintf("%d", limit))
            w.Header().Set("X-RateLimit-Remaining", fmt.Sprintf("%d", limit-int(count)))
            next.ServeHTTP(w, r)
        })
    }
}
```

## Common Mistakes

```text
# WRONG: Using a simple counter without TTL
INCR rate:{ip}
# Counter grows forever — rate limiting becomes permanent

# CORRECT: Set TTL on first increment
INCR rate:{ip}
EXPIRE rate:{ip} 60  # Only on first request

# WRONG: Check-then-set race condition
count = GET rate:{ip}
if count < limit:
    INCR rate:{ip}  # Another request may increment between check and set

# CORRECT: Use atomic INCR (returns new count)
count = INCR rate:{ip}
if count == 1: EXPIRE rate:{ip} 60
if count > limit: return 429
```

## Gotchas
- Sliding window is more accurate than fixed window (no burst at boundaries)
- Token bucket allows bursts — good for APIs with variable traffic
- Always return `429 Too Many Requests` with `Retry-After` header
- Rate limit by IP, user ID, or API key depending on use case
- Redis atomic operations prevent race conditions
- Use Lua scripts for complex multi-step rate limiting logic
- Consider separate limits for different endpoint categories (auth vs read)
- Client-side: respect `Retry-After` and implement exponential backoff

## Related
- python/db/redis/rate-limiting.md
- api-design/versioning.md
- security/web-security-basics.md
