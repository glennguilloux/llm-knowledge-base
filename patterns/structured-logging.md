---
id: "patterns-structured-logging"
title: "Structured Logging Best Practices"
language: "multi"
category: "patterns"
subcategory: "operations"
tags: ["logging", "structured", "json", "correlation", "context", "level"]
version: ""
retrieval_hint: "Structured logging JSON correlation ID context level best practices"
last_verified: "2026-05-22"
confidence: "high"
---

# Structured Logging Best Practices

## When to Use
- Production applications needing searchable, parseable logs
- Distributed systems requiring correlation across services
- Log aggregation platforms (ELK, Datadog, CloudWatch)
- Debugging with structured context (user ID, request ID, trace ID)

## Standard Pattern

```python
# --- Python structured logging ---
import structlog
import logging

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)

logger = structlog.get_logger()

# Add context
logger = logger.bind(user_id="123", request_id="abc-def")

# Log events
logger.info("user_login", email="alice@test.com", method="oauth")
logger.error("payment_failed", order_id=456, amount=99.99, error="card_declined")
```

```typescript
// --- Node.js structured logging with pino ---
import pino from "pino";

const logger = pino({
  level: process.env.LOG_LEVEL || "info",
  formatters: {
    level: (label) => ({ level: label }),
  },
  timestamp: pino.stdTimeFunctions.isoTime,
});

// Child logger with context
const requestLogger = logger.child({ requestId: "abc-123", userId: "user-456" });
requestLogger.info({ endpoint: "/api/users", method: "GET" }, "request started");
requestLogger.error({ err: error, orderId: 789 }, "payment failed");
```

```go
// --- Go structured logging with slog ---
logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))
logger = logger.With("request_id", "abc-123", "user_id", "user-456")

logger.Info("request started",
    slog.String("method", "GET"),
    slog.String("path", "/api/users"),
)

logger.Error("payment failed",
    slog.Int64("order_id", 789),
    slog.String("error", "card_declined"),
)
```

## Common Mistakes

```text
# WRONG: String interpolation in log messages
logger.info(f"User {user_id} created order {order_id}")
# Not searchable! Can't filter by user_id or order_id

# CORRECT: Structured key-value pairs
logger.info("order_created", user_id=user_id, order_id=order_id)

# WRONG: Logging sensitive data
logger.info("login", email="alice@test.com", password="secret123")
logger.info("payment", card_number="4111111111111111")

# CORRECT: Log identifiers, not secrets
logger.info("login", user_id=user.id, method="oauth")
logger.info("payment", order_id=order.id, amount=99.99)

# WRONG: Inconsistent log levels
logger.info("database connection failed")  # Should be ERROR
logger.error("user viewed profile")  # Should be INFO

# CORRECT: Consistent level usage
# DEBUG: Detailed diagnostic info (disabled in production)
# INFO: Normal operations (user_login, order_created)
# WARN: Degraded but functional (slow_query, retry_needed)
# ERROR: Failures requiring attention (payment_failed, db_error)
```

## Gotchas
- Use JSON format for machine parsing; human-readable format for development
- Include correlation IDs (request ID, trace ID) in every log line
- Never log passwords, tokens, credit card numbers, or PII
- Use log levels consistently: DEBUG, INFO, WARN, ERROR
- Structured fields should be searchable keys, not embedded in message strings
- Use child loggers to add context without passing it through every function
- Log at service boundaries: incoming requests, outgoing calls, DB queries
- Consider log sampling for high-volume endpoints to reduce costs

## Related
- patterns/health-checks.md
- patterns/graceful-shutdown.md
- python/stdlib/logging.md
