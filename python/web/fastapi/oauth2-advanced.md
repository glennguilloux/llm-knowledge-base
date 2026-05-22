---
id: "python-web-fastapi-oauth2-advanced"
title: "FastAPI OAuth2 Scopes and Token Refresh"
language: "python"
category: "web"
subcategory: "auth"
tags: ["fastapi", "oauth2", "scopes", "refresh", "token", "security"]
version: "3.10+"
retrieval_hint: "FastAPI OAuth2 scopes refresh token rotation fine-grained permissions"
last_verified: "2026-05-22"
confidence: "high"
---

# FastAPI OAuth2 Scopes and Token Refresh

## When to Use
- APIs needing fine-grained permissions (read, write, admin scopes)
- Implementing token refresh without re-authentication
- Third-party API integrations requiring scope-based access
- Mobile/SPA apps where short-lived access tokens + refresh tokens improve security

## Standard Pattern

```python
from fastapi import FastAPI, Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError, jwt
from pydantic import BaseModel
from datetime import datetime, timedelta

app = FastAPI()

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE = 15  # minutes
REFRESH_TOKEN_EXPIRE = 7 * 24 * 60  # 7 days

# --- Scopes definition ---
SCOPES = {
    "read": "Read access to resources",
    "write": "Write access to resources",
    "admin": "Administrative access",
}

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/token",
    scopes=SCOPES,
)


# --- Token models ---
class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


# --- Token creation ---
def create_token(data: dict, expires_delta: timedelta, token_type: str = "access") -> str:
    to_encode = data.copy()
    to_encode.update({
        "exp": datetime.utcnow() + expires_delta,
        "type": token_type,
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_token_pair(user: dict, scopes: list[str]) -> TokenPair:
    token_data = {"sub": user["username"], "scopes": scopes}
    return TokenPair(
        access_token=create_token(token_data, timedelta(minutes=ACCESS_TOKEN_EXPIRE), "access"),
        refresh_token=create_token(token_data, timedelta(minutes=REFRESH_TOKEN_EXPIRE), "refresh"),
        expires_in=ACCESS_TOKEN_EXPIRE * 60,
    )


# --- Dependency with scope checking ---
async def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": f'Bearer scope="{security_scopes.scope_str}"'},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_scopes: list[str] = payload.get("scopes", [])
        token_type: str = payload.get("type", "access")
        if username is None or token_type != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Check required scopes
    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {scope}",
            )
    return {"username": username, "scopes": token_scopes}


# --- Routes ---
@app.post("/auth/token", response_model=TokenPair)
async def login(username: str, password: str, scopes: str = ""):
    user = authenticate_user(username, password)
    requested_scopes = scopes.split() if scopes else ["read"]
    return create_token_pair(user, requested_scopes)


@app.post("/auth/refresh", response_model=TokenPair)
async def refresh_token(refresh_token: str):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = get_user(payload["sub"])
        return create_token_pair(user, payload.get("scopes", ["read"]))
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@app.get("/items")
async def list_items(user: dict = Security(get_current_user, scopes=["read"])):
    return [{"id": 1, "name": "Item"}]


@app.post("/items")
async def create_item(item: dict, user: dict = Security(get_current_user, scopes=["write"])):
    return {"id": 2, **item}


@app.delete("/items/{item_id}")
async def delete_item(item_id: int, user: dict = Security(get_current_user, scopes=["admin"])):
    return {"deleted": item_id}
```

## Common Mistakes

```python
# WRONG: Same secret for access and refresh tokens
access_token = create_token(data, timedelta(minutes=15))
refresh_token = create_token(data, timedelta(days=7))
# Both decode with same logic — can't distinguish token types

# CORRECT: Include token type in payload
access_token = create_token({**data, "type": "access"}, timedelta(minutes=15))
refresh_token = create_token({**data, "type": "refresh"}, timedelta(days=7))

# WRONG: Not validating token type on refresh
payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
# Could be an access token used as refresh!

# CORRECT: Check token type
if payload.get("type") != "refresh":
    raise HTTPException(status_code=401, detail="Invalid token type")

# WRONG: Long-lived access tokens
access_token = create_token(data, timedelta(days=30))  # Too long!

# CORRECT: Short access + long refresh
access_token = create_token(data, timedelta(minutes=15))
refresh_token = create_token(data, timedelta(days=7))
```

## Gotchas
- `Security()` with `scopes` parameter is like `Depends()` but adds scope requirements to docs
- Scopes are checked in the dependency, not automatically — you must verify them manually
- `WWW-Authenticate` header must include the scope string for OAuth2 compliance
- Refresh tokens should be stored securely (HttpOnly cookie or secure storage)
- Token rotation: issue a new refresh token with each refresh (invalidate old one)
- Store refresh tokens in a database for revocation capability
- Access tokens are stateless (just JWT); refresh tokens need server-side state for revocation
- Default scopes in `OAuth2PasswordBearer` apply when no scopes are requested

## Related
- python/web/fastapi/oauth2-password.md
- python/web/fastapi/auth-jwt.md
- python/web/fastapi/dependency-injection.md
