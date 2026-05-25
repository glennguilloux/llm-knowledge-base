---
id: "patterns-health-checks"
title: "Health Check Patterns"
language: "multi"
category: "patterns"
subcategory: "operations"
tags: ["health", "check", "liveness", "readiness", "kubernetes", "monitoring"]
version: ""
retrieval_hint: "Health check liveness readiness Kubernetes probe monitoring status"
last_verified: "2026-05-24"
confidence: "high"
---

# Health Check Patterns

## When to Use
- Kubernetes liveness and readiness probes
- Load balancer health monitoring
- Service dependency checking (database, cache, external APIs)
- Automated alerting and self-healing

## Standard Pattern

```python
# --- FastAPI health endpoints ---
from fastapi import FastAPI, Depends
from sqlalchemy import text
import redis

app = FastAPI()

# Basic health (liveness)
@app.get("/health/live")
async def liveness():
    return {"status": "ok"}

# Detailed health (readiness)
@app.get("/health/ready")
async def readiness(db=Depends(get_db)):
    checks = {}

    # Database
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    # Redis
    try:
        r.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    # External API
    try:
        resp = await httpx.get("https://api.example.com/health", timeout=5)
        checks["external_api"] = "ok" if resp.status_code == 200 else "degraded"
    except Exception:
        checks["external_api"] = "unavailable"

    all_ok = all(v == "ok" for v in checks.values())
    status = 200 if all_ok else 503

    return {"status": "ok" if all_ok else "degraded", "checks": checks}
```

```go
// --- Go health check ---
func healthHandler(db *sql.DB, rdb *redis.Client) http.HandlerFunc {
    return func(w http.ResponseWriter, r *http.Request) {
        checks := map[string]string{}

        if err := db.PingContext(r.Context()); err != nil {
            checks["database"] = err.Error()
        } else {
            checks["database"] = "ok"
        }

        if err := rdb.Ping(r.Context()).Err(); err != nil {
            checks["redis"] = err.Error()
        } else {
            checks["redis"] = "ok"
        }

        healthy := true
        for _, status := range checks {
            if status != "ok" {
                healthy = false
                break
            }
        }

        w.Header().Set("Content-Type", "application/json")
        if !healthy {
            w.WriteHeader(503)
        }
        json.NewEncoder(w).Encode(map[string]any{"status": healthStatus(healthy), "checks": checks})
    }
}
```

```yaml
# --- Kubernetes probes ---
# spec:
#   containers:
#   - name: app
#     livenessProbe:
#       httpGet:
#         path: /health/live
#         port: 8080
#       initialDelaySeconds: 10
#       periodSeconds: 15
#       failureThreshold: 3
#     readinessProbe:
#       httpGet:
#         path: /health/ready
#         port: 8080
#       initialDelaySeconds: 5
#       periodSeconds: 10
#       failureThreshold: 3
```

## Common Mistakes

```text
# WRONG: Single health endpoint for everything
GET /health → checks DB, cache, external APIs, disk, memory
# Liveness fails when external API is down → pod restarts unnecessarily

# CORRECT: Separate liveness and readiness
/health/live  → Is the process alive? (always 200 if running)
/health/ready → Can it serve traffic? (checks dependencies)

# WRONG: Health check queries heavy data
SELECT COUNT(*) FROM users  # Expensive query on every probe!

# CORRECT: Lightweight checks
SELECT 1  # Simple connectivity check

# WRONG: No timeout on dependency checks
await external_api.health()  # May hang for 30s

# CORRECT: Short timeout for health checks
await external_api.health(timeout=5)
```

## Gotchas
- Liveness: "Is the process alive?" — always returns 200 if the process is running
- Readiness: "Can it serve traffic?" — returns 503 if dependencies are down
- Kubernetes restarts pods that fail liveness probes (don't check dependencies there)
- Kubernetes removes pods from Service if readiness fails (graceful degradation)
- Use short timeouts (5s) for dependency checks in readiness probes
- Health checks should be lightweight — no expensive queries
- Include version info in health response for debugging
- Consider a `/health/startup` probe for slow-starting applications

## Related
- patterns/rate-limiting.md
- patterns/webhook-patterns.md
- python/infra/sentry-integration.md
