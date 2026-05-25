---
id: "security-authentication-best-practices"
title: "Authentication Best Practices"
language: "multi"
category: "security"
tags: ["authentication", "passwords", "bcrypt", "argon2", "jwt", "sessions", "mfa", "brute-force"]
version: "n/a"
retrieval_hint: "authentication best practices password hashing bcrypt argon2 JWT sessions MFA brute force protection account lockout"
last_verified: "2026-05-24"
confidence: "high"
---

# Authentication Best Practices

## When to Use
- Implementing user registration and login
- Setting up password storage and verification
- Building session or token-based authentication
- Adding brute force protection and account lockout

## Standard Pattern

```python
# === Password Hashing (the most critical part) ===

import bcrypt
import secrets

# CORRECT: Hash password with bcrypt
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)  # Cost factor 12 (~250ms)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))

# CORRECT: Argon2id (recommended by OWASP for new projects)
from argon2 import PasswordHasher

ph = PasswordHasher(
    time_cost=3,        # Number of iterations
    memory_cost=65536,  # 64 MB memory
    parallelism=4,      # 4 threads
    hash_len=32,
    salt_len=16,
)

hash = ph.hash(password)
try:
    ph.verify(hash, password)  # Raises VerifyMismatchError if wrong
except argon2.exceptions.VerifyMismatchError:
    return False
```

```python
# === JWT Token Management ===

from datetime import datetime, timedelta, timezone
import jwt

SECRET_KEY = "load-from-env-not-hardcoded"  # os.environ["JWT_SECRET"]

def create_access_token(user_id: int) -> str:
    """Short-lived access token (15 minutes)."""
    payload = {
        "sub": str(user_id),
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        "type": "access",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def create_refresh_token(user_id: int) -> str:
    """Long-lived refresh token (7 days)."""
    payload = {
        "sub": str(user_id),
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "type": "refresh",
        "jti": secrets.token_urlsafe(32),  # Unique ID for revocation
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token: str, expected_type: str = "access") -> dict:
    """Verify and decode JWT."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != expected_type:
            raise ValueError(f"Expected {expected_type} token")
        # Check revocation list for refresh tokens
        if expected_type == "refresh" and payload["jti"] in revoked_tokens:
            raise ValueError("Token revoked")
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")
```

```java
// === Java: Spring Security Password Hashing ===

import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.crypto.argon2.Argon2PasswordEncoder;

// CORRECT: BCrypt (battle-tested)
PasswordEncoder encoder = new BCryptPasswordEncoder(12);
String hash = encoder.encode(password);
boolean matches = encoder.matches(inputPassword, hash);

// CORRECT: Argon2id (modern recommendation)
PasswordEncoder argon2 = Argon2PasswordEncoder.defaultsForSpringSecurity_v5_8();
String hash = argon2.encode(password);
```

```python
# === Brute Force Protection ===

from datetime import datetime, timedelta
from collections import defaultdict
import threading

class LoginRateLimiter:
    """Thread-safe login rate limiter with progressive delays."""

    def __init__(self, max_attempts: int = 5, window_minutes: int = 15):
        self.max_attempts = max_attempts
        self.window = timedelta(minutes=window_minutes)
        self._attempts: dict[str, list[datetime]] = defaultdict(list)
        self._lock = threading.Lock()

    def is_locked(self, email: str) -> bool:
        with self._lock:
            cutoff = datetime.utcnow() - self.window
            self._attempts[email] = [
                t for t in self._attempts[email] if t > cutoff
            ]
            return len(self._attempts[email]) >= self.max_attempts

    def record_attempt(self, email: str, success: bool) -> None:
        with self._lock:
            if success:
                self._attempts.pop(email, None)
            else:
                self._attempts[email].append(datetime.utcnow())

rate_limiter = LoginRateLimiter()

@app.post("/login")
async def login(email: str, password: str):
    if rate_limiter.is_locked(email):
        raise HTTPException(429, "Too many attempts. Try again later.")

    user = await authenticate(email, password)
    rate_limiter.record_attempt(email, user is not None)

    if not user:
        raise HTTPException(401, "Invalid credentials")
    ...
```

```python
# === Secure Session Cookie Setup ===

# CORRECT: All security flags on session cookies
response.set_cookie(
    key="session_id",
    value=session_token,
    httponly=True,          # Not readable by JavaScript
    secure=True,            # HTTPS only
    samesite="lax",         # CSRF protection
    max_age=3600,           # 1 hour
    path="/",
    domain=None,            # Current domain only (not subdomains)
)
```

## Common Mistakes

```python
# WRONG: Storing passwords in plaintext or with weak hash
import hashlib
stored = hashlib.md5(password.encode()).hexdigest()  # Cracked instantly

# CORRECT: Use bcrypt or argon2
stored = bcrypt.hashpw(password.encode(), bcrypt.gensalt(12))

# WRONG: Short JWT expiry without refresh tokens
token = jwt.encode({"sub": user_id, "exp": now + timedelta(days=30)}, secret)
# If stolen, attacker has 30 days of access

# CORRECT: Short access + long refresh
access = create_access_token(user_id)    # 15 minutes
refresh = create_refresh_token(user_id)  # 7 days, can be revoked

# WRONG: Hardcoded secrets
SECRET = "my-secret-key"  # Visible in source control

# CORRECT: Environment variables
SECRET = os.environ["JWT_SECRET"]  # 32+ random bytes

# WRONG: No rate limiting on login
@app.post("/login")
async def login(email, password):
    return await authenticate(email, password)  # Unlimited attempts

# CORRECT: Rate limit + lockout
if rate_limiter.is_locked(email):
    raise HTTPException(429, "Account temporarily locked")
```

## Gotchas
- bcrypt has a 72-byte password limit — hash with SHA-256 first if supporting long passwords
- Argon2id is recommended over bcrypt for new projects (memory-hard, GPU-resistant)
- JWTs cannot be truly revoked — use a refresh token blocklist or short expiry + rotation
- `iat` (issued at) in JWT prevents tokens issued before a password change from being used
- Password reset tokens should be single-use, time-limited (1 hour), and sent to verified email only
- `bcrypt.gensalt(rounds=12)` takes ~250ms per hash — that's the security, not a bug
- Never log passwords, tokens, or session IDs — even in error handlers
- Progressive lockout (5 min → 15 min → 1 hour) is better than permanent lockout
- MFA blocks 99% of account compromise attacks — implement it
- Timing-safe comparison (`hmac.compare_digest`) prevents timing attacks on token verification

## Related
- security/web-security-basics.md
- security/owasp-top-10.md
- security/csrf-protection.md
- security/https-tls-must-know.md
- crypto/password-hashing.md
