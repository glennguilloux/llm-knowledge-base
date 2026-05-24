---
id: "anti-patterns-security-cors-misconfig"
title: "Security Anti-Pattern: CORS Misconfiguration"
language: "multi"
category: "anti-patterns"
tags: ["antipatterns", "security", "cors", "access-control", "cross-origin"]
version: "n/a"
retrieval_hint: "CORS wildcard origin reflection credentials with wildcard Access-Control-Allow-Origin misconfigured"
last_verified: "2026-05-24"
confidence: "high"
---

# Security Anti-Pattern: CORS Misconfiguration

## When to Use
- Configuring cross-origin API access
- Setting up frontend-backend communication across domains
- Reviewing security headers in API responses
- Debugging "blocked by CORS policy" browser errors

## Standard Pattern

```python
# WRONG: Wildcard allows any origin (FastAPI)
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Any website can call your API
    allow_credentials=True,     # Sends cookies cross-origin
    allow_methods=["*"],
    allow_headers=["*"],
)

# CORRECT: Restrict origins (FastAPI)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

```javascript
// WRONG: Reflecting origin header (Express)
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', req.headers.origin);  // Reflects any origin
  res.header('Access-Control-Allow-Credentials', 'true');
  next();
});

// CORRECT: Allowlist check (Express)
const cors = require('cors');
const ALLOWED = ['https://app.example.com', 'https://admin.example.com'];

app.use(cors({
  origin: (origin, callback) => {
    if (!origin || ALLOWED.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
}));
```

```java
// WRONG: Wildcard CORS (Spring)
@CrossOrigin(origins = "*", allowCredentials = "true")  // Browsers reject this combo
@GetMapping("/api/data")
public Data getData() { ... }

// CORRECT: Specific origins (Spring)
@CrossOrigin(origins = "https://app.example.com", allowCredentials = "true")
@GetMapping("/api/data")
public Data getData() { ... }

// CORRECT: Global CORS config
@Configuration
public class CorsConfig implements WebMvcConfigurer {
    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
            .allowedOrigins("https://app.example.com")
            .allowedMethods("GET", "POST", "PUT", "DELETE")
            .allowCredentials(true);
    }
}
```

```python
# WRONG: Django CORS unrestricted
# settings.py
CORS_ALLOW_ALL_ORIGINS = True  # Any origin can make requests

# CORRECT: Django CORS allowlist
# settings.py
CORS_ALLOWED_ORIGINS = [
    "https://app.example.com",
    "https://admin.example.com",
]
CORS_ALLOW_CREDENTIALS = True
```

## Common Mistakes
CORS misconfiguration is one of the most common API security issues. The biggest mistakes are using `Access-Control-Allow-Origin: *` (allows any website to read API responses), reflecting the `Origin` header back as the allowed origin (defeats the purpose of CORS), and combining `*` with `allowCredentials: true` (browsers actually block this, but it signals misunderstanding). CORS is a browser-enforced mechanism — it does NOT protect against server-to-server requests. The real purpose of CORS is controlling which websites can read responses from your API in the browser.

## Gotchas
- `Access-Control-Allow-Origin: *` with `Access-Control-Allow-Credentials: true` is rejected by browsers — but the intent is wrong
- Reflecting `req.headers.origin` is equivalent to `*` — any origin gets access
- Preflight requests (`OPTIONS`) must return CORS headers too, not just the actual method
- `null` origin can be sent by sandboxed iframes, `file://` URLs, and redirects — do not allow `null`
- Wildcard subdomain matching (`*.example.com`) is NOT supported by CORS spec — list each origin explicitly
- `Access-Control-Expose-Headers` controls which response headers JavaScript can read — default is only simple response headers
- CORS does NOT protect against CSRF — use CSRF tokens for state-changing operations
- Proxying through the same origin (nginx reverse proxy) bypasses CORS entirely but may introduce SSRF

## Related
- security/web-security-basics.md
- security/csrf-protection.md
- python/web/fastapi/cors-static.md
