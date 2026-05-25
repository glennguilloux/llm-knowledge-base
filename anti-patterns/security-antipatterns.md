---
id: "antipatterns-security"
title: "Security Anti-Patterns"
language: "multi"
category: "anti-patterns"
tags: ["antipatterns", "security", "owasp", "injection", "xss", "csrf"]
version: "n/a"
retrieval_hint: "security antipatterns hardcoded secrets SQL injection XSS CSRF"
last_verified: "2026-05-24"
confidence: "high"
---

# Security Anti-Patterns

## When to Use
- Security code reviews
- Training LLMs to write secure code
- Pre-deployment security audits
- Onboarding developers on secure coding

## Standard Pattern

```python
# WRONG: Hardcoded secrets
API_KEY = "sk-1234567890abcdef"
DATABASE_URL = "postgresql://user:password@localhost/db"

# CORRECT: Environment variables
import os
API_KEY = os.environ["API_KEY"]
DATABASE_URL = os.environ["DATABASE_URL"]

# WRONG: SQL string formatting (SQL injection)
query = f"SELECT * FROM users WHERE email = '{email}'"
cursor.execute(query)  # Attacker: email = "' OR 1=1 --"

# CORRECT: Parameterized queries
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))

# WRONG: Using eval on user input
result = eval(user_input)  # Attacker: __import__('os').system('rm -rf /')

# CORRECT: Parse safely
import ast
result = ast.literal_eval(user_input)  # Only literals, no code execution

# WRONG: Trusting client-side validation only
@app.post("/register")
def register(email: str, password: str):
    db.insert(email, password)  # No server-side validation

# CORRECT: Validate on server
from pydantic import BaseModel, EmailStr
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
```

```javascript
// WRONG: XSS via innerHTML
element.innerHTML = userInput;  // <script>alert('xss')</script>

// CORRECT: Use textContent or sanitize
element.textContent = userInput;
// Or with React: JSX auto-escapes
return <div>{userInput}</div>;

// WRONG: Logging sensitive data
console.log("User login:", { email, password, ssn });

// CORRECT: Log only what's needed, mask sensitive fields
console.log("User login:", { email, passwordLength: password.length });
```

```java
// WRONG: Weak password hashing
String hash = MD5.digest(password.getBytes());

// CORRECT: Use bcrypt or argon2
BCryptPasswordEncoder encoder = new BCryptPasswordEncoder();
String hash = encoder.encode(password);

// WRONG: CORS wildcard
@CrossOrigin(origins = "*")  // Any origin can make requests

// CORRECT: Restrict origins
@CrossOrigin(origins = {"https://app.example.com"})
```

```sql
-- WRONG: Dynamic SQL in stored procedure
EXEC('SELECT * FROM ' + @tableName + ' WHERE id = ' + @id);

-- CORRECT: Parameterized queries
SELECT * FROM users WHERE id = @id;
```

## Common Mistakes
The most critical security anti-patterns are hardcoded secrets (exposed in version control), SQL injection (data breach), and XSS (session hijacking). Weak password hashing (MD5/SHA1) makes credential theft trivial. CORS wildcards allow any site to make authenticated requests. Missing server-side validation trusts client input blindly.

## Gotchas
- Client-side validation is a UX feature, NOT a security measure — always validate server-side
- `innerHTML` is an XSS vector — use `textContent` or framework escaping
- MD5 and SHA1 are NOT password hashing algorithms — use bcrypt/argon2
- `eval()` on user input is ALWAYS a vulnerability, regardless of context
- CORS `*` with credentials is rejected by browsers, but without credentials it works
- SQL injection works in stored procedures too if using dynamic SQL
- Secrets in `.env` files can be committed — add `.env` to `.gitignore`
- HTTP headers like `X-Frame-Options` and `Content-Security-Policy` prevent entire classes of attacks

## Related
- security/web-security-basics.md
- python/stdlib/env-config.md
- api-design/rest-conventions.md
