---
id: "antipatterns-error-handling"
title: "Error Handling Anti-Patterns: Catching and Swallowing, and No Error Context"
language: "multi"
category: "anti-patterns"
tags: ["antipatterns", "error-handling", "swallowing", "catching-exception", "no-context", "logging-rethrowing", "return-codes"]
version: "n/a"
retrieval_hint: "error handling antipatterns catching and swallowing catching Exception base no error context logging and rethrowing ignoring return codes"
last_verified: "2026-05-24"
confidence: "high"
---

# Error Handling Anti-Patterns: Catching and Swallowing, and No Error Context

## When to Use
- Reviewing error handling code
- Training LLMs to handle errors properly
- Error handling code review checklist
- Understanding error handling best practices

## Standard Pattern

```python
# === Python Examples ===

# WRONG: Catching and swallowing exceptions
try:
    process_data(data)
except Exception:
    pass  # Error silently lost!

# CORRECT: Handle or log the exception
try:
    process_data(data)
except ValueError as e:
    logger.error("Invalid data: %s", e)
    raise  # Re-raise if caller should handle it
except Exception as e:
    logger.error("Unexpected error processing data: %s", e, exc_info=True)
    raise ProcessingError("Failed to process data") from e

# WRONG: Catching Exception base class (too broad)
try:
    result = 1 / x
except Exception:  # Catches KeyboardInterrupt, SystemExit too!
    result = 0

# CORRECT: Catch specific exceptions
try:
    result = 1 / x
except ZeroDivisionError:
    result = 0

# WRONG: No error context (what failed?)
raise Exception("Error occurred")

# CORRECT: Provide context
raise ProcessingError(
    f"Failed to process order {order_id} for user {user_id}"
) from original_exception

# WRONG: Logging and rethrowing (duplicate logging)
try:
    process(data)
except Exception as e:
    logger.error("Error: %s", e)  # Logged here
    raise  # Caller also logs — duplicate log entries!

# CORRECT: Either log OR rethrow, not both (unless at boundary)
# Option 1: Let caller handle it
def process(data):
    return transform(data)  # Let exception propagate

# Option 2: Log at the boundary (API handler, main loop)
def handle_request(request):
    try:
        return process(request)
    except Exception as e:
        logger.error("Request failed: %s", e, exc_info=True)
        return error_response(e)

# === Java Examples ===

# WRONG: Catching and swallowing
# try {
#     process(data);
# } catch (Exception e) {
#     // Nothing here
# }

# CORRECT: Handle or rethrow
# try {
#     process(data);
# } catch (IOException e) {
#     logger.error("IO error processing data", e);
#     throw new ProcessingException("Failed to process", e);
# }

# === JavaScript Examples ===

# WRONG: Catching and swallowing
# try {
#     process(data);
# } catch (e) {
#     // Nothing
# }

# CORRECT: Handle or rethrow
# try {
#     process(data);
# } catch (e) {
#     logger.error('Failed to process data:', e);
#     throw new ProcessingError('Failed to process data', { cause: e });
# }

# WRONG: Ignoring return codes (C/C++)
# fp = fopen("file.txt", "r");
# fgets(buffer, 100, fp);  // If fopen failed, fp is NULL!
# fclose(fp);

# CORRECT: Check return codes
# fp = fopen("file.txt", "r");
# if (fp == NULL) {
#     perror("Failed to open file");
#     return -1;
# }
# fgets(buffer, 100, fp);
# fclose(fp);

# WRONG: Using print for error messages
print("Error: database connection failed")

# CORRECT: Use proper error handling
logger.error("Database connection failed: %s", error)
raise DatabaseError("Connection failed") from error
```

## Common Mistakes
- Catching and swallowing — errors silently lost, bugs go undetected
- Catching Exception base class — catches system exceptions like KeyboardInterrupt
- No error context — generic "Error occurred" messages with no details
- Logging and rethrowing — duplicate log entries at every level of the call stack
- Ignoring return codes — especially in C/C++, NULL pointers and -1 returns indicate errors
- Print debugging in production — print statements left in production code

## Gotchas
- **NEVER** use `except: pass` or `catch (Exception e) { }`. Errors must be handled or logged.
- Catch the MOST SPECIFIC exception type possible. Never catch `Exception` unless at a boundary.
- Always include context in error messages: what failed, what data was involved.
- Use exception chaining (`raise ... from ...` in Python, `new Exception(msg, cause)` in Java).
- Log at the BOUNDARY (API handler, main loop), not at every level.
- In C/C++, always check return codes. `NULL` pointers and `-1` returns are error indicators.
- `exc_info=True` in Python includes the full traceback in the log.
- Error types should be specific: `ValidationError`, `NotFoundError`, `ConnectionError`.
- Don't use print/logging for errors in library code. Let the caller decide how to handle.

## Related
- anti-patterns/logging-antipatterns.md
- anti-patterns/testing-antipatterns.md
- anti-patterns/configuration-antipatterns.md
- error-handling/structured-errors.md
