---
id: "patterns-graceful-degradation"
title: "Graceful Degradation Pattern"
language: "multi"
category: "patterns"
tags: ["patterns", "resilience", "fault-tolerance", "circuit-breaker", "fallback"]
version: "n/a"
retrieval_hint: "graceful degradation fallback circuit breaker resilience pattern"
last_verified: "2026-05-24"
confidence: "high"
---

# Graceful Degradation Pattern

## When to Use
- External service dependencies that may fail or be slow
- Reducing impact of downstream outages on user experience
- Serving stale data when fresh data is unavailable
- Preventing cascading failures in distributed systems

## Standard Pattern

```python
import time
import logging
from typing import Any, Callable, TypeVar
from functools import wraps
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

T = TypeVar("T")


# === Circuit Breaker ===
class CircuitBreaker:
    """Prevent repeated calls to a failing dependency."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.state = "CLOSED"  # CLOSED → OPEN → HALF_OPEN

    def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T | None:
        if self.state == "OPEN":
            if time.monotonic() - (self.last_failure_time or 0) > self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker: HALF_OPEN — probing")
            else:
                logger.warning("Circuit breaker: OPEN — fast failing")
                return None

        try:
            result = func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
                logger.info("Circuit breaker: CLOSED — recovery successful")
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.monotonic()
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                logger.error(f"Circuit breaker: OPEN after {self.failure_count} failures")
            logger.warning(f"Call failed ({self.failure_count}/{self.failure_threshold}): {e}")
            return None


# === Fallback Cache ===
class FallbackCache:
    """Serve stale cached data when the source is unavailable."""

    def __init__(self, default_ttl: int = 300):
        self._cache: dict[str, tuple[Any, datetime]] = {}
        self.default_ttl = default_ttl

    def get_or_fetch(
        self, key: str, fetch_func: Callable[[], T], ttl: int | None = None
    ) -> T | None:
        """Try fetching fresh data; fall back to stale cache on failure."""
        ttl = ttl or self.default_ttl
        now = datetime.now(timezone.utc)

        try:
            fresh_data = fetch_func()
            self._cache[key] = (fresh_data, now)
            return fresh_data
        except Exception as e:
            logger.warning(f"Fetch failed for {key}, trying cache: {e}")
            if key in self._cache:
                cached_value, cached_time = self._cache[key]
                age = (now - cached_time).total_seconds()
                logger.info(f"Serving stale cache for {key} (age: {age:.0f}s)")
                return cached_value
            return None  # No cache available either


# === Feature Flag Degradation ===
from enum import Enum

class DegradationLevel(Enum):
    FULL = "full"          # All features available
    DEGRADED = "degraded"  # Non-critical features disabled
    MINIMAL = "minimal"    # Only read-only/critical features
    OFFLINE = "offline"    # Service unavailable

class DegradationManager:
    """Control feature availability based on system health."""

    def __init__(self):
        self.level = DegradationLevel.FULL

    def is_enabled(self, feature: str, min_level: DegradationLevel = DegradationLevel.FULL) -> bool:
        """Check if a feature should be available at current degradation level."""
        levels = {
            DegradationLevel.FULL: 3,
            DegradationLevel.DEGRADED: 2,
            DegradationLevel.MINIMAL: 1,
            DegradationLevel.OFFLINE: 0,
        }
        return levels[self.level] >= levels[min_level]


# === Usage ===
circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=10.0)
cache = FallbackCache(default_ttl=60)
degradation = DegradationManager()


def fetch_user_profile(user_id: int) -> dict | None:
    """Fetch user profile with graceful degradation."""
    result = circuit_breaker.call(
        lambda: cache.get_or_fetch(
            f"user:{user_id}",
            lambda: call_user_service(user_id),  # Replace with actual call
        )
    )

    if result is None and degradation.level in (DegradationLevel.MINIMAL, DegradationLevel.OFFLINE):
        return {"id": user_id, "name": "Unavailable", "status": "degraded"}

    return result


def call_user_service(user_id: int) -> dict:
    """Simulated external call that may fail."""
    # In production: requests.get(f"http://user-service/users/{user_id}")
    raise ConnectionError("User service unreachable")
```

## Common Mistakes

```python
# WRONG: No fallback, crash on dependency failure
def get_user_orders(user_id: int):
    response = requests.get(f"http://orders/users/{user_id}/orders")
    response.raise_for_status()  # Crash if orders service is down
    return response.json()

# CORRECT: Return degraded response
def get_user_orders(user_id: int):
    try:
        response = requests.get(
            f"http://orders/users/{user_id}/orders", timeout=2
        )
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ConnectionError):
        logger.warning(f"Orders service unavailable for user {user_id}")
        return {"orders": [], "status": "degraded", "message": "Order history temporarily unavailable"}


# WRONG: No timeout on fallback (fallback itself hangs)
def fetch_prices():
    return requests.get("http://prices/api/prices", timeout=30)  # Hangs for 30s!

# CORRECT: Short timeout with fast fallback
def fetch_prices():
    try:
        return requests.get("http://prices/api/prices", timeout=1)
    except requests.Timeout:
        return {"prices": None, "status": "stale"}  # Fast fallback


# WRONG: Degradation without monitoring — you don't know it's happening
def get_recommendations(user_id: int):
    return fallback_cache.get_or_fetch(
        f"recs:{user_id}",
        lambda: call_rec_service(user_id),
    )
    # No logging or metrics — silent degradation

# CORRECT: Log and track degradation
def get_recommendations(user_id: int):
    result = fallback_cache.get_or_fetch(
        f"recs:{user_id}",
        lambda: call_rec_service(user_id),
    )
    if result is None:
        logger.warning(f"Recommendations degraded for user {user_id}")
        metrics.increment("recommendations.degraded")
    return result
```

## Gotchas
- **Partial degradation is hard**: Some features depend on others. Degrading the recommendations service might also affect the homepage, search, and notifications. Map dependency chains before implementing degradation.
- **Monitoring is mandatory**: Graceful degradation without monitoring is invisible failure. Always log degradation events and set up alerts for increased fallback rates.
- **Cascading fallbacks**: A fallback that calls another fallback can create deep chains that are hard to debug. Limit fallback depth to 1 level.
- **Cache stampede**: When a cached value expires and multiple requests try to refresh it simultaneously, the upstream service gets hammered. Use a "lock around refresh" pattern or `stale-while-revalidate`.
- **Feature flag complexity**: Degradation levels must be tested at each level. A feature that works at FULL might break at MINIMAL if it assumes all dependencies are available.
- **User experience**: Communicate degradation to users. A message like "Some features are temporarily limited" is better than silent missing data.
- **Recovery testing**: The circuit breaker's HALF_OPEN state must actually probe the downstream service, not just assume recovery after a timeout.

## Related
- patterns/health-checks.md
- patterns/rate-limiting.md
- error-handling/structured-errors.md
