---
id: "security-web-security-basics"
title: "Web Security Fundamentals"
language: "multi"
category: "security"
tags: ["security", "owasp", "xss", "csrf", "sql-injection", "input-validation"]
version: "n/a"
retrieval_hint: "OWASP XSS CSRF SQL injection security input validation Content Security Policy"
last_verified: "2026-05-24"
confidence: "high"
---

# Web Security Fundamentals

## When to Use
- Building web applications with user input
- Handling authentication and sessions
- Processing data from external sources
- Pre-deployment security review

## Standard Pattern

```python
# === SQL Injection Prevention ===
# ALWAYS use parameterized queries
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))  # SAFE

# ORM is also safe (parameterized under the hood)
user = db.query(User).filter(User.email == email).first()  # SAFE
```

```javascript
// === XSS Prevention ===
// React auto-escapes JSX — don't bypass it
function UserInput({ name }) {
  return <div>{name}</div>;  // SAFE — auto-escaped
}

// If you MUST render HTML, sanitize first
import DOMPurify from 'dompurify';
function RichContent({ html }) {
  return <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(html) }} />;
}

// Content Security Policy header
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'
```

```python
# === CSRF Protection ===
# FastAPI: use SameSite cookies + CSRF tokens
from fastapi_csrf_protect import CsrfProtect

# Django: middleware handles it
# MIDDLEWARE = ['django.middleware.csrf.CsrfViewMiddleware']

# General: SameSite cookie attribute
Set-Cookie: session=abc; SameSite=Strict; Secure; HttpOnly
```

```python
# === Input Validation ===
from pydantic import BaseModel, EmailStr, Field

class CreateUserRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    age: int = Field(..., ge=0, le=150)

# Reject unexpected fields
class Config:
    extra = "forbid"
```

```python
# === Authentication Best Practices ===
import bcrypt
from datetime import datetime, timedelta
import jwt

# Hash passwords with bcrypt (not MD5/SHA)
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

# JWT with short expiry
token = jwt.encode(
    {"sub": str(user.id), "exp": datetime.utcnow() + timedelta(minutes=15)},
    SECRET_KEY,
    algorithm="HS256"
)

# Refresh tokens for long sessions
refresh_token = jwt.encode(
    {"sub": str(user.id), "exp": datetime.utcnow() + timedelta(days=7)},
    REFRESH_SECRET,
    algorithm="HS256"
)
```

```python
# === Secure Headers ===
# Add these HTTP response headers:
headers = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "0",  # Modern browsers don't need this
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}
```

```python
# === OWASP Top 10 Summary (2021) ===
# A01: Broken Access Control    → enforce server-side authorization
# A02: Cryptographic Failures   → use bcrypt, TLS, don't store secrets in code
# A03: Injection                 → parameterized queries, input validation
# A04: Insecure Design          → threat modeling, security requirements
# A05: Security Misconfiguration→ disable debug, remove defaults, CORS
# A06: Vulnerable Components    → update dependencies, audit with npm audit / pip-audit
# A07: Auth Failures            → MFA, rate limiting, strong passwords
# A08: Data Integrity Failures  → verify deserialization, signed updates
# A09: Logging Failures         → log auth events, don't log PII/secrets
# A10: SSRF                     → validate/allowlist URLs, don't pass user URLs to requests
```

## Common Mistakes

```python
# WRONG: SQL string formatting
query = f"SELECT * FROM users WHERE email = '{email}'"  # SQL injection!
# Attacker: email = "' OR '1'='1"

# CORRECT: Parameterized queries
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))

# WRONG: Storing passwords in plaintext or with weak hash
import hashlib
password_hash = hashlib.md5(password.encode()).hexdigest()  # Cracked in seconds

# CORRECT: Use bcrypt or argon2
import bcrypt
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))

# WRONG: innerHTML with user input
element.innerHTML = userInput;  // XSS if userInput contains <script>

# CORRECT: textContent or framework escaping
element.textContent = userInput;

# WRONG: CORS allow all
Access-Control-Allow-Origin: *  # Any website can call your API

# CORRECT: Restrict to known origins
Access-Control-Allow-Origin: https://app.example.com

# WRONG: Logging sensitive data
logger.info(f"User login: email={email}, password={password}")

# CORRECT: Log non-sensitive context
logger.info(f"User login: email={email}, ip={request.client.host}")
```

## Gotchas
- `innerHTML` is an XSS vector — use `textContent` or framework auto-escaping
- `bcrypt` is slow by design — that's the point. Don't use SHA/MD5 for passwords
- `SameSite=Strict` prevents CSRF completely but breaks legitimate cross-origin links
- `HttpOnly` cookies can't be read by JavaScript — prevents token theft via XSS
- `Secure` cookies are only sent over HTTPS — always use in production
- CORS is enforced by browsers, not by server-to-server requests — it's not a firewall
- JWTs are not encrypted — don't put secrets in the payload
- Short JWT expiry (15 min) + refresh token (7 days) is the standard pattern
- Input validation on the client is UX; on the server is security — do both
- `Content-Security-Policy` prevents inline scripts — the strongest XSS defense

## Related
- api-design/rest-conventions.md
- error-handling/structured-errors.md
- csharp/web/aspnet-basics.md
