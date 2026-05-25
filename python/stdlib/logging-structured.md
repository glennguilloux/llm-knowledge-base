---
id: "python-stdlib-logging-structured"
title: "Structured Logging in Python"
language: "python"
category: "stdlib"
tags: ["logging", "structured", "json", "structlog", "correlation-id", "sentry"]
version: "3.10+"
retrieval_hint: "structured logging json structlog correlation sentry cloudwatch"
last_verified: "2026-05-24"
confidence: "high"
---

# Structured Logging in Python

## When to Use
- Production services that need machine-parseable logs
- Distributed systems requiring correlation IDs across services
- Integration with log aggregation (ELK, Datadog, CloudWatch)
- Replacing print() debugging with proper log levels
- Error tracking with Sentry or similar tools

## Standard Pattern

```python
import logging
import json
import sys
import uuid
from typing import Any


# --- Standard library structured logging (JSON formatter) ---

class JSONFormatter(logging.Formatter):
    """Output log records as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        # Include extra fields
        for key in ("correlation_id", "user_id", "request_path"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)
        return json.dumps(log_entry, default=str)


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger with JSON output."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)


# --- Using structlog (preferred for structured logging) ---

import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

log = structlog.get_logger()

# Basic structured logging
log.info("user_login", user_id=42, ip="192.168.1.1")
# {"user_login": null, "user_id": 42, "ip": "192.168.1.1", "level": "info", "timestamp": "..."}

# With context (bound to all subsequent logs)
request_log = log.bind(
    correlation_id=str(uuid.uuid4()),
    request_path="/api/users",
)
request_log.info("request_started")
request_log.info("request_completed", status_code=200, duration_ms=45)


# --- Correlation IDs with contextvars ---

from contextvars import ContextVar

correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")

def get_correlation_id() -> str:
    cid = correlation_id.get("")
    if not cid:
        cid = str(uuid.uuid4())
        correlation_id.set(cid)
    return cid

# Middleware pattern (FastAPI/Starlette example)
async def correlation_middleware(request, call_next):
    cid = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    correlation_id.set(cid)
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = cid
    return response


# --- Integration with Sentry ---

def setup_sentry(dsn: str, environment: str = "production") -> None:
    """Configure Sentry for error monitoring."""
    import sentry_sdk
    from sentry_sdk.integrations.logging import (
        Integration as LoggingIntegration,
        EventHandler,
    )

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        traces_sample_rate=0.1,
        integrations=[
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR,
            ),
        ],
    )
```

## Common Mistakes

```python
# WRONG: Using f-strings in log messages (defeats lazy evaluation)
name = "world"
log.info(f"Hello {name}")  # String is formatted even if log level is filtered out

# CORRECT: Use printf-style formatting (lazy evaluation)
log.info("Hello %s", name)  # Only formatted if message is actually logged

# WRONG: Using print() for logging in production
print(f"Error: {e}")  # No level, no timestamp, no structure

# CORRECT: Use proper logger with level
log.error("operation_failed", error=str(e), operation="save_user")

# WRONG: Logging sensitive data
log.info("login_attempt", password=user_password, ssn=user_ssn)

# CORRECT: Never log secrets — redact or omit
log.info("login_attempt", username=username, success=False)

# WRONG: Creating logger at module level without name
logger = logging.getLogger()  # Gets root logger — hard to configure per-module

# CORRECT: Use __name__ for hierarchical loggers
logger = logging.getLogger(__name__)  # "myapp.services.user"

# WRONG: Catching and logging without context
try:
    process(data)
except Exception:
    log.error("Something went wrong")  # No exception info!

# CORRECT: Include exception info
try:
    process(data)
except Exception:
    log.exception("process_failed", data_id=data.id)  # Includes traceback
```

## Gotchas
- `structlog` is the de facto standard for structured logging in Python — prefer it over rolling your own JSON formatter
- `logging` is lazy with `%s` formatting but NOT with f-strings — always use `%s` or `extra={}` for structured data
- `log.exception()` automatically includes `exc_info` — equivalent to `log.error(..., exc_info=True)`
- Correlation IDs should be set at the request boundary (middleware) and propagated via `contextvars`
- Sentry's `LoggingIntegration` sends `ERROR` and above to Sentry as events, while `INFO` and above go to breadcrumbs
- `structlog.contextvars.bind_contextvars()` binds key-value pairs to all subsequent log calls in the current context
- Never log passwords, tokens, PII, or credit card numbers — use a redaction processor
- `logging.getLogger(__name__)` creates a hierarchy matching your package structure — configure `myapp` to control all sub-loggers
- In async code, use `contextvars` (not thread-local) for correlation IDs — `structlog.contextvars` handles this

## Related
- python/stdlib/logging.md
- python/infra/sentry-integration.md
- python/patterns/error-handling.md
