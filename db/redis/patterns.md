---
id: "db-redis-patterns"
title: "Redis: Data Structures, Caching, Rate Limiting, Pub/Sub"
language: "multi"
category: "db"
tags: ["redis", "caching", "data-structures", "rate-limiting", "pub-sub", "sessions"]
version: "n/a"
retrieval_hint: "redis caching data structures strings hashes sets sorted sets rate limiting pub sub session store"
last_verified: "2026-05-24"
confidence: "high"
---

# Redis: Data Structures, Caching, Rate Limiting, Pub/Sub

## When to Use
- High-performance caching layer for databases and APIs
- Session store for distributed applications
- Real-time features: leaderboards, rate limiting, queues
- Pub/Sub messaging between services

## Standard Pattern

```bash
# === Core Data Structures ===

# --- Strings (most basic) ---
SET user:100:name "Alice"
SET user:100:login_count 0
INCR user:100:login_count         # → 1
GET user:100:name                 # → "Alice"
EXPIRE user:100:session 3600      # TTL in seconds
TTL user:100:session              # → remaining seconds

# Batch operations
MSET user:101:name "Bob" user:101:role "admin"
MGET user:101:name user:101:role


# --- Hashes (objects) ---
HSET user:200 name "Charlie" email "charlie@example.com" age 30
HGET user:200 email                      # → "charlie@example.com"
HGETALL user:200                         # → all fields
HINCRBY user:200 login_count 1           # Atomic increment

# Cache pattern: store entire object
HMSET product:42 name "Widget" price 9.99 stock 100


# --- Lists (ordered, duplicates allowed) ---
LPUSH notifications:user:300 "New message" "Friend request"
LRANGE notifications:user:300 0 -1       # All items
LLEN notifications:user:300              # Length
RPOP notifications:user:300              # Pop from right

# Use as queue
LPUSH task_queue "job:123"               # Enqueue
BRPOP task_queue 0                        # Blocking dequeue (0 = no timeout)


# --- Sets (unique, unordered) ---
SADD tags:article:42 "redis" "database" "performance"
SMEMBERS tags:article:42                 # All members
SISMEMBER tags:article:42 "redis"        # → 1 (true)
SINTER tags:article:42 tags:article:43   # Common tags
SUNION tags:article:42 tags:article:43   # Union


# --- Sorted Sets (unique, scored) ---
ZADD leaderboard 100 "player:1" 85 "player:2" 200 "player:3"
ZREVRANGE leaderboard 0 2 WITHSCORES     # Top 3
ZSCORE leaderboard "player:1"            # → 100
ZINCRBY leaderboard 10 "player:1"        # Add 10 points
ZRANK leaderboard "player:2"             # Rank (0-based, low to high)


# === Caching Patterns ===

# --- Cache-Aside (lazy loading) ---
# Application code:
# key = "user:42"
# data = redis.get(key)
# if not data:
#     data = db.query("SELECT * FROM users WHERE id = 42")
#     redis.setex(key, 3600, data)
# return data

# --- Cache invalidation ---
# On write:
DEL "user:42:profile"                    # Delete cache
# Or set with TTL
SETEX "page:home" 300 "<html>...</html>"  # 5 minute TTL


# --- Rate Limiting ---

# Fixed window (simple)
INCR "rate_limit:api:user:100"           # → count
EXPIRE "rate_limit:api:user:100" 60      # Reset every 60s

# Sliding window (accurate)
# Lua script:
# local key = KEYS[1]
# local now = tonumber(ARGV[1])
# local window = tonumber(ARGV[2])
# local max = tonumber(ARGV[3])
# redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
# local count = redis.call('ZCARD', key)
# if count < max then
#     redis.call('ZADD', key, now, now)
#     return 1  # Allowed
# end
# return 0  # Rate limited


# === Session Store ===

# Store session
SETEX "session:abc123" 86400 '{"user_id":42,"role":"admin"}'

# Session with hash (easier partial updates)
HSET "session:xyz789" user_id 42 created_at "2025-05-23"
EXPIRE "session:xyz789" 86400


# === Pub/Sub ===

# Publisher (any client)
PUBLISH "channel:orders" '{"event":"new","order_id":123}'

# Subscriber (separate connection)
SUBSCRIBE "channel:orders"
# Messages arrive as: [message, channel, payload]


# === Distributed Lock ===

# Lock
SET lock:resource:42 "instance:1" NX EX 10
# NX = set only if not exists
# EX 10 = expire after 10 seconds

# Release (with Lua for atomicity)
# if redis.call("GET", KEYS[1]) == ARGV[1] then
#     return redis.call("DEL", KEYS[1])
# else
#     return 0
# end
```

## Common Mistakes

```bash
# WRONG: Using KEYS in production (blocking, O(N))
KEYS user:*        # Blocks Redis for millions of keys!

# CORRECT: Use SCAN (non-blocking cursor)
SCAN 0 MATCH "user:*" COUNT 100


# WRONG: No expiry on cache keys (memory leak)
SET "user:42:profile" "..."      # Forever in memory!

# CORRECT: Always set TTL for caches
SETEX "user:42:profile" 3600 "..."


# WRONG: Using Redis for complex queries
# SELECT * FROM users WHERE ... (many fields filtered)
# Redis cannot do arbitrary filtering

# CORRECT: Use Redis as cache, not primary query engine
# Cache hydrated objects, query database for complex filters


# WRONG: Large values in Redis (latency spike)
# > 10MB values block other operations

# CORRECT: Keep values small (under 10KB ideally)
# Split large blobs or use compression


# WRONG: Single Redis instance for everything (no isolation)
# Cache, sessions, queues, rate limits all on same instance

# CORRECT: Separate Redis instances or databases by use case
# db0 = cache, db1 = sessions, db2 = queues


# WRONG: Using Redis for durable data (no persistence guarantees)
# Default RDB snapshot every 5 minutes — data loss on crash

# CORRECT: Understand persistence tradeoffs
# AOF fsync=always: safest, ~50% slower
# AOF fsync=everysec: good balance
# RDB only: highest throughput, potential data loss
```

## Gotchas
- **Single-threaded event loop**: Redis processes commands sequentially. A single slow command (KEYS, large values, complex Lua scripts) blocks ALL other operations. Keep commands fast.
- **Memory management**: Redis lives entirely in RAM. Use `maxmemory` and `maxmemory-policy` (allkeys-lru for caches) to prevent out-of-memory crashes. Monitor with `INFO memory`.
- **Network round trips**: Each command is a TCP round trip. Use pipelines (`redis.pipeline()`) or batching for multiple operations. Lua scripts execute atomically server-side with no round trips.
- **Replication lag**: Redis replication is asynchronous. After a write to the primary, there's a brief window where replicas have stale data. Use `WAIT` for synchronous replication if needed.
- **Big keys (hot keys)**: A single key with millions of elements (e.g., a large set) can cause latency spikes for other operations. Use `redis-cli --bigkeys` to find them. Split across keys with sharding.
- **Eviction policies**: Default `noeviction` returns errors on writes when memory is full. For caches, use `allkeys-lru`. For session stores, `volatile-ttl` evicts keys with TTL set first.
- **Redis Cluster limitations**: Multi-key operations work only if all keys hash to the same slot. Transactions across slots are not supported. Use hash tags `{user:42}` to co-locate related keys.

## Related
- db/mysql/basics.md
- db/query-analysis.md
- db/sqlite/production.md
