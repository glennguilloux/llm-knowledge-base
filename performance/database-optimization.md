---
id: "performance-database-optimization"
title: "Database Query Optimization"
language: "multi"
category: "performance"
tags: ["database", "performance", "indexing", "n-plus-1", "query-optimization", "explain", "connection-pooling"]
version: "n/a"
retrieval_hint: "database query optimization indexing N+1 problem EXPLAIN plan connection pooling performance slow queries"
last_verified: "2026-05-24"
confidence: "high"
---

# Database Query Optimization

## When to Use
- Debugging slow database queries
- Designing indexes for read-heavy workloads
- Fixing N+1 query problems in ORM code
- Setting up connection pooling for production

## Standard Pattern

```sql
-- === Indexing Strategy ===

-- CORRECT: Index columns used in WHERE, JOIN, ORDER BY
CREATE INDEX idx_users_email ON users (email);                    -- Equality lookup
CREATE INDEX idx_orders_user_date ON orders (user_id, created_at); -- Composite for common query

-- CORRECT: Partial index for common filter patterns
CREATE INDEX idx_active_users ON users (email) WHERE active = true;

-- CORRECT: Covering index (includes all needed columns)
CREATE INDEX idx_orders_covering ON orders (user_id, created_at) INCLUDE (total_amount, status);

-- CORRECT: Check if your index is being used
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';
-- Look for "Index Scan" (good) vs "Seq Scan" (bad on large tables)
```

```python
# === Python: SQLAlchemy N+1 Prevention ===

from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import select

# WRONG: N+1 queries — loads posts, then one query per post for comments
posts = session.execute(select(Post)).scalars().all()
for post in posts:
    print(len(post.comments))  # One additional query per post!

# CORRECT: joinedload — single query with JOIN
posts = session.execute(
    select(Post).options(joinedload(Post.comments))
).scalars().unique().all()

# CORRECT: selectinload — separate query with IN (better for many-to-many)
posts = session.execute(
    select(Post).options(selectinload(Post.comments))
).scalars().all()

# CORRECT: subqueryload — for complex nested relationships
posts = session.execute(
    select(Post).options(
        selectinload(Post.comments).selectinload(Comment.author)
    )
).scalars().all()
```

```python
# === Django ORM: N+1 Prevention ===

from django.db.models import Prefetch

# WRONG: N+1 in template
authors = Author.objects.all()
for author in authors:
    print(author.book_set.count())  # One query per author!

# CORRECT: select_related (ForeignKey, OneToOne — uses JOIN)
book = Book.objects.select_related("author").get(id=1)
print(book.author.name)  # No extra query

# CORRECT: prefetch_related (ManyToMany, reverse ForeignKey — uses IN)
authors = Author.objects.prefetch_related("books").all()
for author in authors:
    print(len(author.books.all()))  # No extra queries

# CORRECT: Prefetch with custom queryset
authors = Author.objects.prefetch_related(
    Prefetch("books", queryset=Book.objects.filter(published=True))
).all()
```

```java
// === Java: JPA/Hibernate N+1 Prevention ===

import org.hibernate.annotations.FetchMode;
import org.hibernate.annotations.Fetch;

// CORRECT: Entity graph for fetch planning
@Entity
@NamedEntityGraph(
    name = "Post.withComments",
    attributeNodes = @NamedAttributeNode("comments")
)
public class Post { ... }

// Usage
@EntityGraph(value = "Post.withComments")
List<Post> findAll();

// CORRECT: JPQL JOIN FETCH
@Query("SELECT p FROM Post p JOIN FETCH p.comments WHERE p.id = :id")
Post findByIdWithComments(@Param("id") Long id);

// CORRECT: Batch fetching (reduces N+1 to N/batch queries)
@OneToMany(mappedBy = "post", fetch = FetchType.LAZY)
@BatchSize(size = 50)  // Loads 50 at a time
private List<Comment> comments;
```

```python
# === Connection Pooling ===

# CORRECT: SQLAlchemy connection pool
from sqlalchemy import create_engine

engine = create_engine(
    DATABASE_URL,
    pool_size=10,           # 10 persistent connections
    max_overflow=20,        # Allow 20 additional when pool is busy
    pool_timeout=30,        # Wait 30s for a connection
    pool_recycle=3600,      # Recycle connections after 1 hour
    pool_pre_ping=True,     # Check connection health before use
)

# CORRECT: Async connection pool
from sqlalchemy.ext.asyncio import create_async_engine

async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_size=20,
    max_overflow=10,
)
```

## Common Mistakes

```sql
-- WRONG: Indexing every column (write penalty)
CREATE INDEX idx_everything ON users (id, name, email, created_at, updated_at);
-- This single composite index is rarely useful and slows all INSERTs/UPDATEs

-- CORRECT: Index for specific query patterns
CREATE INDEX idx_users_email ON users (email);           -- Login lookup
CREATE INDEX idx_users_created ON users (created_at);    -- Admin dashboard sort
```

```python
# WRONG: Using .all() then filtering in Python
users = session.query(User).all()
active = [u for u in users if u.active]  # Loading ALL users into memory

# CORRECT: Filter at the database level
active = session.query(User).filter(User.active == True).all()
```

```python
# WRONG: Counting with len(query.all())
count = len(session.query(Order).all())  # Loads all orders just to count

# CORRECT: Use COUNT at database level
from sqlalchemy import func
count = session.query(func.count(Order.id)).scalar()
```

```sql
-- WRONG: SELECT * when you only need specific columns
SELECT * FROM orders WHERE user_id = 123;

-- CORRECT: Select only needed columns
SELECT id, status, total_amount FROM orders WHERE user_id = 123;
```

## Gotchas
- `EXPLAIN ANALYZE` actually runs the query — don't use on write queries in production
- Composite index column order matters: `(user_id, created_at)` supports `WHERE user_id = ?` but NOT `WHERE created_at = ?`
- ORM `lazy="dynamic"` or lazy loading creates N+1 by default — always use eager loading in loops
- Connection pooling with `pool_size=10` means 10 connections PER engine instance — watch total across workers
- `pool_pre_ping=True` prevents "connection already closed" errors after idle periods
- `select_related` uses JOIN (single query, more data per row), `prefetch_related` uses IN (two queries, less duplication)
- Partial indexes (`WHERE` clause) are smaller and faster — use when you frequently filter on a subset
- `SELECT *` prevents covering index optimization — always select specific columns for hot queries
- ORM `.count()` and `.len(query.all())` are fundamentally different — one is O(1) on DB, the other loads everything

## Related
- performance/n-plus-one-prevention.md
- performance/caching-strategies.md
- performance/connection-pooling.md
- db/postgres/json-queries.md
