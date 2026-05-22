---
id: "python-db-sqlalchemy-2.0-queries"
title: "SQLAlchemy 2.0 CRUD Queries"
language: "python"
category: "db"
subcategory: "orm"
tags: ["sqlalchemy", "query", "crud", "select", "insert", "update", "delete"]
version: "3.10+"
retrieval_hint: "SQLAlchemy query CRUD select insert update delete filter"
last_verified: "2026-05-22"
confidence: "high"
---

# SQLAlchemy 2.0 CRUD Queries

## When to Use
- Creating, reading, updating, and deleting records
- Filtering and sorting query results
- Pagination
- Aggregation queries

## Standard Pattern

```python
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import Session

# CREATE
def create_user(session: Session, name: str, email: str) -> User:
    user = User(name=name, email=email)
    session.add(user)
    session.commit()
    session.refresh(user)  # Refresh to get generated fields (id, created_at)
    return user


# READ - Single record
def get_user_by_id(session: Session, user_id: int) -> User | None:
    return session.get(User, user_id)  # SQLAlchemy 2.0 style

def get_user_by_email(session: Session, email: str) -> User | None:
    stmt = select(User).where(User.email == email)
    return session.scalars(stmt).first()


# READ - Multiple records
def list_users(
    session: Session,
    skip: int = 0,
    limit: int = 10,
    is_active: bool | None = None,
) -> list[User]:
    stmt = select(User)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
    stmt = stmt.offset(skip).limit(limit).order_by(User.created_at.desc())
    return list(session.scalars(stmt).all())


# UPDATE
def update_user(session: Session, user_id: int, **kwargs) -> User | None:
    user = session.get(User, user_id)
    if not user:
        return None
    for key, value in kwargs.items():
        setattr(user, key, value)
    session.commit()
    session.refresh(user)
    return user


# Bulk update
def deactivate_all_users(session: Session) -> int:
    stmt = update(User).where(User.is_active == True).values(is_active=False)
    result = session.execute(stmt)
    session.commit()
    return result.rowcount


# DELETE
def delete_user(session: Session, user_id: int) -> bool:
    user = session.get(User, user_id)
    if not user:
        return False
    session.delete(user)
    session.commit()
    return True


# Aggregation
def count_users(session: Session) -> int:
    return session.scalar(select(func.count(User.id)))


def user_count_by_status(session: Session) -> dict:
    stmt = select(User.is_active, func.count(User.id)).group_by(User.is_active)
    return {row[0]: row[1] for row in session.execute(stmt)}
```

## Common Mistakes

```python
# WRONG: Forgetting to commit
def create_user(session: Session, name: str) -> User:
    user = User(name=name)
    session.add(user)
    # Missing session.commit()! Data never saved.

# CORRECT: Always commit after modifications
def create_user(session: Session, name: str) -> User:
    user = User(name=name)
    session.add(user)
    session.commit()
    return user

# WRONG: Using session.execute() for single object
user = session.execute(select(User).where(User.id == 1)).scalar_one()

# CORRECT: Use session.get() for primary key lookup
user = session.get(User, 1)

# WRONG: Not handling None from first()
user = session.scalars(select(User).where(User.id == 999)).first()
print(user.name)  # AttributeError if None!

# CORRECT: Check for None
user = session.scalars(select(User).where(User.id == 999)).first()
if user:
    print(user.name)
```

## Gotchas
- `session.get(Model, id)` returns `None` if not found (no exception)
- `session.scalars(stmt).first()` returns `None` if no results
- `session.scalars(stmt).all()` returns a list
- Always `commit()` after `add()`, `delete()`, or attribute changes
- Use `session.refresh(obj)` to get database-generated values (id, timestamps)
- Bulk updates bypass the ORM (no Python-side defaults or events)
- Use `session.rollback()` to undo uncommitted changes

## Related
- python/db/sqlalchemy-2.0/models.md
- python/db/sqlalchemy-2.0/relationships.md
