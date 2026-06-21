---
id: "security-python-best-practices"
title: "Python Security Best Practices"
language: "python"
category: "security"
tags: ["python", "security", "best-practices", "secrets", "input-validation", "parameterized-queries", "logging", "secure-defaults"]
version: "3.10+"
retrieval_hint: "Python security best practices secrets environment variables input validation parameterized queries logging redaction secure defaults"
last_verified: "2026-06-20"
confidence: "medium"
---

# Python Security Best Practices

## When to Use
- Designing secure defaults for a Python web service or API
- Reviewing Python code for secret handling, validation, and safe database access
- Adding defensive checks before deploying Python applications
- Teaching Python developers practical OWASP-aligned prevention patterns

## Standard Pattern

```python
# === Python Security Baseline ===
import os
import logging
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr, Field

# CORRECT: Load secrets from the environment, never from source code
API_KEY = os.environ["API_KEY"]
SESSION_SECRET = os.environ["SESSION_SECRET"]

# CORRECT: Configure structured logging without sensitive fields
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

# CORRECT: Validate and constrain input with a schema
class CreateUserRequest(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=80)
    age: int = Field(ge=0, le=130)

# CORRECT: Use short-lived tokens for session refresh windows
def token_expires_soon(expires_at: datetime) -> bool:
    return expires_at < datetime.utcnow() + timedelta(minutes=5)
```

```python
# === Python: Safe Database Access ===
from psycopg2 import connect
from psycopg2.extras import RealDictCursor

conn = connect(os.environ["DATABASE_URL"])

# CORRECT: Parameterized query for all user-controlled values
def find_user_by_email(email: str):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT id, email FROM users WHERE email = %s", (email,))
        return cur.fetchone()

# CORRECT: Safe identifier selection from an allowlist
ALLOWED_SORT_COLUMNS = {"created_at", "email", "display_name"}

def list_users(sort_by: str):
    column = sort_by if sort_by in ALLOWED_SORT_COLUMNS else "created_at"
    query = f"SELECT id, email FROM users ORDER BY {column} LIMIT 100"
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query)
        return cur.fetchall()
```

```python
# === Python: Secure Defaults ===
SECURITY_DEFAULTS = {
    "DEBUG": False,
    "SESSION_COOKIE_HTTPONLY": True,
    "SESSION_COOKIE_SECURE": True,
    "SESSION_COOKIE_SAMESITE": "lax",
    "CORS_ALLOW_ALL_ORIGINS": False,
}

# CORRECT: Reject unexpected JSON fields in API requests
request_model = CreateUserRequest.model_validate(request_body)
```

## Common Mistakes

```python
# WRONG: Hardcoded API key in source
API_KEY = "example-secret"  # Commits to version control

# CORRECT: Load from environment
API_KEY = os.environ["API_KEY"]
```

```python
# WRONG: Building SQL from request fields
query = f"SELECT * FROM users WHERE email = '{email}'"

# CORRECT: Use bind parameters
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
```

```python
# WRONG: Logging credentials or tokens
logger.info("login", email=email, credential=credential)

# CORRECT: Log non-sensitive context only
logger.info("login", email=email, ip_address=client_ip, success=success)
```

```python
# WRONG: Accepting arbitrary sort parameters
sort_by = request.query_params["sort"]
query = f"SELECT * FROM users ORDER BY {sort_by}"

# CORRECT: Map to an allowlist
sort_by = request.query_params.get("sort", "created_at")
column = ALLOWED_SORT_COLUMNS.get(sort_by, "created_at")
```

## Gotchas
- Python environment variables are still process-visible; prefer a secrets manager for high-risk credentials
- Parameterized queries protect values, but identifiers still need allowlisting or safe SQL builders
- Pydantic validation is a security boundary only when enforced on the server
- Debug mode can expose stack traces, configuration, and source snippets
- Logging middleware should redact authorization headers, cookies, passwords, and API keys
- `os.environ["NAME"]` fails loudly if a required secret is missing; use that failure during deployment checks

## Related
- security/owasp-top-10.md
- security/web-security-basics.md
- security/authentication-best-practices.md
- security/sql-injection-prevention.md
