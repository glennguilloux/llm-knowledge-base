---
id: "anti-patterns-python-lru-cache-memory-leak"
title: "Python Anti-Pattern: lru_cache Memory Leak"
language: "python"
category: "anti-patterns"
tags: ["antipatterns", "python", "lru_cache", "functools", "memory", "caching", "performance"]
version: "n/a"
retrieval_hint: "lru_cache unbounded memory leak maxsize=None functools cache decorator unhashable arguments method instance reference"
last_verified: "2026-05-24"
confidence: "high"
---

# Python Anti-Pattern: lru_cache Memory Leak

## When to Use
- Caching expensive function calls where inputs are bounded in practice
- Reviewing code for uncontrolled memory growth from memoization
- Understanding when `lru_cache` creates object reference cycles
- Choosing between `lru_cache`, `cache`, `cached_property`, and manual caches

## Standard Pattern

```python
from functools import lru_cache, cache
import time
import sys

# ---------------------------------------------------------------------------
# WRONG: Unbounded lru_cache on dynamic/arbitrary input
# ---------------------------------------------------------------------------

# WRONG: maxsize=None means unlimited growth — memory leak on dynamic data
@lru_cache(maxsize=None)
def expensive_api_call(user_id: str) -> dict:
    # Imagine this calls an external API with different user_ids
    # If user_ids are unbounded (e.g., ever-growing customer base),
    # this cache grows forever
    return {"id": user_id, "data": "..."}

# If this is called with 1 million different user_ids over a day,
# the cache holds 1 million entries — a memory leak by design

# CORRECT: Bound the cache size
@lru_cache(maxsize=1000)
def expensive_api_call(user_id: str) -> dict:
    return {"id": user_id, "data": "..."}

# Or use a TTL-based approach (lru_cache has no built-in TTL)
from functools import lru_cache, wraps
import time

def ttl_lru_cache(seconds: int = 300, maxsize: int = 128):
    def decorator(func):
        func = lru_cache(maxsize=maxsize)(func)
        func._ttl = seconds
        func._last_clear = time.monotonic()

        @wraps(func)
        def wrapper(*args, **kwargs):
            if time.monotonic() - func._last_clear > func._ttl:
                func.cache_clear()
                func._last_clear = time.monotonic()
            return func(*args, **kwargs)
        return wrapper
    return decorator

# ---------------------------------------------------------------------------
# WRONG: lru_cache on methods (instance reference leak)
# ---------------------------------------------------------------------------

# WRONG: lru_cache on a method caches self, preventing GC
class DataProcessor:
    def __init__(self, data_id: str):
        self.data_id = data_id
        self._large_data = "X" * 10_000_000  # 10MB

    @lru_cache(maxsize=128)
    def compute(self, param: str) -> str:
        # self is part of the cache key! The instance can't be GC'd
        # while the cache holds references to its results
        return f"{self.data_id}:{param}"

# Every DataProcessor instance with cached results stays alive forever
# Even after you delete all references to the processor:
p = DataProcessor("abc")
p.compute("x")
del p  # NOT collected — lru_cache holds reference via self

# WRONG: Also creates CacheData.report (self.__class__) as part of hash
print(sys.getsizeof(DataProcessor.compute.cache_info().currsize))  # wrong approach, but use cache_clear()

# CORRECT: Make cache key explicit — don't let self leak
class DataProcessor:
    def __init__(self, data_id: str):
        self.data_id = data_id
        self._large_data = "X" * 10_000_000

    def compute(self, param: str) -> str:
        return self._cached_compute(self.data_id, param)

    @staticmethod
    @lru_cache(maxsize=128)
    def _cached_compute(data_id: str, param: str) -> str:
        return f"{data_id}:{param}"

# Now instances can be GC'd normally — the cache key is just (data_id, param)

# ---------------------------------------------------------------------------
# WRONG: @cache (Python 3.9+) is just lru_cache(maxsize=None)
# ---------------------------------------------------------------------------

# WRONG: @cache is unbounded by default
@cache
def fetch_config(env: str) -> dict:
    return {"env": env}

# CORRECT: Use @lru_cache(maxsize=...) when bounded
@lru_cache(maxsize=50)
def fetch_config(env: str) -> dict:
    return {"env": env}

# ---------------------------------------------------------------------------
# WRONG: Unhashable arguments (TypeError)
# ---------------------------------------------------------------------------

# WRONG: Lists and dicts can't be cached
@lru_cache(maxsize=128)
def process_items(items: list[str]) -> int:  # TypeError: unhashable type: 'list'
    return len(items)

# CORRECT: Convert to hashable types
@lru_cache(maxsize=128)
def process_items(items: tuple[str, ...]) -> int:
    return len(items)

# Or use a helper for dicts
@lru_cache(maxsize=128)
def process_config(config_json: str) -> dict:
    """Pass JSON string instead of dict — string is hashable."""
    import json
    return json.loads(config_json)

# ---------------------------------------------------------------------------
# WRONG: Large return values in cache (memory pressure)
# ---------------------------------------------------------------------------

# WRONG: Caching a function that returns 100MB DataFrames
@lru_cache(maxsize=1000)
def load_large_dataset(date: str):
    # Returns huge data — 1000 * 100MB = 100GB in cache
    return load_parquet(f"data_{date}.parquet")

# CORRECT: Be cache-size aware
@lru_cache(maxsize=5)
def load_large_dataset(date: str):
    return load_parquet(f"data_{date}.parquet")

# ---------------------------------------------------------------------------
# WRONG: Not clearing cache when dependencies change
# ---------------------------------------------------------------------------

config = {"db_url": "old"}

@lru_cache(maxsize=32)
def get_connection_pool():
    return create_pool(config["db_url"])

# config changes, but cache isn't cleared!
config["db_url"] = "new"
# get_connection_pool() still returns the old pool

# CORRECT: Clear cache after mutation
config["db_url"] = "new"
get_connection_pool.cache_clear()
```

## Common Mistakes
The most dangerous pattern is `@lru_cache(maxsize=None)` (or `@cache` in 3.9+) on functions called with unbounded input — it's a guaranteed memory leak. Second: using `@lru_cache` on instance methods — the `self` parameter becomes part of the cache key, preventing garbage collection of the instance. Third: not considering the memory cost of cached return values — a function returning multi-MB results with `maxsize=1000` can consume gigabytes.

## Gotchas
- `@lru_cache(maxsize=None)` and `@cache` (3.9+) are unbounded — they will grow until they consume all available memory given diverse inputs
- Instance methods with `@lru_cache` capture `self` as the first cache key argument — this creates an implicit reference that prevents GC, effectively a memory leak for ephemeral objects
- `lru_cache` raises `TypeError` for unhashable arguments (list, dict, set) — convert to tuple, frozenset, or string keys
- `cache_info()` returns `CacheInfo(hits, misses, maxsize, currsize)` — monitor `currsize` in production to detect leaks
- `cache_clear()` resets the cache but does NOT free memory immediately if other references exist to return values
- `lru_cache` is NOT thread-safe by default — concurrent writes can lose entries (use `RLock` if strict accuracy is needed)
- `functools.cached_property` is for instance properties that are computed once and cached on the instance — it's different from `lru_cache`
- Decorator ordering matters: `@lru_cache` above `@staticmethod` breaks; `@lru_cache` below `@property` is wrong
- `lru_cache` stores results indefinitely — there is no built-in TTL/expiry mechanism
- `cache_clear()` clears ALL entries, not selective ones — use `cache` parameter or `cache_parameters()` for inspection
- The `typed` parameter (`@lru_cache(typed=True)`) distinguishes `1` from `1.0` as separate cache entries — useful but doubles entries for numeric-heavy workloads
- `lru_cache` on recursive functions like Fibonacci creates exponential cache entries in the call graph — this is usually desired but doubles memory during deep recursion

## Related
- anti-patterns/python-antipatterns.md
- python/stdlib/decorators.md
