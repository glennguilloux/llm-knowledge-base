---
id: "typescript-stdlib-process-management"
title: "Node.js Process Management and Graceful Shutdown"
language: "typescript"
category: "stdlib"
tags: ["process", "shutdown", "signals", "SIGTERM", "SIGINT", "cluster", "worker"]
version: "5.0+"
retrieval_hint: "process management graceful shutdown SIGTERM SIGINT cluster worker signal handling"
last_verified: "2026-05-22"
confidence: "high"
---

# Node.js Process Management and Graceful Shutdown

## When to Use
- Handling shutdown signals (SIGTERM, SIGINT) gracefully
- Closing database connections and servers on exit
- Running background workers alongside HTTP servers
- Managing process lifecycle in containers (Docker, K8s)

## Standard Pattern

```typescript
import express from "express";
import { createServer } from "http";

const app = express();
const server = createServer(app);

// --- Graceful shutdown ---
let isShuttingDown = false;

async function gracefulShutdown(signal: string): Promise<void> {
  if (isShuttingDown) return;
  isShuttingDown = true;

  console.log(`Received ${signal}, starting graceful shutdown...`);

  // Stop accepting new connections
  server.close(async () => {
    console.log("HTTP server closed");

    try {
      // Close database connections
      // await db.close();
      // await redis.quit();
      // await messageQueue.close();

      console.log("All connections closed, exiting");
      process.exit(0);
    } catch (err) {
      console.error("Error during shutdown:", err);
      process.exit(1);
    }
  });

  // Force exit after timeout
  setTimeout(() => {
    console.error("Forced shutdown after timeout");
    process.exit(1);
  }, 30_000);
}

// Register signal handlers
process.on("SIGTERM", () => gracefulShutdown("SIGTERM"));
process.on("SIGINT", () => gracefulShutdown("SIGINT"));

// Handle uncaught errors
process.on("unhandledRejection", (reason) => {
  console.error("Unhandled rejection:", reason);
});

process.on("uncaughtException", (err) => {
  console.error("Uncaught exception:", err);
  gracefulShutdown("uncaughtException");
});

// --- Health check endpoint ---
app.get("/health", (req, res) => {
  if (isShuttingDown) {
    res.status(503).json({ status: "shutting_down" });
    return;
  }
  res.json({ status: "ok" });
});

// Start server
server.listen(3000, () => {
  console.log("Server running on port 3000");
});
```

## Common Mistakes

```typescript
// WRONG: No graceful shutdown
app.listen(3000);  // Connections killed abruptly on SIGTERM

// CORRECT: Handle signals
const server = app.listen(3000);
process.on("SIGTERM", () => {
  server.close(() => process.exit(0));
});

// WRONG: Immediate exit
process.on("SIGTERM", () => process.exit(0));  // In-flight requests dropped!

// CORRECT: Wait for connections to drain
process.on("SIGTERM", () => {
  server.close(() => process.exit(0));  // Waits for active connections
});

// WRONG: No shutdown timeout
server.close(() => { /* hangs if connection never closes */ });

// CORRECT: Force exit after timeout
setTimeout(() => {
  console.error("Forced shutdown");
  process.exit(1);
}, 30_000);

// WRONG: Registering handlers after server starts
app.listen(3000);
process.on("SIGTERM", ...);  // May miss signal in race condition

// CORRECT: Register before listen
process.on("SIGTERM", () => gracefulShutdown("SIGTERM"));
app.listen(3000);
```

## Gotchas
- Docker sends SIGTERM, waits 30s, then SIGKILL — handle SIGTERM to clean up
- Kubernetes uses SIGTERM for pod termination — readiness probe should fail during shutdown
- `server.close()` stops accepting new connections but waits for existing ones to finish
- `process.exit(0)` immediately terminates — always close resources first
- `unhandledRejection` is the async equivalent of `uncaughtException` — always handle it
- Health check should return 503 during shutdown — load balancers stop routing to it
- `isShuttingDown` flag prevents new work from starting during shutdown

## Related
- typescript/web/express-server.md
- typescript/stdlib/async-patterns.md
