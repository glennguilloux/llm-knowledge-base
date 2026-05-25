---
id: "python-web-fastapi-auth-jwt"
title: "JWT Authentication with FastAPI"
language: "python"
category: "web"
subcategory: "authentication"
tags: ["fastapi", "jwt", "authentication", "oauth2", "bearer", "security"]
version: "3.10+"
retrieval_hint: "JWT authentication FastAPI OAuth2 bearer token login"
last_verified: "2026-05-24"
confidence: "high"
---

# JWT Authentication with FastAPI

## When to Use
- Stateless API authentication
- Token-based auth for SPAs and mobile apps
- Microservice-to-microservice auth
- OAuth2 bearer token flows

## Standard Pattern

```python
from datetime import datetime, timedelta, timezone
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Configuration
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: str
    disabled: bool = False


# Fake user database
fake_users_db = {
    "alice": {
        "username": "alice",
        "email": "alice@example.com",
        "hashed_password": pwd_context.hash("secret"),
    }
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user_data = fake_users_db.get(username)
    if user_data is None:
        raise credentials_exception
    return User(**user_data)


@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    user_data = fake_users_db.get(form_data.username)
    if not user_data or not verify_password(form_data.password, user_data["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token = create_access_token(
        data={"sub": user_data["username"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(access_token=access_token, token_type="bearer")


@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
```

## Common Mistakes

```python
# WRONG: Hardcoded secret in production
SECRET_KEY = "my-secret"  # Never commit this!

# CORRECT: Use environment variable
SECRET_KEY = os.environ["JWT_SECRET_KEY"]

# WRONG: No expiration on tokens
token = jwt.encode({"sub": username}, SECRET_KEY, algorithm=ALGORITHM)  # Lives forever!

# CORRECT: Set expiration
expire = datetime.now(timezone.utc) + timedelta(minutes=30)
token = jwt.encode({"sub": username, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

# WRONG: Not verifying token expiration
payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})

# CORRECT: Always verify expiration (default behavior)
payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
```

## Gotchas
- `SECRET_KEY` must be kept secret — use environment variables
- Use `HS256` for symmetric key, `RS256` for asymmetric (microservices)
- Token expiration should be short (15-30 minutes); use refresh tokens for longer sessions
- `jwt.decode()` raises `ExpiredSignatureError` for expired tokens
- Use `Depends(get_current_user)` to protect endpoints
- `OAuth2PasswordBearer` sends token in `Authorization: Bearer <token>` header
- Always hash passwords with bcrypt/argon2, never store plain text

## Real-World Example

### Complete Auth Flow: Register → Login → Protected Endpoint

```python
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pydantic import BaseModel

app = FastAPI()
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Simulated database
fake_users_db: dict[str, dict] = {}


class UserCreate(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
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
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise credentials_exception
    user = fake_users_db.get(username)
    if user is None:
        raise credentials_exception
    return user


@app.post("/register", status_code=201)
async def register(user: UserCreate):
    if user.username in fake_users_db:
        raise HTTPException(status_code=400, detail="Username already exists")
    fake_users_db[user.username] = {
        "username": user.username,
        "hashed_password": hash_password(user.password),
    }
    return {"message": "User created"}


@app.post("/token", response_model=Token)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = fake_users_db.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = create_access_token(data={"sub": user["username"]})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/me")
async def read_users_me(current_user: Annotated[dict, Depends(get_current_user)]):
    return {"username": current_user["username"]}
```

## Related
- crypto/password-hashing.md
- crypto/jwt-tokens.md
- python/web/fastapi/error-handling.md
