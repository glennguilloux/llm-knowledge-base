---
id: "patterns-graceful-shutdown"
title: "Graceful Shutdown Patterns"
language: "multi"
category: "patterns"
subcategory: "operations"
tags: ["shutdown", "graceful", "signal", "drain", "connection", "cleanup"]
version: ""
retrieval_hint: "Graceful shutdown signal SIGTERM drain connection cleanup server"
last_verified: "2026-05-24"
confidence: "high"
---

# Graceful Shutdown Patterns

## When to Use
- Deploying new versions without dropping in-flight requests
- Kubernetes pod termination (SIGTERM before SIGKILL)
- Database connection cleanup on application exit
- WebSocket/long-poll connection draining

## Standard Pattern

```go
// --- Go graceful shutdown ---
func main() {
    srv := &http.Server{
        Addr:    ":8080",
        Handler: router,
    }

    go func() {
        if err := srv.ListenAndServe(); err != http.ErrServerClosed {
            log.Fatalf("Server error: %v", err)
        }
    }()

    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit

    log.Println("Shutting down...")
    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()

    // Stop accepting new connections, finish in-flight
    if err := srv.Shutdown(ctx); err != nil {
        log.Fatalf("Forced shutdown: %v", err)
    }

    // Cleanup resources
    db.Close()
    redis.Close()

    log.Println("Server stopped")
}
```

```python
# --- Python/FastAPI graceful shutdown ---
import signal
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await db.connect()
    yield
    # Shutdown
    await db.disconnect()
    await redis.close()

app = FastAPI(lifespan=lifespan)

# Manual signal handling
shutdown_event = asyncio.Event()

def handle_signal(sig):
    shutdown_event.set()

signal.signal(signal.SIGTERM, lambda s, f: handle_signal(s))
signal.signal(signal.SIGINT, lambda s, f: handle_signal(s))
```

```typescript
// --- Node.js graceful shutdown ---
const server = app.listen(8080);

function gracefulShutdown(signal: string) {
  console.log(`Received ${signal}, shutting down...`);

  server.close(() => {
    console.log("HTTP server closed");
    // Cleanup
    db.end();
    redis.quit();
    process.exit(0);
  });

  // Force shutdown after timeout
  setTimeout(() => {
    console.error("Forced shutdown after timeout");
    process.exit(1);
  }, 30000);
}

process.on("SIGTERM", () => gracefulShutdown("SIGTERM"));
process.on("SIGINT", () => gracefulShutdown("SIGINT"));
```

## Common Mistakes

```text
# WRONG: Exiting immediately on SIGTERM
signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))
# In-flight requests are dropped!

# CORRECT: Stop accepting new requests, finish in-flight
server.shutdown()  # Stop accepting
server.wait()      # Wait for in-flight to complete

# WRONG: No timeout on shutdown
server.shutdown()  # May hang forever if a request is stuck

# CORRECT: Set shutdown timeout
server.shutdown(timeout=30)  # Force kill after 30s

# WRONG: Not closing database connections
# Connection pool exhausted after multiple restarts

# CORRECT: Close connections in shutdown handler
db.close()
redis.close()
```

## Gotchas
- Kubernetes sends SIGTERM, waits `terminationGracePeriodSeconds` (default 30s), then SIGKILL
- Stop accepting new connections first, then wait for in-flight to complete
- Set a shutdown timeout — don't wait forever
- Close database connections, flush logs, release locks
- For WebSocket: send close frame to clients before shutting down
- Health endpoint should return 503 during shutdown (readiness probe fails)
- Pre-stop hooks in Kubernetes can initiate graceful shutdown before SIGTERM
- Test shutdown behavior — it's often where bugs hide

## Related
- patterns/health-checks.md
- patterns/webhook-patterns.md
- go/web/chi-router.md
