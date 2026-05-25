---
id: "antipatterns-logging"
title: "Logging Anti-Patterns: Sensitive Data, Wrong Levels, and No Correlation IDs"
language: "multi"
category: "anti-patterns"
tags: ["antipatterns", "logging", "sensitive-data", "structured-logging", "log-levels", "correlation-ids"]
version: "n/a"
retrieval_hint: "logging antipatterns logging sensitive data no structured logging wrong log levels logging in hot paths no correlation IDs printf debugging in production"
last_verified: "2026-05-24"
confidence: "high"
---

# Logging Anti-Patterns: Sensitive Data, Wrong Levels, and No Correlation IDs

## When to Use
- Reviewing logging practices
- Training LLMs to write proper logging
- Setting up logging infrastructure
- Understanding observability best practices

## Standard Pattern

```python
# === Python Examples ===

# WRONG: Logging sensitive data
logger.info(f"User login: {email}, password: {password}")
logger.debug(f"Payment: {credit_card_number}, CVV: {cvv}")

# CORRECT: Never log sensitive data
logger.info("User login attempt: %s", email)
# Log payment events without card details
logger.info("Payment processed for order %s", order_id)

# WRONG: Wrong log levels
logger.debug("Database connection failed!")  # Should be ERROR!
logger.error("User viewed page")  # Should be INFO!
logger.info("Critical system failure!")  # Should be CRITICAL!

# CORRECT: Use appropriate log levels
# DEBUG: Detailed diagnostic info (development only)
logger.debug("Processing item %d of %d", i, total)

# INFO: Normal application events
logger.info("User %s logged in", user_id)
logger.info("Order %s created successfully", order_id)

# WARNING: Unexpected but recoverable issues
logger.warning("API response slow: %dms", response_time)
logger.warning("Retry attempt %d for request %s", attempt, request_id)

# ERROR: Failed operations, exceptions
logger.error("Failed to process order %s: %s", order_id, error)

# CRITICAL: System-level failures
logger.critical("Database connection lost!")
logger.critical("Out of memory!")

# WRONG: No structured logging (plain text, hard to query)
logger.info(f"User {user_id} purchased {item} for ${price}")

# CORRECT: Structured logging (JSON, queryable)
logger.info("Purchase completed", extra={
    "user_id": user_id,
    "item": item,
    "price": price,
    "event": "purchase",
    "timestamp": datetime.utcnow().isoformat(),
})

# Or with structlog:
# log.info("purchase_completed", user_id=user_id, item=item, price=price)

# WRONG: No correlation IDs (can't trace requests across services)
# Service A: logger.info("Processing request")
# Service B: logger.info("Processing request")
# Which request? Can't tell!

# CORRECT: Use correlation IDs to trace requests
import uuid

def handle_request(request):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    logger.info("Request received", extra={
        "correlation_id": correlation_id,
        "path": request.path,
        "method": request.method,
    })
    # Pass correlation_id to all downstream calls

# WRONG: Logging in hot paths (performance impact)
for item in million_items:
    logger.debug("Processing item: %s", item)  # Slows down the loop!

# CORRECT: Guard expensive logging
if logger.isEnabledFor(logging.DEBUG):
    logger.debug("Processing item: %s", expensive_serialization(item))

# Or use sampling for high-volume logs
if random.random() < 0.01:  # Log 1% of events
    logger.info("Sampled event: %s", event)

# WRONG: printf debugging left in production code
print(f"DEBUG: value = {value}")
print(f"Processing step 3: {data}")

# CORRECT: Use proper logging
logger.debug("Processing step 3: %s", data)

# WRONG: Catching and swallowing exceptions without logging
try:
    process(data)
except Exception:
    pass  # Error silently lost!

# CORRECT: Always log exceptions
try:
    process(data)
except Exception as e:
    logger.error("Failed to process data: %s", e, exc_info=True)
    # exc_info=True includes the full traceback
```

## Common Mistakes
- Logging sensitive data — passwords, credit cards, tokens in log files
- Wrong log levels — debug for errors, error for normal events
- No structured logging — plain text that can't be queried or aggregated
- No correlation IDs — can't trace requests across microservices
- Logging in hot paths — performance degradation from excessive logging
- Printf debugging in production — print statements left in production code
- Catching without logging — exceptions silently swallowed, bugs go undetected

## Gotchas
- **NEVER** log passwords, API keys, credit card numbers, or personal data.
- Structured logging (JSON) enables querying and aggregation in log management systems.
- Correlation IDs are essential for distributed tracing across microservices.
- `exc_info=True` in Python includes the full exception traceback.
- Log levels should be configurable at runtime (DEBUG in dev, INFO/WARNING in production).
- Sampling can reduce log volume for high-frequency events.
- Centralized logging (ELK, Datadog, CloudWatch) requires structured format.
- Log rotation prevents disk space exhaustion.
- Use `logger.isEnabledFor(level)` to guard expensive log message construction.

## Related
- anti-patterns/testing-antipatterns.md
- anti-patterns/error-handling-antipatterns.md
- anti-patterns/docker-antipatterns.md
- patterns/observability.md
