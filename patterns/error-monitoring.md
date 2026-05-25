---
id: "patterns-error-monitoring"
title: "Error Monitoring and Alerting Patterns"
language: "multi"
category: "patterns"
tags: ["error-monitoring", "sentry", "alerting", "error-boundaries", "observability", "privacy"]
version: "1.0+"
retrieval_hint: "error monitoring sentry alerting error boundary observability privacy"
last_verified: "2026-05-24"
confidence: "high"
---

# Error Monitoring and Alerting Patterns

## When to Use
- Production applications where silent failures are unacceptable
- Distributed systems with many microservices
- Applications with SLAs requiring fast incident response
- Teams that need to prioritize which bugs to fix first
- Compliance requirements for error tracking and audit trails

## Standard Pattern

```python
import sentry_sdk
from sentry_sdk.integrations.logging import Integration as LoggingIntegration
import structlog
import logging


# --- Sentry initialization ---

def init_error_monitoring(dsn: str, environment: str = "production") -> None:
    """Initialize Sentry with recommended settings."""
    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        traces_sample_rate=0.1,  # 10% of transactions for performance
        profiles_sample_rate=0.01,  # 1% for CPU profiling
        send_default_pii=False,  # Don't send user data by default
        before_send=scrub_sensitive_data,
        integrations=[
            LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
        ],
    )


def scrub_sensitive_data(event, hint):
    """Remove sensitive data before sending to Sentry."""
    # Scrub headers
    if "request" in event and "headers" in event["request"]:
        headers = event["request"]["headers"]
        for key in list(headers.keys()):
            if key.lower() in ("authorization", "cookie", "x-api-key"):
                headers[key] = "[Filtered]"

    # Scrub user context
    if "user" in event:
        user = event["user"]
        user.pop("email", None)
        user.pop("ip_address", None)

    return event


# --- Structured error reporting ---

log = structlog.get_logger()

def handle_error(error: Exception, context: dict) -> None:
    """Report error with context to monitoring system."""
    log.error(
        "operation_failed",
        error_type=type(error).__name__,
        error_message=str(error),
        **context,
        exc_info=error,
    )
    # Sentry captures automatically via LoggingIntegration
    # For manual capture:
    # sentry_sdk.capture_exception(error)


# --- Error boundary pattern (for batch processing) ---

def process_batch(items: list[dict]) -> dict:
    """Process items, tracking failures without stopping."""
    results = {"succeeded": 0, "failed": 0, "errors": []}

    for item in items:
        try:
            process_item(item)
            results["succeeded"] += 1
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({
                "item_id": item.get("id"),
                "error": str(e),
            })
            handle_error(e, {"item_id": item.get("id")})

    if results["failed"] > 0:
        log.warning(
            "batch_partial_failure",
            total=len(items),
            **results,
        )

    return results
```

```typescript
// --- React Error Boundary ---

import React, { Component, ErrorInfo, ReactNode } from "react";
import * as Sentry from "@sentry/react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    Sentry.withScope((scope) => {
      scope.setExtras({
        componentStack: errorInfo.componentStack,
      });
      Sentry.captureException(error);
    });
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div role="alert">
            <h2>Something went wrong</h2>
            <button onClick={() => this.setState({ hasError: false })}>
              Try again
            </button>
          </div>
        )
      );
    }
    return this.props.children;
  }
}

// Wrap app root
// <ErrorBoundary><App /></ErrorBoundary>
```

```go
// --- Go error monitoring ---

package monitoring

import (
    "fmt"
    "time"

    "github.com/getsentry/sentry-go"
)

func Init(dsn string, environment string) error {
    return sentry.Init(sentry.ClientOptions{
        Dsn:              dsn,
        Environment:      environment,
        TracesSampleRate: 0.1,
        BeforeSend: func(event *sentry.Event, hint *sentry.EventHint) *sentry.Event {
            // Scrub sensitive data
            if event.Request != nil {
                delete(event.Request.Headers, "Authorization")
                delete(event.Request.Headers, "Cookie")
            }
            return event
        },
    })
}

func ReportError(err error, context map[string]interface{}) {
    sentry.WithScope(func(scope *sentry.Scope) {
        for k, v := range context {
            scope.SetExtra(k, v)
        }
        scope.SetTag("component", context["component"].(string))
        sentry.CaptureException(err)
    })
}

// Alert threshold check
type AlertManager struct {
    errorCount    int
    windowStart   time.Time
    threshold     int
    windowSize    time.Duration
}

func NewAlertManager(threshold int, windowSize time.Duration) *AlertManager {
    return &AlertManager{
        threshold:  threshold,
        windowSize: windowSize,
        windowStart: time.Now(),
    }
}

func (a *AlertManager) RecordError() bool {
    a.errorCount++
    if time.Since(a.windowStart) > a.windowSize {
        a.errorCount = 0
        a.windowStart = time.Now()
    }
    return a.errorCount >= a.threshold
}
```

## Common Mistakes

```python
# WRONG: Catching all exceptions and silently passing
try:
    critical_operation()
except Exception:
    pass  # Error disappears forever!

# CORRECT: Log and report, then decide whether to re-raise
try:
    critical_operation()
except Exception as e:
    handle_error(e, {"operation": "critical_operation"})
    raise  # Re-raise if the error is unrecoverable

# WRONG: Sending PII to error monitoring
sentry_sdk.set_user({"email": user.email, "ssn": user.ssn})

# CORRECT: Only send non-PII identifiers
sentry_sdk.set_user({"id": str(user.id)})

# WRONG: Alerting on every single error (alert fatigue)
# Every 404 triggers a PagerDuty incident

# CORRECT: Set meaningful thresholds
# Alert only when error rate > 1% over 5 minutes
# Or when a new error type appears

# WRONG: Not grouping errors properly
# Each error creates a separate issue

# CORRECT: Use error types and contexts for grouping
sentry_sdk.set_tag("error_type", "payment_failure")
sentry_sdk.set_tag("payment_provider", "stripe")

# WRONG: Monitoring only crashes, not degraded behavior
# Slow responses go unnoticed

# CORRECT: Track performance alongside errors
sentry_sdk.start_transaction(op="http.server", name="/api/users")
```

## Gotchas
- **Alert fatigue**: If everything alerts, nothing gets attention. Set thresholds (e.g., >1% error rate over 5 min) and only page for new/critical errors
- **Error grouping**: Sentry groups by stack trace + error type. Use `scope.set_tag()` to add custom grouping dimensions
- **Privacy**: Never send passwords, tokens, SSNs, or health data to monitoring. Use `before_send` to scrub
- **Sampling**: `traces_sample_rate=0.1` means 10% of transactions are traced — enough for performance insights without overwhelming storage
- **Breadcrumbs**: Sentry captures INFO+ logs as breadcrumbs, giving context before an ERROR event. Use structured logging
- **Error boundaries** (React): Catch render errors in UI subtrees — one broken component shouldn't crash the entire page
- **Batch processing**: Use error boundary pattern — process all items, collect failures, report summary
- **Sentry transactions**: Wrap request handlers in transactions to track latency, not just errors
- **Local development**: Set `environment="development"` and use a separate DSN or `dsn=""` to avoid polluting production data
- **Rate limits**: Sentry has rate limits on events — bursty error storms may be sampled. Consider client-side rate limiting

## Related
- patterns/input-validation.md
- patterns/observability.md
- patterns/structured-logging.md
- python/stdlib/logging-structured.md
- python/infra/sentry-integration.md
