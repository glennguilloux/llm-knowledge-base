---
id: "go-stdlib-slog-logging"
title: "Go Structured Logging with slog"
language: "go"
category: "stdlib"
subcategory: "logging"
tags: ["go", "slog", "logging", "structured", "json", "handler"]
version: "1.21+"
retrieval_hint: "Go slog structured logging JSON handler log level context"
last_verified: "2026-05-24"
confidence: "high"
---

# Go Structured Logging with slog

## When to Use
- Structured logging in Go applications (JSON output for log aggregation)
- Replacing `log.Printf` with typed, searchable log entries
- Adding context (request ID, user ID) to log lines
- Production logging with configurable levels

## Standard Pattern

```go
package main

import (
    "context"
    "log/slog"
    "os"
)

// --- Setup ---
func setupLogger(level string, jsonOutput bool) *slog.Logger {
    var logLevel slog.Level
    switch level {
    case "debug":
        logLevel = slog.LevelDebug
    case "warn":
        logLevel = slog.LevelWarn
    case "error":
        logLevel = slog.LevelError
    default:
        logLevel = slog.LevelInfo
    }

    opts := &slog.HandlerOptions{Level: logLevel}

    var handler slog.Handler
    if jsonOutput {
        handler = slog.NewJSONHandler(os.Stdout, opts)
    } else {
        handler = slog.NewTextHandler(os.Stdout, opts)
    }

    return slog.New(handler)
}

// --- Basic usage ---
func main() {
    logger := setupLogger("info", true)
    slog.SetDefault(logger)

    slog.Info("server starting",
        slog.String("host", "0.0.0.0"),
        slog.Int("port", 8080),
    )

    slog.Warn("config missing",
        slog.String("key", "database.url"),
        slog.String("fallback", "sqlite:///app.db"),
    )

    slog.Error("database connection failed",
        slog.String("url", dbURL),
        slog.Any("error", err),
    )
}

// --- With context (request-scoped fields) ---
type contextKey string

const loggerKey contextKey = "logger"

func WithLogger(ctx context.Context, logger *slog.Logger) context.Context {
    return context.WithValue(ctx, loggerKey, logger)
}

func LoggerFromCtx(ctx context.Context) *slog.Logger {
    if l, ok := ctx.Value(loggerKey).(*slog.Logger); ok {
        return l
    }
    return slog.Default()
}

// --- Middleware that adds request context ---
func loggingMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        requestID := r.Header.Get("X-Request-ID")
        logger := slog.With(
            slog.String("method", r.Method),
            slog.String("path", r.URL.Path),
            slog.String("request_id", requestID),
            slog.String("remote_addr", r.RemoteAddr),
        )

        ctx := WithLogger(r.Context(), logger)
        logger.Info("request started")

        next.ServeHTTP(w, r.WithContext(ctx))

        logger.Info("request completed")
    })
}

// --- Handler usage ---
func handleRequest(w http.ResponseWriter, r *http.Request) {
    logger := LoggerFromCtx(r.Context())

    user, err := getUser(r.Context())
    if err != nil {
        logger.Error("failed to get user", slog.Any("error", err))
        http.Error(w, "Internal error", 500)
        return
    }

    logger.Info("user retrieved", slog.Int64("user_id", user.ID))
}
```

## Common Mistakes

```go
// WRONG: Using log.Printf in production
log.Printf("User %d created", userID)  // Unstructured, hard to search

// CORRECT: Use slog with structured fields
slog.Info("user created", slog.Int64("user_id", userID))

// WRONG: Logging sensitive data
slog.Info("login", slog.String("password", password))  // Never log passwords!

// CORRECT: Log non-sensitive identifiers
slog.Info("login", slog.String("user_id", userID))

// WRONG: Using fmt.Sprintf in log message
slog.Info(fmt.Sprintf("User %d created", userID))  // String interpolation defeats structured logging

// CORRECT: Use slog attributes
slog.Info("user created", slog.Int64("user_id", userID))

// WRONG: Not using context for request-scoped fields
slog.Info("request", slog.String("request_id", reqID))  // reqID must be passed around

// CORRECT: Store logger in context with pre-populated fields
logger := slog.With(slog.String("request_id", reqID))
ctx = WithLogger(ctx, logger)
```

## Gotchas
- `slog.SetDefault()` sets the global default — use for application-wide logging
- `slog.With()` creates a new logger with pre-populated fields (immutable)
- `slog.NewJSONHandler` outputs JSON; `slog.NewTextHandler` outputs human-readable text
- `slog.HandlerOptions.Level` controls minimum log level
- `slog.Any()` accepts any type — use for errors, structs, etc.
- Context-based loggers let you add request-scoped fields without threading them through params
- `slog.LogAttrs()` is more efficient than `slog.Log()` for many attributes
- Use `slog.Group()` to nest attributes: `slog.Group("db", slog.String("host", "..."))`

## Related
- go/stdlib/error-handling.md
- go/web/http-server.md
- go/web/chi-router.md
