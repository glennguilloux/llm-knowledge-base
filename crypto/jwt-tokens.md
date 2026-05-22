---
id: "crypto-jwt-tokens"
title: "JWT Token Creation and Validation"
language: "multi"
category: "crypto"
subcategory: "authentication"
tags: ["jwt", "token", "authentication", "bearer", "signing"]
version: "n/a"
retrieval_hint: "JWT token creation validation signing bearer authentication"
last_verified: "2026-05-22"
confidence: "high"
---

# JWT Token Creation and Validation

## When to Use
- Stateless API authentication
- Token-based auth for SPAs and mobile apps
- Microservice-to-microservice auth
- Single sign-on (SSO)

## Standard Pattern

### Python

```python
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

def create_token(data: dict, expires_minutes: int = 30) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# Usage
token = create_token({"sub": "user@example.com", "role": "admin"})
payload = verify_token(token)
```

### Java

```java
import io.jsonwebtoken.*;

String token = Jwts.builder()
    .setSubject("user@example.com")
    .setIssuedAt(new Date())
    .setExpiration(new Date(System.currentTimeMillis() + 3600000))
    .signWith(SignatureAlgorithm.HS256, secretKey)
    .compact();

Claims claims = Jwts.parser()
    .setSigningKey(secretKey)
    .parseClaimsJws(token)
    .getBody();
```

### TypeScript (Node.js)

```typescript
import jwt from 'jsonwebtoken';

const token = jwt.sign(
  { sub: 'user@example.com', role: 'admin' },
  secretKey,
  { expiresIn: '1h' }
);

const payload = jwt.verify(token, secretKey);
```

## Common Mistakes

```python
# WRONG: No expiration
token = jwt.encode({"sub": user_id}, SECRET_KEY, algorithm=ALGORITHM)  # Lives forever!

# CORRECT: Set expiration
expire = datetime.now(timezone.utc) + timedelta(minutes=30)
token = jwt.encode({"sub": user_id, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

# WRONG: Using HS256 for microservices (shared secret)
token = jwt.encode(data, shared_secret, algorithm="HS256")  # Secret must be shared!

# CORRECT: Use RS256 for microservices (public/private key)
token = jwt.encode(data, private_key, algorithm="RS256")
payload = jwt.decode(token, public_key, algorithms=["RS256"])

# WRONG: Not specifying allowed algorithms (algorithm confusion attack)
payload = jwt.decode(token, public_key)  # No algorithms specified!

# CORRECT: Always specify allowed algorithms explicitly
payload = jwt.decode(token, public_key, algorithms=["RS256"])
```

## Gotchas
- JWTs are signed, not encrypted — don't put secrets in payload
- Always verify the `exp` claim
- Use HS256 for single service, RS256 for microservices
- Store JWT in httpOnly cookie (not localStorage) for web apps
- JWTs can't be revoked — use short expiration + refresh tokens
- `verify()` throws on expired/invalid tokens

## Real-World Example

### Multi-Language JWT Auth: Python Issuer → TypeScript Verifier

```python
# Python: Token issuer (FastAPI)
import jwt
from datetime import datetime, timedelta, timezone

SECRET = "your-256-bit-secret"
ALGORITHM = "HS256"

def create_token(user_id: int, roles: list[str]) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "roles": roles,
        "iat": now,
        "exp": now + timedelta(hours=1),
        "iss": "myapp",
    }
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    return jwt.decode(
        token,
        SECRET,
        algorithms=[ALGORITHM],
        issuer="myapp",
        options={"require": ["exp", "iss", "sub"]},
    )
```

```typescript
// TypeScript: Token verifier (Express middleware)
import jwt from "jsonwebtoken";

const SECRET = "your-256-bit-secret";

interface TokenPayload {
  sub: string;
  roles: string[];
  iat: number;
  exp: number;
  iss: string;
}

export function authMiddleware(req: Request, res: Response, next: NextFunction) {
  const header = req.headers.authorization;
  if (!header?.startsWith("Bearer ")) {
    return res.status(401).json({ error: "Missing token" });
  }
  try {
    const payload = jwt.verify(header.slice(7), SECRET, {
      algorithms: ["HS256"],
      issuer: "myapp",
    }) as TokenPayload;
    req.user = { id: parseInt(payload.sub), roles: payload.roles };
    next();
  } catch (err) {
    if (err instanceof jwt.TokenExpiredError) {
      return res.status(401).json({ error: "Token expired" });
    }
    return res.status(401).json({ error: "Invalid token" });
  }
}
```

## Related
- crypto/password-hashing.md
- python/web/fastapi/auth-jwt.md
- java/spring/spring-security/jwt-auth.md
