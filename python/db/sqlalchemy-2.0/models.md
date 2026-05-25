---
id: "python-db-sqlalchemy-2.0-models"
title: "SQLAlchemy 2.0 Declarative Models"
language: "python"
category: "db"
subcategory: "orm"
tags: ["sqlalchemy", "orm", "model", "declarative", "database", "table"]
version: "3.10+"
retrieval_hint: "SQLAlchemy ORM model declarative table column relationship"
last_verified: "2026-05-24"
confidence: "high"
---

# SQLAlchemy 2.0 Declarative Models

## When to Use
- Defining database tables as Python classes
- ORM-based data access
- Type-safe database operations
- Schema migrations with Alembic

## Standard Pattern

```python
from datetime import datetime
from sqlalchemy import create_engine, String, ForeignKey, func
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    Session,
)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    posts: Mapped[list["Post"]] = relationship(back_populates="author")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, name={self.name!r})>"


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str]
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    author: Mapped["User"] = relationship(back_populates="posts")


# Engine and session
engine = create_engine("postgresql://user:pass@localhost/dbname", echo=True)

def get_session():
    with Session(engine) as session:
        yield session
```

## Common Mistakes

```python
# WRONG: Using old-style Column() syntax
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)  # SQLAlchemy 1.x style

# CORRECT: Use Mapped[] and mapped_column()
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)

# WRONG: Not using server_default for timestamps
created_at: Mapped[datetime] = mapped_column(default=func.now())  # Python-side only

# CORRECT: Use server_default for database-generated values
created_at: Mapped[datetime] = mapped_column(server_default=func.now())

# WRONG: Forgetting back_populates
class User(Base):
    posts: Mapped[list["Post"]] = relationship()  # One-sided relationship

# CORRECT: Use back_populates for bidirectional relationships
class User(Base):
    posts: Mapped[list["Post"]] = relationship(back_populates="author")
```

## Gotchas
- `Mapped[]` provides type hints for IDE autocompletion and type checking
- `server_default` runs in the database; `default` runs in Python
- Use `String(255)` not `Text` for indexed columns (database-specific limits)
- `relationship()` is lazy-loaded by default; use `selectin` or `joined` for eager loading
- `func.now()` is database-specific (use `func.now()` for PostgreSQL, `func.now()` for MySQL)
- Always define `__tablename__` on every model
- Use `mapped_column(unique=True)` for unique constraints

## Related
- python/db/sqlalchemy-2.0/queries.md
- python/db/sqlalchemy-2.0/relationships.md
- python/db/sqlalchemy-2.0/migrations-alembic.md
