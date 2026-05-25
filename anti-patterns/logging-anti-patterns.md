---
id: "anti-patterns-logging-anti-patterns"
title: "Logging Anti-Patterns: print() Statements, Leaking Secrets, and Wrong Levels"
language: "multi"
category: "anti-patterns"
tags: ["antipatterns", "logging", "structured-logging", "security", "debugging"]
version: "n/a"
retrieval_hint: "print instead of logging logging secrets PII no structured logging wrong log levels no correlation IDs"
last_verified: "2026-05-24"
confidence: "high"
---

# Logging Anti-Patterns: print() Statements, Leaking Secrets, and Wrong Levels

## When to Use
- Setting up logging in any application
- Reviewing code for observability best practices
- Debugging production issues with insufficient log context
- Migrating from print statements to structured logging

## Standard Pattern

```python
# WRONG: Using print() instead of logging
print("User logged in: " + user_id)
print(f"Error: {error}")
# No log levels, no timestamps, no structured data, goes to stdout only

# CORRECT: Use proper logging
import logging
logger = logging.getLogger(__name__)
logger.info("User logged in", extra={"user_id": user_id})
logger.error("Request failed", extra={"error": str(error)})
```

```python
# WRONG: Logging secrets and PII
logger.info(f"User login: email={email}, password={password}")
logger.debug(f"API key: {api_key}")
logger.error(f"Token: {jwt_token}")
# Secrets exposed in log aggregation systems (ELK, Datadog, CloudWatch)

# CORRECT: Mask or omit sensitive data
logger.info("User login attempt", extra={"email": email, "password_length": len(password)})
logger.debug("API request authorized")
logger.error("Token validation failed", extra={"token_prefix": jwt_token[:8] + "..."})
```

```javascript
// WRONG: Logging everything at INFO level
logger.info("Starting request")
logger.info("Database query: SELECT * FROM users")
logger.info("Cache hit for key: user_123")
logger.info("Sending response")
logger.info("Request completed in 45ms")
// All INFO — can't filter noise from signal

// CORRECT: Use appropriate log levels
logger.info("Starting request", { requestId, method, path })  // Business event
logger.debug("Database query executed", { query, duration_ms })  // Diagnostic
logger.debug("Cache hit", { key, ttl_remaining })  // Diagnostic
logger.warn("Slow query detected", { query, duration_ms: 2500 })  // Attention needed
logger.error("Request failed", { error: err.message, requestId })  // Failure
```

```python
# WRONG: No structured logging (string formatting)
logger.info(f"Order {order_id} placed by user {user_id} for ${total}")
# Impossible to query: "show me all orders > $1000" in log aggregation

# CORRECT: Structured logging with key-value pairs
logger.info("Order placed", extra={
    "order_id": order_id,
    "user_id": user_id,
    "total_amount": total,
    "item_count": len(items),
})
```

```json
// WRONG: Unstructured log output
// 2024-01-15 10:30:22 INFO Order 12345 placed by user 678 for $99.99
// 2024-01-15 10:30:23 ERROR Failed to send email to user 678
// Can't filter, aggregate, or alert on structured fields

// CORRECT: JSON structured log output
{"timestamp": "2024-01-15T10:30:22Z", "level": "INFO", "message": "Order placed", "order_id": "12345", "user_id": "678", "total": 99.99}
```

```python
# WRONG: No correlation/request IDs
# Distributed system — which logs belong to which request?
logger.info("Received request")
logger.info("Called payment service")
logger.info("Database query")
logger.info("Response sent")

# CORRECT: Include request/correlation ID in every log entry
import uuid
request_id = str(uuid.uuid4())
logger.info("Received request", extra={"request_id": request_id, "path": "/api/orders"})
logger.info("Called payment service", extra={"request_id": request_id, "service": "payment"})
```

```python
# WRONG: Logging in library code (pollutes application logs)
# mylib/utils.py
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mylib")
logger.info("Library function called")  # User didn't ask for this

# CORRECT: Let library consumers configure logging
# mylib/utils.py
logger = logging.getLogger(__name__)  # Use __name__, not hardcoded name
# Don't call basicConfig or set levels in library code
# Users configure: logging.getLogger("mylib").setLevel(logging.DEBUG)
```

## Common Mistakes
Using `print()` instead of proper logging is the most common logging anti-pattern. Print statements have no log levels, no timestamps (in structured format), and cannot be filtered or routed to different outputs. Logging secrets (passwords, API keys, tokens, PII like SSNs) is a security incident — log aggregation systems like ELK, Datadog, and CloudWatch are often accessible to many team members and persist data for months. Using the wrong log level (everything at INFO) makes it impossible to filter noise from signal in production, where you typically want INFO and above but need DEBUG available for troubleshooting.

## Gotchas
- Python's `logging.basicConfig()` only takes effect on the first call — subsequent calls are no-ops unless `force=True`
- Use `logging.getLogger(__name__)` in libraries so consumers can control log levels per module
- `extra={}` fields in Python logging are not automatically included by all handlers — JSON formatters need explicit field mapping
- Correlation IDs should be propagated through HTTP headers (e.g., `X-Request-ID`) in microservices
- Log rotation prevents disk exhaustion — configure `RotatingFileHandler` or use external rotation (logrotate)
- `logger.exception()` automatically includes the stack trace — `logger.error()` does not
- In structured logging, use consistent field names across the codebase (e.g., always `user_id`, not sometimes `userId`)
- Python `structlog`, Go `zerolog`, Java `SLF4J+Logback`, Node `pino` are recommended structured logging libraries
- `DEBUG` logs should be disabled in production but configurable without redeployment

## Related
- python/stdlib/logging.md
- python/stdlib/logging-structured.md
- bash/error-handling.md
- security/web-security-basics.md
