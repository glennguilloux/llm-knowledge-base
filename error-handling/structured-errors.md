---
id: "error-handling-structured-errors"
title: "Structured Error Handling Patterns"
language: "multi"
category: "error-handling"
tags: ["error-handling", "errors", "retry", "resilience", "circuit-breaker"]
version: "n/a"
retrieval_hint: "error handling structured retry circuit breaker resilience exponential backoff"
last_verified: "2026-05-24"
confidence: "high"
---

# Structured Error Handling Patterns

## When to Use
- Building APIs with consistent error responses
- Implementing retry logic for unreliable services
- Designing resilient distributed systems
- Handling transient failures gracefully

## Standard Pattern

```json
// === Standard Error Response ===
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid fields",
    "status": 422,
    "details": [
      { "field": "email", "code": "INVALID_FORMAT", "message": "Must be a valid email" },
      { "field": "age", "code": "OUT_OF_RANGE", "message": "Must be between 0 and 150" }
    ],
    "request_id": "req-abc-123",
    "timestamp": "2025-01-15T10:30:00Z"
  }
}
```

```python
# === Error Code Hierarchy ===
# App-level error codes (machine-readable)
ERROR_CODES = {
    "VALIDATION_ERROR": 422,
    "NOT_FOUND": 404,
    "UNAUTHORIZED": 401,
    "FORBIDDEN": 403,
    "CONFLICT": 409,
    "RATE_LIMITED": 429,
    "INTERNAL_ERROR": 500,
    "SERVICE_UNAVAILABLE": 503,
}

# Custom exception hierarchy
class AppError(Exception):
    def __init__(self, code: str, message: str, status: int = 500, details: list = None):
        self.code = code
        self.message = message
        self.status = status
        self.details = details or []

class NotFoundError(AppError):
    def __init__(self, resource: str, resource_id: str):
        super().__init__("NOT_FOUND", f"{resource} '{resource_id}' not found", 404)

class ValidationError(AppError):
    def __init__(self, details: list):
        super().__init__("VALIDATION_ERROR", "Invalid input", 422, details)

class ConflictError(AppError):
    def __init__(self, message: str):
        super().__init__("CONFLICT", message, 409)
```

```python
# === Retry with Exponential Backoff and Jitter ===
import time
import random
from functools import wraps

def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    retryable_exceptions: tuple = (ConnectionError, TimeoutError),
):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        raise
                    # Exponential backoff with jitter
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    jitter = random.uniform(0, delay * 0.5)
                    time.sleep(delay + jitter)
            raise last_exception
        return wrapper
    return decorator

@retry_with_backoff(max_retries=3, base_delay=0.5)
def call_external_api(url: str) -> dict:
    import httpx
    response = httpx.get(url, timeout=5.0)
    response.raise_for_status()
    return response.json()
```

```python
# === Circuit Breaker Pattern ===
import time
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"        # Normal operation
    OPEN = "open"            # Failing — reject calls
    HALF_OPEN = "half_open"  # Testing recovery

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0

    def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitOpenError("Circuit breaker is open")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

class CircuitOpenError(Exception):
    pass
```

```python
# === Graceful Degradation ===
async def get_product_with_fallback(product_id: int) -> dict:
    try:
        return await fetch_from_primary_db(product_id)
    except DatabaseError:
        try:
            return await fetch_from_read_replica(product_id)
        except DatabaseError:
            cached = await redis.get(f"product:{product_id}")
            if cached:
                return json.loads(cached)
            return {"id": product_id, "name": "Unavailable", "status": "degraded"}
```

## Common Mistakes

```python
# WRONG: Retrying non-idempotent operations blindly
@retry(max_retries=3)
def create_payment(amount: float):  # Creates duplicate payments!
    return payment_api.charge(amount)

# CORRECT: Only retry idempotent operations, or use idempotency keys
@retry(retryable_exceptions=(ConnectionError,))
def create_payment(amount: float, idempotency_key: str):
    return payment_api.charge(amount, idempotency_key=idempotency_key)

# WRONG: Retrying immediately (thundering herd)
for attempt in range(3):
    try:
        return call_api()
    except Error:
        pass  # Immediate retry — hammers the failing service

# CORRECT: Backoff with jitter
for attempt in range(3):
    try:
        return call_api()
    except Error:
        delay = 2 ** attempt + random.uniform(0, 1)
        time.sleep(delay)

# WRONG: Catching and swallowing errors
try:
    process_payment()
except Exception:
    pass  # Payment failed — nobody knows

# CORRECT: Catch, log, and re-raise or return error
try:
    process_payment()
except PaymentError as e:
    logger.error("Payment failed: %s", e)
    raise

# WRONG: Generic error messages
raise AppError("INTERNAL_ERROR", "Something went wrong")  # Unhelpful

# CORRECT: Specific, actionable error messages
raise NotFoundError("User", str(user_id))
```

## Gotchas
- Retry with jitter prevents synchronized retries (thundering herd) across multiple clients
- Exponential backoff: `delay = base * 2^attempt` — grows fast, cap at max_delay
- Circuit breaker prevents cascading failures — fail fast instead of waiting for timeouts
- Idempotency keys are essential for retrying non-idempotent operations (payments, emails)
- `503 Service Unavailable` + `Retry-After` header tells clients when to retry
- Log errors with context (request ID, user ID, parameters) for debugging
- Error codes should be machine-readable; messages should be human-readable
- Structured error responses let clients handle errors programmatically
- Graceful degradation: fall back to cached data, read replicas, or default values
- Never expose internal details (stack traces, SQL queries) in error responses

## Related
- api-design/rest-conventions.md
- security/web-security-basics.md
- performance/caching-strategies.md
