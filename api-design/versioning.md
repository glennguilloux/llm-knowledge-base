---
id: "api-design-versioning"
title: "API Versioning Strategies"
language: "multi"
category: "api-design"
subcategory: "versioning"
tags: ["api", "versioning", "rest", "breaking-change", "backward-compatible"]
version: ""
retrieval_hint: "API versioning URL path header breaking change backward compatible"
last_verified: "2026-05-24"
confidence: "high"
---

# API Versioning Strategies

## When to Use
- Making breaking changes to an API while maintaining existing clients
- Supporting multiple API versions simultaneously during migration
- Communicating API stability and deprecation timelines
- Planning backward-compatible evolution of endpoints

## Standard Pattern

```yaml
# --- Strategy 1: URL Path Versioning (most common) ---
# GET /api/v1/users
# GET /api/v2/users (new response format)
# Pros: Clear, cacheable, easy to route
# Cons: URL changes break bookmarks/links

# --- Strategy 2: Header Versioning ---
# GET /api/users
# Accept: application/vnd.myapp.v2+json
# Pros: Clean URLs, content negotiation
# Cons: Harder to test in browser, less visible

# --- Strategy 3: Query Parameter ---
# GET /api/users?version=2
# Pros: Easy to test, explicit
# Cons: Caching issues, not RESTful

# --- Recommended: URL Path with backward compatibility ---
```

```typescript
// --- Express versioning ---
// routes/v1/users.ts
const v1Router = Router();
v1Router.get("/users", (req, res) => {
  const users = getUsers();
  res.json(users.map(u => ({ id: u.id, name: u.name })));
});

// routes/v2/users.ts
const v2Router = Router();
v2Router.get("/users", (req, res) => {
  const users = getUsers();
  res.json({
    data: users.map(u => ({ id: u.id, name: u.name, email: u.email })),
    meta: { total: users.length },
  });
});

app.use("/api/v1", v1Router);
app.use("/api/v2", v2Router);

// --- Deprecation headers ---
app.use("/api/v1/*", (req, res, next) => {
  res.set("Deprecation", "true");
  res.set("Sunset", "2026-01-01");
  res.set("Link", '</api/v2' + req.path + '>; rel="successor-version"');
  next();
});
```

```python
# --- FastAPI versioning ---
from fastapi import FastAPI, APIRouter

v1 = APIRouter(prefix="/api/v1")
v2 = APIRouter(prefix="/api/v2")

@v1.get("/users")
async def list_users_v1():
    return [{"id": 1, "name": "Alice"}]  # v1: simple list

@v2.get("/users")
async def list_users_v2():
    return {  # v2: envelope format
        "data": [{"id": 1, "name": "Alice", "email": "alice@test.com"}],
        "meta": {"total": 1},
    }

app = FastAPI()
app.include_router(v1)
app.include_router(v2)
```

## Common Mistakes

```text
# WRONG: Breaking change without version bump
# v1 response: {"name": "Alice"}
# Updated v1 response: {"firstName": "Alice", "lastName": "Smith"}
# Existing clients break!

# CORRECT: New version for breaking changes
# v1: {"name": "Alice"}  (unchanged)
# v2: {"firstName": "Alice", "lastName": "Smith"}

# WRONG: No deprecation timeline
# v1 endpoints exist forever, maintenance burden grows

# CORRECT: Set sunset date and communicate
# Deprecation: true
# Sunset: 2026-01-01
# Link: </api/v2/users>; rel="successor-version"

# WRONG: Changing response envelope between versions without documentation
# v1: {"users": [...]}
# v2: {"data": [...], "meta": {"total": 50}}  — clients parsing "users" key break silently

# CORRECT: Document envelope changes and provide migration guide
# v1: {"users": [...]}  (unchanged)
# v2: {"data": [...], "meta": {"total": 50}}
# Migration: v2 wraps all lists in "data", adds "meta" for pagination
```

## Gotchas
- URL path versioning is the most common and easiest to understand
- Backward-compatible changes (new fields, new endpoints) don't need a version bump
- Breaking changes: removing fields, changing types, changing semantics
- Always include deprecation headers on old versions
- Support at least 2 versions simultaneously during migration
- Document the migration path from old to new version
- Use `Sunset` header (RFC 8594) to communicate end-of-life dates
- Consider API gateways (Kong, AWS API Gateway) for routing versioned endpoints

## Related
- patterns/rate-limiting.md
- patterns/webhook-patterns.md
- patterns/health-checks.md
