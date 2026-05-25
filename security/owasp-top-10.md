---
id: "security-owasp-top-10"
title: "OWASP Top 10 Security Risks and Prevention"
language: "multi"
category: "security"
tags: ["owasp", "security", "injection", "xss", "broken-auth", "misconfiguration", "vulnerabilities"]
version: "n/a"
retrieval_hint: "OWASP Top 10 2024 2025 security risks injection broken access control authentication misconfiguration SSRF"
last_verified: "2026-05-24"
confidence: "high"
---

# OWASP Top 10 Security Risks and Prevention

## When to Use
- Pre-deployment security review of any web application
- Threat modeling during application design
- Security audit checklist for existing codebases
- Onboarding developers to common vulnerability classes

## Standard Pattern

```python
# === A01: Broken Access Control ===
# Enforce server-side authorization on EVERY endpoint

from fastapi import Depends, HTTPException, status
from functools import wraps

# WRONG: No authorization check
@app.get("/admin/users")
async def list_users(): ...  # Anyone can access!

# CORRECT: Role-based access control
def require_role(role: str):
    async def checker(current_user: User = Depends(get_current_user)):
        if role not in current_user.roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return current_user
    return checker

@app.get("/admin/users")
async def list_users(admin: User = Depends(require_role("admin"))):
    return await db.query(User).all()

# CORRECT: Resource-level access control
@app.get("/documents/{doc_id}")
async def get_document(doc_id: int, user: User = Depends(get_current_user)):
    doc = await db.get(Document, doc_id)
    if doc.owner_id != user.id and "admin" not in user.roles:
        raise HTTPException(status_code=403)
    return doc
```

```java
// === A02: Cryptographic Failures ===
// Use strong algorithms, never roll your own crypto

import org.mindrot.jbcrypt.BCrypt;
import javax.crypto.AEADBadTagException;
import com.nimbusds.jwt.*;

// CORRECT: Password hashing with bcrypt
String hash = BCrypt.hashpw(password, BCrypt.gensalt(12));
boolean valid = BCrypt.checkpw(input, hash);

// CORRECT: Encrypt sensitive data at rest (AES-256-GCM)
import javax.crypto.Cipher;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.SecretKeySpec;

Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
cipher.init(Cipher.ENCRYPT_MODE, secretKey);
byte[] iv = cipher.getIV();
byte[] ciphertext = cipher.doFinal(plaintext.getBytes());
```

```typescript
// === A03: Injection Prevention ===
// NEVER concatenate user input into queries/commands/HTML

import { DataSource } from "typeorm";

// CORRECT: Parameterized queries
const users = await dataSource.query(
    "SELECT * FROM users WHERE email = $1 AND active = $2",
    [email, true]
);

// CORRECT: Input validation with zod
import { z } from "zod";

const SearchSchema = z.object({
    query: z.string().min(1).max(200).regex(/^[a-zA-Z0-9\s]+$/),
    page: z.number().int().min(1).default(1),
});

// CORRECT: HTML escaping in templates (React auto-escapes)
function UserGreeting({ name }: { name: string }) {
    return <div>Hello, {name}</div>;  // Auto-escaped
}
```

```python
# === A04: Insecure Design ===
# Threat modeling and secure design patterns

# CORRECT: Rate limiting on auth endpoints
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/login")
@limiter.limit("5/minute")
async def login(request: Request):
    ...

# CORRECT: Principle of least privilege
# Database user for app should NOT have DROP, ALTER permissions
# GRANT SELECT, INSERT, UPDATE, DELETE ON app_db.* TO 'app_user'@'%';

# CORRECT: Secure defaults
SECURITY_DEFAULTS = {
    "DEBUG": False,
    "SESSION_COOKIE_SECURE": True,
    "SESSION_COOKIE_HTTPONLY": True,
    "CSRF_COOKIE_SECURE": True,
    "SECURE_SSL_REDIRECT": True,
}
```

```python
# === A05: Security Misconfiguration ===
# CORRECT: Disable debug in production, remove defaults

import os
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

# CORRECT: Remove default credentials
# Never ship with admin/admin, change all default passwords

# CORRECT: Proper CORS configuration
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com"],  # NOT ["*"]
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization"],
)

# CORRECT: Security headers middleware
@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

```bash
# === A06: Vulnerable Components ===
# Check for known vulnerabilities regularly

# Python: pip-audit
pip install pip-audit && pip-audit

# Node.js: npm audit
npm audit --production

# Java: OWASP Dependency-Check
dependency-check --scan ./target/

# Fix: Update vulnerable packages immediately
pip install --upgrade vulnerable-package
npm update vulnerable-package
```

```python
# === A07: Authentication Failures ===
# Strong password policies, MFA, account lockout

from datetime import datetime, timedelta
from collections import defaultdict

# CORRECT: Account lockout after failed attempts
login_attempts: dict[str, list[datetime]] = defaultdict(list)
MAX_ATTEMPTS = 5
LOCKOUT_MINUTES = 15

def check_lockout(email: str) -> bool:
    attempts = login_attempts[email]
    recent = [a for a in attempts if a > datetime.utcnow() - timedelta(minutes=LOCKOUT_MINUTES)]
    login_attempts[email] = recent
    return len(recent) >= MAX_ATTEMPTS

# CORRECT: Strong password requirements
from pydantic import BaseModel, Field

class PasswordChange(BaseModel):
    new_password: str = Field(
        ...,
        min_length=12,
        pattern=r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).+$"
    )
```

```python
# === A08: Data Integrity Failures ===
# Verify deserialization, signed updates

import hmac
import hashlib

# CORRECT: Verify webhook signatures
def verify_webhook(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)

# CORRECT: Pin dependencies with hashes
# requirements.txt:
# flask==3.0.0 --hash=sha256:abc123...
```

```python
# === A09: Logging and Monitoring Failures ===
# Log security events, don't log secrets

import logging
import structlog

logger = structlog.get_logger()

# CORRECT: Log security-relevant events
logger.info("login_success", user_id=user.id, ip=request.client.host)
logger.warning("login_failure", email=email, ip=request.client.host)
logger.error("access_denied", user_id=user.id, resource=path)

# WRONG: Never log secrets
# logger.info(f"User auth: password={password}")  # NEVER
```

```python
# === A10: Server-Side Request Forgery (SSRF) ===
# Validate and allowlist URLs, never pass user URLs directly

import ipaddress
from urllib.parse import urlparse

ALLOWED_DOMAINS = {"api.stripe.com", "api.github.com"}

def validate_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ("https",):
        raise ValueError("Only HTTPS allowed")
    if parsed.hostname not in ALLOWED_DOMAINS:
        raise ValueError(f"Domain not allowlisted: {parsed.hostname}")
    # Block internal IPs
    try:
        ip = ipaddress.ip_address(parsed.hostname)
        if ip.is_private:
            raise ValueError("Internal IPs not allowed")
    except ValueError:
        pass  # hostname is not an IP, that's fine
    return url
```

## Common Mistakes

```python
# WRONG: Checking authorization only on the client
<button onClick={() => fetch("/api/admin/users")}>Admin</button>
# User can just curl the endpoint directly

# CORRECT: Always check on the server
@app.get("/api/admin/users")
async def list_users(admin: User = Depends(require_role("admin"))):
    return await get_all_users()
```

```python
# WRONG: String concatenation in SQL
query = f"SELECT * FROM products WHERE category = '{category}'"
# Attacker: category = "' UNION SELECT password FROM users--"

# CORRECT: Parameterized queries
cursor.execute("SELECT * FROM products WHERE category = %s", (category,))
```

```python
# WRONG: CORS allow all origins
Access-Control-Allow-Origin: *

# CORRECT: Specific allowed origins
Access-Control-Allow-Origin: https://app.example.com
```

```python
# WRONG: Logging passwords or tokens
logger.info(f"Login attempt: email={email}, password={password}")

# CORRECT: Log only non-sensitive context
logger.info("login_attempt", email=email, ip=ip_address, success=True)
```

```python
# WRONG: Fetching URLs provided by users without validation
import requests
response = requests.get(user_provided_url)  # SSRF!

# CORRECT: Validate URL against allowlist
url = validate_url(user_provided_url)  # Checks domain + blocks internal IPs
response = requests.get(url)
```

## Gotchas
- Broken Access Control is #1 for a reason — it's the most common and impactful vulnerability
- CORS is a browser-enforced policy, NOT server security — it doesn't protect API-to-API calls
- `pip-audit` and `npm audit` only find KNOWN vulnerabilities — keep dependencies updated
- Rate limiting must be per-user (not per-IP) behind CDN/proxy scenarios
- HMAC comparison must use `hmac.compare_digest()` (constant-time) to prevent timing attacks
- Security headers don't protect API consumers — they protect browsers
- SSRF can access cloud metadata endpoints (169.254.169.254 on AWS) to steal credentials
- Logging too much is also a risk — logs can contain PII that violates GDPR
- JWT revocation requires a blocklist — JWTs are valid until expiry by design
- `DEBUG=True` in production leaks stack traces, environment variables, and source code

## Related
- security/web-security-basics.md
- security/xss-prevention.md
- security/sql-injection-prevention.md
- security/csrf-protection.md
- security/authentication-best-practices.md
