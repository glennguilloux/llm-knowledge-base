---
id: "anti-patterns-api-versioning-anti-patterns"
title: "API Anti-Pattern: Versioning Mistakes"
language: "multi"
category: "anti-patterns"
tags: ["antipatterns", "api", "versioning", "breaking-changes", "deprecation"]
version: "n/a"
retrieval_hint: "API versioning breaking changes URL vs header versioning sunset deprecation backward compatible"
last_verified: "2026-05-24"
confidence: "high"
---

# API Anti-Pattern: Versioning Mistakes

## When to Use
- Designing API evolution strategy
- Planning breaking changes to existing APIs
- Communicating deprecation timelines to API consumers
- Choosing between URL-based and header-based versioning

## Standard Pattern

```python
# WRONG: Breaking change without version bump
# v1 returned: {"users": [...]}
# Suddenly returns: {"data": {"users": [...]}, "meta": {...}}
# Every client breaks!

# CORRECT: Version the API or use backward-compatible changes
# Option A: URL versioning (simple, explicit)
@app.get("/v1/users")
async def get_users_v1():
    users = await db.get_users()
    return {"users": [u.to_dict() for u in users]}

@app.get("/v2/users")
async def get_users_v2():
    users = await db.get_users()
    return {"data": [u.to_dict() for u in users], "meta": {"count": len(users)}}

# Option B: Header versioning (clean URLs)
@app.get("/users")
async def get_users(request: Request):
    version = request.headers.get("Accept", "").split("v")[-1].split("+")[0]
    users = await db.get_users()
    if version == "2":
        return {"data": [u.to_dict() for u in users], "meta": {"count": len(users)}}
    return {"users": [u.to_dict() for u in users]}
```

```javascript
// WRONG: Deprecating with no sunset period — clients have no time to migrate
app.get("/api/v1/users", async (req, res) => {
    // 410 Gone — suddenly all v1 clients get nothing
    return res.status(410).json({ error: "v1 is no longer available" });
});

// CORRECT: Gradual deprecation with sunset headers
app.get("/api/v1/users", async (req, res) => {
    res.set("Sunset", "Sat, 01 Jan 2027 00:00:00 GMT");
    res.set("Deprecation", "true");
    res.set("Link", '</api/v2/users>; rel="successor-version"');
    // Still serve v1 — warn via response header, not by breaking the client
    const users = await db.getUsers();
    res.json({ users });
});
```

```java
// WRONG: Never versioning — accumulating breaking changes until clients can't cope
@RestController
public class UserController {
    // Field renamed from "name" to "fullName" — breaks all clients
    // Field "email" removed — breaks all clients
    // Response wrapped in {"data": ...} — breaks all clients
    @GetMapping("/users")
    public Map<String, Object> getUsers() {
        return Map.of("data", userService.findAll());
    }
}

// CORRECT: Content negotiation with media type versioning
@RestController
@RequestMapping("/users")
public class UserController {

    @GetMapping(produces = "application/vnd.myapp.v1+json")
    public ResponseEntity<List<UserV1>> getUsersV1() {
        return ResponseEntity.ok(userService.findAllV1());
    }

    @GetMapping(produces = "application/vnd.myapp.v2+json")
    public ResponseEntity<UserListV2> getUsersV2() {
        return ResponseEntity.ok(userService.findAllV2());
    }
}
```

## Common Mistakes
The most damaging versioning anti-pattern is pushing breaking changes to a live API without any version bump — this silently breaks every existing client. Equally harmful is the opposite extreme: never versioning and accumulating breaking changes until a large, painful rewrite is needed. URL-based versioning (`/v1/users`) is simple but clutters routes and tempts developers to create entirely new endpoints instead of evolving existing ones. Header-based versioning (`Accept: application/vnd.api.v2+json`) keeps URLs clean but is harder to test in browsers and often forgotten in documentation. Abrupt deprecation — returning 410 Gone with no warning — destroys trust and breaks integrations without giving consumers time to migrate.

## Gotchas
- URL versioning is simpler to implement and easier for clients to understand — prefer it for public APIs
- Header versioning keeps URLs clean but requires tooling support and good documentation
- Never remove old versions immediately — use sunset headers and a deprecation period (6-12 months)
- `Sunset` and `Deprecation` HTTP headers are the RFC-standard way to signal version retirement
- Breaking changes include: renaming fields, changing types, removing fields, changing response structure, changing error formats
- Non-breaking changes (adding fields, adding endpoints) don't need a version bump
- Consider "v0" or "beta" labels for APIs still under active development
- Version the media type, not the URL, when you want to evolve the API in place
- Multiple simultaneous versions are expensive to maintain — plan a clear deprecation schedule
- Document migration guides for each version transition

## Related
- api-design/versioning.md
- api-design/rest-conventions.md
- anti-patterns/api-antipatterns.md
