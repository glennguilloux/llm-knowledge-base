---
id: "python-db-sqlmodel-patterns"
title: "SQLModel Patterns for FastAPI and SQLAlchemy"
language: "python"
category: "db"
subcategory: "orm"
tags: ["sqlmodel", "fastapi", "sqlalchemy", "orm", "pydantic", "async", "crud"]
version: "3.10+"
retrieval_hint: "SQLModel FastAPI ORM CRUD session dependency injection async migration"
last_verified: "2026-05-25"
confidence: "high"
---

# SQLModel Patterns for FastAPI and SQLAlchemy

## When to Use
- Building FastAPI applications with a single-model approach (no separate Pydantic + SQLAlchemy)
- Projects that want Pydantic validation + SQLAlchemy power without maintaining two schemas
- Rapid prototyping where model definitions should drive both DB schema and API validation
- Simple to moderate CRUD APIs that don't need the raw power of SQLAlchemy directly

## Standard Pattern

```python
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Field, Session, SQLModel, create_engine, select, Relationship
from typing import Annotated

# --- Models ---
class HeroBase(SQLModel):
    name: str = Field(index=True)
    secret_name: str
    age: Optional[int] = Field(default=None, index=True)

class Hero(HeroBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: Optional[int] = Field(default=None, foreign_key="team.id")
    team: Optional["Team"] = Relationship(back_populates="heroes")

class HeroCreate(HeroBase):
    pass

class HeroPublic(HeroBase):
    id: int

class TeamBase(SQLModel):
    name: str = Field(index=True, unique=True)

class Team(TeamBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    heroes: list[Hero] = Relationship(back_populates="team")

class TeamPublic(TeamBase):
    id: int
    heroes: list[HeroPublic] = []

# --- Database ---
DATABASE_URL = "postgresql+psycopg://user:pass@localhost/db"
engine = create_engine(DATABASE_URL, echo=True)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

# --- FastAPI App ---
app = FastAPI()

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

@app.post("/heroes/", response_model=HeroPublic)
def create_hero(hero: HeroCreate, session: SessionDep):
    db_hero = Hero.model_validate(hero)
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero

@app.get("/heroes/{hero_id}", response_model=HeroPublic)
def get_hero(hero_id: int, session: SessionDep):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero

@app.get("/heroes/", response_model=list[HeroPublic])
def list_heroes(session: SessionDep, offset: int = 0, limit: int = 100):
    heroes = session.exec(select(Hero).offset(offset).limit(limit)).all()
    return heroes

# Query with JOIN
@app.get("/teams/{team_id}/heroes", response_model=list[HeroPublic])
def get_team_heroes(team_id: int, session: SessionDep):
    statement = select(Hero).where(Hero.team_id == team_id)
    return session.exec(statement).all()
```

## Common Mistakes

```python
# WRONG: Using separate Pydantic models for input/output alongside SQLModel table models
# This defeats the purpose — you're maintaining two schemas
from pydantic import BaseModel

class HeroIn(BaseModel):
    name: str
    age: int | None = None

class HeroDB(HeroIn):
    id: int

# Now you have to maintain HeroIn AND HeroSQLModel separately

# CORRECT: Use SQLModel's inheritance to define shared fields once
class HeroBase(SQLModel):
    name: str
    age: int | None = None

class HeroCreate(HeroBase):
    pass

class Hero(HeroBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

# WRONG: Forgetting session.refresh() after commit — the returned object has no ID
@app.post("/heroes/")
def create_hero(hero: HeroCreate, session: SessionDep):
    db_hero = Hero.model_validate(hero)
    session.add(db_hero)
    session.commit()
    return db_hero  # db_hero.id is None!

# CORRECT: Always refresh after commit to get DB-generated values
@app.post("/heroes/")
def create_hero(hero: HeroCreate, session: SessionDep):
    db_hero = Hero.model_validate(hero)
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero  # db_hero.id is now populated

# WRONG: Using SQLAlchemy-style async session with SQLModel table models
# SQLModel doesn't natively support async — you need a separate setup
from sqlalchemy.ext.asyncio import AsyncSession

# CORRECT: Use SQLAlchemy's async support directly when needed,
# or use sqlmodel's sync session which is the primary supported path
# For async, you need the sqlmodel-extras package or raw SQLAlchemy async
```

## Gotchas
- **`table=True` vs no `table=True`:** A class with `table=True` becomes a database table (SQLAlchemy model). One without is a Pydantic-only schema. You can use the same base class for both, but the `table=True` subclass is the actual DB model.
- **`model_validate()` vs `model_dump()`:** SQLModel uses Pydantic v2 methods. Use `Hero.model_validate(hero_create)` to create a DB model from a create schema. Use `hero.model_dump()` to serialize back. Don't use the old `from_orm()` or `dict()`.
- **Relationship loading:** By default, SQLModel relationships are lazy-loaded. In FastAPI, if you access a relationship outside the session (after the response), you'll get an `AttributeError`. Use `selectinload()` or `joinedload()` for eager loading, or use `response_model` to control serialization.
- **Alembic migration generation:** SQLModel's `SQLModel.metadata` is a combined metadata from SQLAlchemy. When using Alembic, set `target_metadata = SQLModel.metadata` (not `Base.metadata`). Also, SQLModel doesn't yet auto-detect all relationship changes in autogenerate.
- **Type annotations on relationships:** Always annotate the reverse side (`team: Optional["Team"] = Relationship(...)`) with `Optional` and quotes for forward references. Without this, mypy and Pydantic may fail validation.

## Related
- python/db/sqlalchemy-2.0/async-sessions.md
- python/web/fastapi/dependency-injection.md
- python/data/pydantic-v2/models.md
- python/db/sqlalchemy-2.0/alembic-advanced.md
