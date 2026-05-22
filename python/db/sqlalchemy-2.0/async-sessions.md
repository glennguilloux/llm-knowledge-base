---
id: "python-db-sqlalchemy-async-sessions"
title: "SQLAlchemy 2.0 Async Session Patterns"
language: "python"
category: "db"
subcategory: "orm"
tags: ["sqlalchemy", "async", "session", "asyncpg", "database", "asyncio"]
version: "3.10+"
retrieval_hint: "SQLAlchemy async session asyncpg AsyncSession create_async_engine"
last_verified: "2026-05-22"
confidence: "high"
---

# SQLAlchemy 2.0 Async Session Patterns

## When to Use
- FastAPI or other async frameworks needing non-blocking database access
- High-concurrency applications where sync DB calls block the event loop
- Microservices handling many simultaneous requests
- Applications already using asyncio for other I/O (HTTP clients, WebSocket)

## Standard Pattern

```python
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, select, func
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager


# --- Setup ---
DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/dbname"

engine = create_async_engine(DATABASE_URL, echo=False, pool_size=20, max_overflow=10)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)


# --- FastAPI dependency ---
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# --- CRUD operations ---
async def create_user(db: AsyncSession, name: str, email: str) -> User:
    user = User(name=name, email=email)
    db.add(user)
    await db.flush()  # Get the ID without committing
    await db.refresh(user)  # Reload from DB (server defaults, triggers)
    return user


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def list_users(db: AsyncSession, skip: int = 0, limit: int = 20) -> list[User]:
    result = await db.execute(select(User).offset(skip).limit(limit))
    return list(result.scalars().all())


async def update_user(db: AsyncSession, user_id: int, **kwargs) -> User | None:
    user = await db.get(User, user_id)
    if not user:
        return None
    for key, value in kwargs.items():
        setattr(user, key, value)
    await db.flush()
    await db.refresh(user)
    return user


# --- Context manager for standalone scripts ---
async def standalone_example() -> None:
    async with async_session() as db:
        user = await create_user(db, "Alice", "alice@example.com")
        print(f"Created user: {user.id}")
        await db.commit()


# --- Bulk operations ---
async def bulk_insert(db: AsyncSession, users_data: list[dict]) -> None:
    db.add_all([User(**data) for data in users_data])
    await db.flush()
```

## Common Mistakes

```python
# WRONG: Using sync Session with async framework
from sqlalchemy.orm import Session

@app.get("/users")
async def list_users():
    with Session(engine) as db:  # Blocks the event loop!
        return db.query(User).all()

# CORRECT: Use AsyncSession
@app.get("/users")
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalars().all()

# WRONG: Forgetting await on session operations
async def create_user(db: AsyncSession):
    user = User(name="Alice")
    db.add(user)
    db.commit()  # This is the SYNC method — doesn't work with AsyncSession!

# CORRECT: Always await async operations
async def create_user(db: AsyncSession):
    user = User(name="Alice")
    db.add(user)
    await db.commit()

# WRONG: Using db.query() with AsyncSession
result = db.query(User).all()  # .query() is sync-only API

# CORRECT: Use select() and db.execute()
result = await db.execute(select(User))
users = result.scalars().all()

# WRONG: Running sync code inside async session context
async def get_user(db: AsyncSession):
    time.sleep(5)  # Blocks the event loop!
    return await db.get(User, 1)

# CORRECT: Use asyncio.sleep or run_in_executor
async def get_user(db: AsyncSession):
    await asyncio.sleep(5)  # Non-blocking
    return await db.get(User, 1)
```

## Gotchas
- Use `expire_on_commit=False` in the session maker to access attributes after commit without lazy-load issues
- `db.add()` is synchronous (no await needed); `db.commit()`, `db.flush()`, `db.execute()` need await
- `asyncpg` is significantly faster than `psycopg2` for async workloads
- `await db.get(Model, id)` is the async equivalent of `db.query(Model).get(id)`
- Use `selectinload()` or `joinedload()` in `select()` options for eager loading relationships
- Connection pooling is managed by the engine — don't create engines per request
- `AsyncSession` is NOT thread-safe — one session per request, never share across tasks

## Related
- python/db/sqlalchemy-2.0/models.md
- python/db/sqlalchemy-2.0/queries.md
- python/web/fastapi/dependency-injection.md
