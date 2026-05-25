---
id: "python-db-sqlalchemy-2.0-relationships"
title: "SQLAlchemy 2.0 Relationships"
language: "python"
category: "db"
subcategory: "orm"
tags: ["sqlalchemy", "relationship", "foreign-key", "one-to-many", "many-to-many"]
version: "3.10+"
retrieval_hint: "SQLAlchemy relationship foreign key one-to-many many-to-many join"
last_verified: "2026-05-24"
confidence: "high"
---

# SQLAlchemy 2.0 Relationships

## When to Use
- Defining foreign key relationships between tables
- One-to-many, many-to-many, one-to-one relationships
- Eager vs lazy loading strategies
- Cascade delete behavior

## Standard Pattern

```python
from sqlalchemy import ForeignKey, Table, Column, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# One-to-Many: User has many Posts
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    posts: Mapped[list["Post"]] = relationship(
        back_populates="author",
        cascade="all, delete-orphan",  # Delete posts when user is deleted
        lazy="selectin",  # Eager load with separate query
    )


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    author: Mapped["User"] = relationship(back_populates="posts")


# Many-to-Many: Students <-> Courses
student_course_table = Table(
    "student_courses",
    Base.metadata,
    Column("student_id", Integer, ForeignKey("students.id"), primary_key=True),
    Column("course_id", Integer, ForeignKey("courses.id"), primary_key=True),
)


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    courses: Mapped[list["Course"]] = relationship(
        secondary=student_course_table,
        back_populates="students",
    )


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    students: Mapped[list["Student"]] = relationship(
        secondary=student_course_table,
        back_populates="courses",
    )


# One-to-One: User has one Profile
class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    bio: Mapped[str | None]
    user: Mapped["User"] = relationship(back_populates="profile")


# Add to User model:
# profile: Mapped["Profile"] = relationship(back_populates="user", uselist=False)
```

## Common Mistakes

```python
# WRONG: Missing back_populates
class User(Base):
    posts: Mapped[list["Post"]] = relationship()  # One-sided only

# CORRECT: Always use back_populates for bidirectional
class User(Base):
    posts: Mapped[list["Post"]] = relationship(back_populates="author")

# WRONG: No cascade on parent deletion
class User(Base):
    posts: Mapped[list["Post"]] = relationship(back_populates="author")
    # Deleting user leaves orphaned posts!

# CORRECT: Add cascade for cleanup
class User(Base):
    posts: Mapped[list["Post"]] = relationship(
        back_populates="author",
        cascade="all, delete-orphan",
    )

# WRONG: N+1 query problem
users = session.scalars(select(User)).all()
for user in users:
    print(user.posts)  # Separate query for each user!

# CORRECT: Use eager loading
users = session.scalars(
    select(User).options(selectinload(User.posts))
).all()
```

## Gotchas
- `cascade="all, delete-orphan"` deletes children when parent is removed
- `lazy="selectin"` eager loads with a separate SELECT (recommended for most cases)
- `lazy="joined"` eager loads with JOIN (can be slower for complex graphs)
- `uselist=False` makes a one-to-one relationship
- `secondary=` defines the association table for many-to-many
- Use `ForeignKey("table.column")` with string for forward references
- `ondelete="CASCADE"` is database-level; `cascade=` is ORM-level

## Related
- python/db/sqlalchemy-2.0/models.md
- python/db/sqlalchemy-2.0/queries.md
