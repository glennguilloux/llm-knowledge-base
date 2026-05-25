---
id: "security-csrf-protection"
title: "Cross-Site Request Forgery (CSRF) Protection"
language: "multi"
category: "security"
tags: ["csrf", "security", "samesite", "csrf-token", "double-submit", "cross-site-request-forgery"]
version: "n/a"
retrieval_hint: "CSRF protection cross-site request forgery SameSite cookies CSRF token double submit pattern prevention"
last_verified: "2026-05-24"
confidence: "high"
---

# Cross-Site Request Forgery (CSRF) Protection

## When to Use
- Building state-changing endpoints (POST, PUT, DELETE, PATCH)
- Setting up session-based authentication
- Securing cookie-based auth flows
- Designing API security for browser-accessible services

## Standard Pattern

```python
# === FastAPI: CSRF Protection with Tokens ===

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
import secrets
import hmac
import hashlib

app = FastAPI()
CSRF_SECRET = "your-secret-key-here"  # Load from env in production

def generate_csrf_token(session_id: str) -> str:
    """Generate HMAC-based CSRF token tied to session."""
    return hmac.new(
        CSRF_SECRET.encode(),
        session_id.encode(),
        hashlib.sha256
    ).hexdigest()

def verify_csrf(session_id: str, token: str) -> bool:
    """Verify CSRF token using constant-time comparison."""
    expected = generate_csrf_token(session_id)
    return hmac.compare_digest(expected, token)

async def require_csrf(request: Request):
    """Dependency: verify CSRF token for state-changing requests."""
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return  # Safe methods don't need CSRF protection

    session_id = request.cookies.get("session_id", "")
    token = request.headers.get("X-CSRF-Token", "")

    if not session_id or not token:
        raise HTTPException(status_code=403, detail="Missing CSRF token")

    if not verify_csrf(session_id, token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

# Use on state-changing routes
@app.post("/transfer")
async def transfer_money(request: Request, _csrf=Depends(require_csrf)):
    ...
```

```python
# === Django: Built-in CSRF Middleware ===

# settings.py — enable middleware (default in new projects)
MIDDLEWARE = [
    'django.middleware.csrf.CsrfViewMiddleware',
    ...
]

# In templates — always include the token in forms
# <form method="POST">
#     {% csrf_token %}
#     <input type="text" name="amount">
#     <button type="submit">Transfer</button>
# </form>

# For AJAX requests — read from cookie and set header
# JavaScript:
# const csrfToken = document.cookie.split('csrftoken=')[1]?.split(';')[0];
# fetch("/api/transfer", {
#     method: "POST",
#     headers: { "X-CSRFToken": csrfToken },
#     body: JSON.stringify(data),
# });
```

```typescript
// === Express: csurf middleware pattern ===

import express from "express";
import csrf from "csurf";
import cookieParser from "cookie-parser";

const app = express();
app.use(cookieParser());

// CSRF protection middleware
const csrfProtection = csrf({ cookie: { httpOnly: true, secure: true, sameSite: "strict" } });

// Endpoint to get CSRF token (call on page load)
app.get("/api/csrf-token", csrfProtection, (req, res) => {
    res.json({ csrfToken: req.csrfToken() });
});

// Protected endpoints
app.post("/api/transfer", csrfProtection, (req, res) => {
    // CSRF token validated automatically
    res.json({ success: true });
});
```

```java
// === Spring Security: CSRF Configuration ===

import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.csrf.CookieCsrfTokenRepository;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .csrf(csrf -> csrf
                .csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse())
                // Skip CSRF for API endpoints using bearer tokens
                .ignoringRequestMatchers("/api/auth/**")
            );
        return http.build();
    }
}

// Frontend reads CSRF token from cookie and sends as header:
// X-XSRF-TOKEN: <token from XSRF-TOKEN cookie>
```

```python
# === SameSite Cookie Attribute (first line of defense) ===

# CORRECT: Set SameSite on all session cookies
from fastapi import Response

@app.post("/login")
async def login(response: Response):
    response.set_cookie(
        key="session_id",
        value=session_token,
        httponly=True,      # Not accessible via JavaScript
        secure=True,        # HTTPS only
        samesite="lax",     # Blocks most CSRF (allows top-level navigations)
        max_age=3600,
    )
    # Use "strict" for maximum protection (breaks some cross-site flows)
    # Use "lax" for good protection with usability (recommended default)
```

## Common Mistakes

```python
# WRONG: No CSRF protection on state-changing endpoints
@app.post("/transfer")
async def transfer(request: Request):
    # Attacker can forge this request from any website
    amount = request.json()["amount"]

# CORRECT: Require CSRF token
@app.post("/transfer")
async def transfer(request: Request, _csrf=Depends(require_csrf)):
    amount = request.json()["amount"]
```

```python
# WRONG: Using SameSite=None (disables protection)
response.set_cookie("session", token, samesite="none")

# CORRECT: Use lax or strict
response.set_cookie("session", token, samesite="lax", secure=True, httponly=True)
```

```python
# WRONG: GET requests that change state (CSRF only protects POST/PUT/DELETE)
@app.get("/delete-account")  # Attacker can embed in <img src="/delete-account">
async def delete_account(user: User = Depends(get_current_user)):
    await delete_user(user.id)

# CORRECT: Use POST for state changes
@app.post("/delete-account")
async def delete_account(request: Request, _csrf=Depends(require_csrf)):
    await delete_user(user.id)
```

```python
# WRONG: Comparing CSRF tokens with == (timing attack vulnerability)
if request_token == expected_token:
    pass

# CORRECT: Constant-time comparison
if hmac.compare_digest(request_token, expected_token):
    pass
```

## Gotchas
- `SameSite=Lax` prevents CSRF from cross-site POST but allows top-level GET navigations — use for most apps
- `SameSite=Strict` blocks ALL cross-site cookie sending — too aggressive for login flows and email links
- Bearer token auth (JWT in Authorization header) is inherently CSRF-safe — tokens aren't sent automatically by browsers
- Cookie-based auth is vulnerable to CSRF; header-based auth (Bearer) is not
- CSRF tokens must be tied to the user's session — a shared token is useless
- AJAX requests need the CSRF token in a custom header (X-CSRF-Token), not just the body
- Double-submit pattern (token in cookie + header) works without server-side session storage
- SameSite cookie support is universal in modern browsers (2020+)
- CORS does NOT prevent CSRF — CORS is a browser mechanism for reading responses, not sending requests

## Related
- security/web-security-basics.md
- security/owasp-top-10.md
- security/authentication-best-practices.md
- security/https-tls-must-know.md
