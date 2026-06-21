---
id: "security-session-management"
title: "Session Management for Web Applications"
language: "multi"
category: "security"
tags: ["session-management", "security", "cookies", "csrf", "session-fixation", "token-rotation", "secure-cookies"]
version: "n/a"
retrieval_hint: "web session management secure cookies CSRF session fixation token rotation cookie flags HttpOnly SameSite Secure expiry"
last_verified: "2026-06-20"
confidence: "medium"
---

# Session Management for Web Applications

## When to Use
- Implementing cookie-based login sessions for web applications
- Hardening session cookies and refresh-token flows
- Reviewing session fixation, logout, and expiry behavior
- Designing browser-accessible APIs that need CSRF-aware session protection

## Standard Pattern

```python
# === Python: Secure Session Cookie and Rotation ===
import secrets
from datetime import datetime, timedelta, timezone

def create_session_token() -> str:
    return secrets.token_urlsafe(32)

def set_session_cookie(response, token: str, user_id: int):
    response.set_cookie(
        key="session_id",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=3600,
        path="/",
    )
    response.set_cookie("session_user", str(user_id), max_age=3600, samesite="lax")

def rotate_session(existing_token: str) -> str:
    # CORRECT: Issue a fresh session identifier after login and privilege changes
    return secrets.token_urlsafe(32)
```

```python
# === Python: Session Expiry and Invalidation ===
from datetime import datetime, timedelta, timezone

class SessionStore:
    def __init__(self):
        self.sessions: dict[str, dict] = {}

    def is_valid(self, token: str) -> bool:
        session = self.sessions.get(token)
        if not session:
            return False
        if session["expires_at"] < datetime.now(timezone.utc):
            self.sessions.pop(token, None)
            return False
        return True

    def invalidate(self, token: str) -> None:
        self.sessions.pop(token, None)
```

```java
// === Java: Secure Cookie Defaults ===
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletResponse;

void setSessionCookie(HttpServletResponse response, String token) {
    Cookie cookie = new Cookie("session_id", token);
    cookie.setHttpOnly(true);
    cookie.setSecure(true);
    cookie.setPath("/");
    cookie.setMaxAge(60 * 60);
    response.setHeader("SameSite", "Lax");
    response.addCookie(cookie);
}
```

## Common Mistakes

```python
# WRONG: Reusing the anonymous session after login
session_id = request.cookies.get("session_id")
authenticate_user()

# CORRECT: Regenerate the session identifier after authentication
new_session_id = rotate_session(session_id)
```

```python
# WRONG: Cookie readable by browser JavaScript
response.set_cookie("session_id", token, httponly=False)

# CORRECT: Prevent JavaScript access to the session cookie
response.set_cookie("session_id", token, httponly=True, secure=True, samesite="lax")
```

```python
# WRONG: No idle or absolute expiry
sessions[token] = {"user_id": user_id}

# CORRECT: Enforce both idle and absolute expiry
sessions[token] = {
    "user_id": user_id,
    "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
}
```

```python
# WRONG: Logout only clears client-side state
delete_browser_cookie()

# CORRECT: Invalidate the server-side session too
sessions.pop(token, None)
```

## Gotchas
- Regenerate session identifiers after login, logout, password change, and privilege escalation
- `HttpOnly` prevents script access but does not replace CSRF protection
- `Secure` is required for production cookies so they are not sent over plain HTTP
- `SameSite=Lax` is a practical default; `Strict` can break email links and third-party login flows
- Long-lived refresh tokens need rotation, revocation, and server-side storage
- Session stores must remove expired sessions to avoid unbounded memory growth

## Related
- security/authentication-best-practices.md
- security/csrf-protection.md
- security/web-security-basics.md
- security/https-tls-must-know.md
