---
id: "python-infra-sentry-integration"
title: "Sentry Error Tracking Integration"
language: "python"
category: "error-handling"
subcategory: "monitoring"
tags: ["sentry", "error", "tracking", "monitoring", "exception", "logging"]
version: "3.10+"
retrieval_hint: "Sentry error tracking monitoring exception capture breadcrumbs context"
last_verified: "2026-05-22"
confidence: "high"
---

# Sentry Error Tracking Integration

## When to Use
- Production error monitoring and alerting
- Debugging issues with full stack traces and context
- Tracking error rates and regression after deployments
- Capturing performance traces for slow endpoints

## Standard Pattern

```python
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration


# --- Basic setup ---
sentry_sdk.init(
    dsn="https://examplePublicKey@o0.ingest.sentry.io/0",
    environment="production",
    release="myapp@1.2.3",
    traces_sample_rate=0.1,       # 10% of transactions for performance monitoring
    profiles_sample_rate=0.1,     # 10% profiling
    integrations=[
        LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
        SqlalchemyIntegration(),
        FastApiIntegration(),
    ],
    before_send=filter_errors,    # Optional: filter sensitive data
)


def filter_errors(event: dict, hint: dict) -> dict | None:
    """Drop or modify events before sending."""
    # Don't send 404s
    if event.get("exception", {}).values():
        exc = event["exception"]["values"][0]
        if exc.get("type") == "HTTPException" and exc.get("value") == "404":
            return None
    # Scrub sensitive data
    if "request" in event:
        event["request"].pop("cookies", None)
    return event


# --- Capture exceptions manually ---
def process_payment(order_id: int) -> dict:
    try:
        result = payment_gateway.charge(order_id)
        return result
    except PaymentError as e:
        sentry_sdk.capture_exception(e)
        return {"error": str(e)}


# --- Add context ---
def handle_request(request):
    sentry_sdk.set_user({"id": user.id, "email": user.email})
    sentry_sdk.set_tag("endpoint", "/api/payments")
    sentry_sdk.set_context("order", {"order_id": order.id, "amount": order.amount})

    try:
        process_order(order)
    except Exception:
        sentry_sdk.capture_exception()  # Captures current exception with context
        raise


# --- Breadcrumbs (manual) ---
sentry_sdk.add_breadcrumb(
    category="auth",
    message="User logged in",
    level="info",
    data={"user_id": user.id},
)


# --- Performance tracing ---
with sentry_sdk.start_transaction(op="task", name="process_batch"):
    for item in batch:
        with sentry_sdk.start_span(op="db", description="fetch_item"):
            item = db.get(item_id)
        with sentry_sdk.start_span(op="process", description="transform"):
            transform(item)
```

## Common Mistakes

```python
# WRONG: Initializing Sentry without DSN (silently does nothing)
sentry_sdk.init()  # No DSN = no events sent

# CORRECT: Always provide DSN (from env var in production)
sentry_sdk.init(dsn=os.environ["SENTRY_DSN"])

# WRONG: Capturing all exceptions (noise, cost)
try:
    result = risky_operation()
except Exception:
    sentry_sdk.capture_exception()  # Sends every 404, validation error, etc.

# CORRECT: Filter or re-raise expected exceptions
try:
    result = risky_operation()
except ValidationError:
    raise  # Expected, don't send to Sentry
except Exception:
    sentry_sdk.capture_exception()
    raise

# WRONG: Sending PII without scrubbing
sentry_sdk.set_user({"id": 1, "email": "user@example.com", "ssn": "123-45-6789"})

# CORRECT: Only send necessary identifiers
sentry_sdk.set_user({"id": 1, "username": "alice"})  # No PII

# WRONG: traces_sample_rate=1.0 in production (100% of requests)
sentry_sdk.init(traces_sample_rate=1.0)  # Overwhelming data, high cost

# CORRECT: Sample a fraction in production
sentry_sdk.init(traces_sample_rate=0.1)  # 10% of transactions
```

## Gotchas
- `sentry_sdk.init()` is module-level — call once at application startup, not per request
- `capture_exception()` without arguments captures the current exception (inside `except`)
- `set_user()`, `set_tag()`, `set_context()` are thread-local — set per request
- Breadcrumbs are stored in a ring buffer (default 100) — old ones are dropped
- `before_send` can return `None` to drop events — useful for filtering noise
- Use `sentry_sdk.flush()` before shutdown to ensure events are sent
- Integrations auto-capture framework-specific errors (FastAPI, SQLAlchemy, Celery, etc.)
- `profiles_sample_rate` requires `traces_sample_rate` to be > 0

## Related
- python/stdlib/logging.md
- python/web/fastapi/error-handling.md
- error-handling/error-patterns.md
