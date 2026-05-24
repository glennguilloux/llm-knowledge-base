---
id: "anti-patterns-security-error-info-leak"
title: "Security Anti-Pattern: Leaking Sensitive Information in Error Responses"
language: "multi"
category: "anti-patterns"
tags: ["antipatterns", "security", "error-handling", "information-disclosure", "stack-traces"]
version: "n/a"
retrieval_hint: "stack traces in production error messages revealing database schema debug mode information leakage"
last_verified: "2026-05-24"
confidence: "high"
---

# Security Anti-Pattern: Leaking Sensitive Information in Error Responses

## When to Use
- Configuring error handlers for production environments
- Reviewing API error response formats
- Setting up environment-specific error verbosity
- Security audits of information disclosure

## Standard Pattern

```python
# WRONG: Exposing stack trace in production (Flask)
@app.errorhandler(Exception)
def handle_error(e):
    return jsonify({
        "error": str(e),
        "traceback": traceback.format_exc(),  # Leaks internal paths, versions
        "type": type(e).__name__
    }), 500

# CORRECT: Generic error in production, detailed logging (Flask)
import logging
logger = logging.getLogger(__name__)

@app.errorhandler(Exception)
def handle_error(e):
    logger.exception("Unhandled error")  # Log full trace server-side
    return jsonify({
        "error": "Internal server error",
        "request_id": g.request_id  # Correlation ID for support
    }), 500
```

```javascript
// WRONG: Express default error handler leaks stack
app.use((err, req, res, next) => {
  res.status(500).json({
    message: err.message,        // May contain DB connection strings
    stack: err.stack             // Full call stack with file paths
  });
});

// CORRECT: Production error handler (Express)
app.use((err, req, res, next) => {
  console.error(`[${req.requestId}]`, err);  // Log full error
  res.status(err.status || 500).json({
    error: err.status ? err.message : 'Internal server error',
    requestId: req.requestId
  });
});
```

```python
# WRONG: Debug mode in production (Django)
# settings.py
DEBUG = True  # Shows full stack trace, SQL queries, settings

# CORRECT: Environment-based config
# settings.py
DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'

# WRONG: Verbose database error
except psycopg2.Error as e:
    return {"error": f"Database error: {e}"}  # Leaks table/column names

# CORRECT: Generic database error
except psycopg2.Error:
    logger.exception("Database error")
    return {"error": "A database error occurred"}, 500
```

```java
// WRONG: Spring exposing error details
@ControllerAdvice
public class ErrorHandler {
    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map> handle(Exception e) {
        return ResponseEntity.status(500).body(Map.of(
            "error", e.getMessage(),   // May contain SQL or class names
            "class", e.getClass().getName()
        ));
    }
}

// CORRECT: Safe error handler (Spring)
@ControllerAdvice
public class ErrorHandler {
    private static final Logger log = LoggerFactory.getLogger(ErrorHandler.class);

    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map> handle(Exception e, HttpServletRequest req) {
        String requestId = UUID.randomUUID().toString();
        log.error("Request {} failed", requestId, e);
        return ResponseEntity.status(500).body(Map.of(
            "error", "Internal server error",
            "requestId", requestId
        ));
    }
}
```

## Common Mistakes
Information leakage in errors is subtle because it works fine in development — detailed errors help developers debug. But in production, stack traces reveal internal file paths, library versions, database schemas, and connection strings. Attackers use this information to fingerprint frameworks, find known vulnerabilities, and craft targeted exploits. The fix is simple: log detailed errors server-side, return generic messages to clients, and use correlation IDs so support can trace issues. Never enable debug mode in production, and always configure environment-specific error handlers.

## Gotchas
- Framework debug modes (`DEBUG=True`, `NODE_ENV=development`) expose settings, environment variables, and SQL queries
- Error messages from database drivers often include table names, column names, and connection details
- 404 pages in some frameworks show the attempted URL pattern, revealing route structure
- Exception class names (`psycopg2.errors.UniqueViolation`) reveal the database technology
- Unhandled promise rejections in Node.js may log full objects to stderr, which ends up in log aggregators
- GraphQL errors include the full query path and field names in error responses by default
- Some CORS error messages reveal allowed origins, helping attackers understand the infrastructure

## Related
- python/patterns/error-handling.md
- python/web/fastapi/error-handling.md
- api-design/error-response-format.md
