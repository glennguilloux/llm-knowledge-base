---
id: "python-web-fastapi-oauth2-password"
title: "FastAPI OAuth2 Password Flow"
language: "python"
category: "web"
subcategory: "auth"
tags: ["fastapi", "oauth2", "password", "bearer", "login", "security"]
version: "3.10+"
retrieval_hint: "FastAPI OAuth2 password bearer token login form authentication"
last_verified: "2026-05-24"
confidence: "high"
---

# FastAPI OAuth2 Password Flow

## When to Use
- Traditional username/password login forms (not social auth)
- Migrating from session-based auth to token-based auth
- APIs that need a `/login` endpoint accepting form data (not JSON)
- Internal tools where OAuth2 Authorization Code flow is overkill

## Standard Pattern

```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel
from datetime import datetime, timedelta

app = FastAPI()

# --- Configuration ---
SECRET_KEY = "your-secret-key"  # Use env var in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- Password hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- OAuth2 scheme (points to token URL) ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


# --- Models ---
class Token(BaseModel):
    access_token: str
    token_type: str


class UserInDB(BaseModel):
    id: int
    username: str
    hashed_password: str
    is_active: bool = True


# --- Simulated user store ---
fake_users_db = {
    "alice": {"id": 1, "username": "alice", "hashed_password": pwd_context.hash("secret123")},
}


# --- Helper functions ---
def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# --- Dependencies ---
async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = fake_users_db.get(username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(user: dict = Depends(get_current_user)) -> dict:
    if not user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


# --- Routes ---
@app.post("/auth/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users_db.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me")
async def read_current_me(user: dict = Depends(get_current_active_user)):
    return {"id": user["id"], "username": user["username"]}
```

## Common Mistakes

```python
# WRONG: Storing passwords in plain text
user = {"username": "alice", "password": "secret123"}  # Never do this

# CORRECT: Always hash passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
user = {"username": "alice", "hashed_password": pwd_context.hash("secret123")}

# WRONG: Using a weak or hardcoded secret key
SECRET_KEY = "mysecret"  # Easily guessable

# CORRECT: Use a strong random key from environment
import os
SECRET_KEY = os.environ["JWT_SECRET_KEY"]  # 256-bit random key

# WRONG: Token with no expiration
token = jwt.encode({"sub": username}, SECRET_KEY, algorithm=ALGORITHM)  # Lives forever

# CORRECT: Always set expiration
expire = datetime.utcnow() + timedelta(minutes=30)
token = jwt.encode({"sub": username, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

# WRONG: Accepting JSON for OAuth2 token endpoint
@app.post("/auth/token")
async def login(data: dict):  # Not OAuth2 compliant

# CORRECT: Use OAuth2PasswordRequestForm (accepts form data)
@app.post("/auth/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # form_data.username, form_data.password
```

## Gotchas
- `OAuth2PasswordRequestForm` expects form-encoded data (`application/x-www-form-urlencoded`), not JSON
- The `tokenUrl` parameter in `OAuth2PasswordBearer` only affects docs — it doesn't create the endpoint
- `bcrypt` has a 72-byte password limit; longer passwords are silently truncated
- JWT tokens are signed, not encrypted — don't put sensitive data in the payload
- `WWW-Authenticate: Bearer` header is required by the OAuth2 spec for 401 responses
- `OAuth2PasswordBearer` returns the token string directly; `OAuth2PasswordRequestForm` parses the form
- For refresh tokens, implement a separate `/auth/refresh` endpoint with longer expiry

## Related
- python/web/fastapi/auth-jwt.md
- python/web/fastapi/dependency-injection.md
- patterns/authentication-patterns.md
