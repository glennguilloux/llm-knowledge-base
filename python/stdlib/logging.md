---
id: "python-stdlib-logging"
title: "Structured Logging with logging Module"
language: "python"
category: "stdlib"
subcategory: "logging"
tags: ["logging", "structured", "logger", "handler", "format"]
version: "3.10+"
retrieval_hint: "logging structured logger handler format level"
last_verified: "2026-05-22"
confidence: "high"
---

# Structured Logging with logging Module

## When to Use
- Application logging (not print statements)
- Structured log output for parsing (JSON logs)
- Configurable log levels per module
- Production logging with file rotation

## Standard Pattern

```python
import logging
import json
from datetime import datetime, timezone


def setup_logging(level: int = logging.INFO) -> None:
    """Configure structured JSON logging."""
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    
    logging.basicConfig(
        level=level,
        handlers=[handler],
        force=True,  # Override any existing config
    )


class JSONFormatter(logging.Formatter):
    """Format log records as JSON."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


# Usage
logger = logging.getLogger(__name__)

def process_order(order_id: str) -> None:
    logger.info("Processing order", extra={"order_id": order_id})
    try:
        # Process...
        logger.info("Order processed", extra={"order_id": order_id})
    except Exception:
        logger.exception("Order processing failed", extra={"order_id": order_id})
        raise
```

## Common Mistakes

```python
# WRONG: Using print() for logging
print(f"User {user_id} logged in")  # No levels, no structure, no rotation

# CORRECT: Use logging
logger.info("User logged in", extra={"user_id": user_id})

# WRONG: Using f-strings in log calls
logger.info(f"Processing {item_count} items")  # Always evaluates string

# CORRECT: Use lazy formatting
logger.info("Processing %d items", item_count)  # Only formats if log level is active

# WRONG: Creating logger at module level without __name__
logger = logging.getLogger("myapp")  # Hard to trace which module

# CORRECT: Use __name__ for module-level logger
logger = logging.getLogger(__name__)
```

## Gotchas
- `logging.basicConfig()` only works if root logger has no handlers (use `force=True` in 3.8+)
- `extra={}` dict keys become `LogRecord` attributes — don't use reserved names
- `logger.exception()` automatically includes traceback
- Use `logging.getLogger(__name__)` — creates hierarchical logger per module
- `propagate=True` (default) sends logs to parent loggers — can cause duplicates
- Use `logger.isEnabledFor(level)` before expensive log message construction

## Related
- python/web/fastapi/error-handling.md
- python/patterns/error-handling.md
