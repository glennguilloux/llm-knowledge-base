---
id: "anti-patterns-api-no-rate-limiting"
title: "API Anti-Pattern: Missing Rate Limiting"
language: "multi"
category: "anti-patterns"
tags: ["antipatterns", "api", "rate-limiting", "dos", "throttling"]
version: "n/a"
retrieval_hint: "no rate limiting auth endpoints unbounded API access DoS expensive queries token bucket sliding window"
last_verified: "2026-05-24"
confidence: "high"
---

# API Anti-Pattern: Missing Rate Limiting

## When to Use
- API endpoint design and security reviews
- Preventing brute-force attacks on authentication endpoints
- Protecting expensive database queries from abuse
- Ensuring fair resource usage across API consumers

## Standard Pattern

```python
# WRONG: No rate limiting on login endpoint — brute force vulnerable
@app.post("/login")
async def login(email: str, password: str):
    user = await authenticate(email, password)
    if not user:
        raise HTTPException(401, "Invalid credentials")
    return create_token(user)

# CORRECT: Rate limit with slowapi
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, email: str, password: str):
    user = await authenticate(email, password)
    if not user:
        raise HTTPException(401, "Invalid credentials")
    return create_token(user)
```

```javascript
// WRONG: Unbounded expensive query — no limit on results
app.get("/api/reports", async (req, res) => {
    const data = await db.query("SELECT * FROM transactions");
    res.json(data);  // Returns millions of rows, crashes server
});

// CORRECT: Rate limit + result cap
const rateLimit = require("express-rate-limit");

const apiLimiter = rateLimit({
    windowMs: 15 * 60 * 1000,  // 15 minutes
    max: 100,                    // 100 requests per window
    standardHeaders: true,       // Return rate limit info in headers
    legacyHeaders: false,
    message: { error: "Too many requests, please try again later." }
});

app.use("/api/", apiLimiter);

app.get("/api/reports", async (req, res) => {
    const limit = Math.min(req.query.limit || 100, 1000);
    const data = await db.query("SELECT * FROM transactions LIMIT ?", [limit]);
    res.json(data);
});
```

```java
// WRONG: No rate limiting on password reset — email flooding
@PostMapping("/password-reset")
public ResponseEntity<?> resetPassword(@RequestBody ResetRequest req) {
    userService.sendResetEmail(req.getEmail());
    return ResponseEntity.ok().build();  // Attacker floods victim's inbox
}

// CORRECT: Bucket4j rate limiting
@Bean
public Bucket bucket() {
    return Bucket.builder()
        .addLimit(Bandwidth.classic(5, Refill.intervally(5, Duration.ofMinutes(1))))
        .build();
}

@PostMapping("/password-reset")
public ResponseEntity<?> resetPassword(@RequestBody ResetRequest req, HttpServletRequest request) {
    String key = request.getRemoteAddr();
    Bucket bucket = buckets.computeIfAbsent(k -> bucket());
    if (!bucket.tryConsume(1)) {
        return ResponseEntity.status(429)
            .header("Retry-After", "60")
            .body(Map.of("error", "Too many reset attempts"));
    }
    userService.sendResetEmail(req.getEmail());
    return ResponseEntity.ok().build();
}
```

## Common Mistakes
The most damaging rate limiting anti-pattern is having no limits on authentication endpoints, which enables brute-force credential attacks and account enumeration. Equally dangerous is exposing expensive queries (reports, exports, search) without throttling, allowing a single client to exhaust server resources. Many developers implement rate limiting on public endpoints but forget internal or webhook endpoints, creating blind spots. Using IP-based limiting alone misses distributed attacks and punishes users behind shared NATs (corporate networks, universities).

## Gotchas
- Rate limiting must cover login, password reset, registration, and token refresh — not just general API calls
- Return `429 Too Many Requests` with a `Retry-After` header so clients know when to retry
- Use `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` headers for transparency
- IP-based limiting alone is insufficient — combine with user-based and endpoint-specific limits
- Sliding window is more accurate than fixed window but uses more memory; choose based on traffic volume
- Rate limiters must use a shared store (Redis) in multi-instance deployments, not in-memory
- Consider separate limits for authenticated (higher) vs anonymous (lower) users
- Test rate limiting under load — a misconfigured limiter can block legitimate traffic

## Related
- anti-patterns/security-antipatterns.md
- patterns/rate-limiting.md
- anti-patterns/api-no-input-validation.md
