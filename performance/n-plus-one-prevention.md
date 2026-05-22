---
id: "performance-n-plus-one-prevention"
title: "N+1 Query Prevention"
language: "multi"
category: "performance"
tags: ["n-plus-one", "query", "optimization", "eager-loading", "batching", "JOIN"]
version: "n/a"
retrieval_hint: "N+1 query optimization eager loading batching JOIN dataloader performance"
last_verified: "2026-05-22"
confidence: "high"
---

# N+1 Query Prevention

## When to Use
- Fetching related data (users with their posts, orders with items)
- Loading nested associations in ORMs
- Building efficient database queries for list views
- Optimizing API response times

## Standard Pattern

```python
# --- SQLAlchemy: Eager loading ---
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import select

# Eager load relationships in a single query
async def get_users_with_posts(session):
    stmt = select(User).options(selectinload(User.posts))
    result = await session.execute(stmt)
    return result.scalars().all()

# JOIN for one-to-one relationships
async def get_users_with_profile(session):
    stmt = select(User).options(joinedload(User.profile))
    result = await session.execute(stmt)
    return result.scalars().all()

# --- Prisma: include ---
# const users = await prisma.user.findMany({
#   include: { posts: true },
# });

# --- DataLoader pattern (batching) ---
from collections import defaultdict

class DataLoader:
    def __init__(self, batch_fn):
        self._batch_fn = batch_fn
        self._cache = {}
        self._pending = []

    async def load(self, key):
        if key in self._cache:
            return self._cache[key]
        self._pending.append(key)
        # In real implementation, defer to next tick
        return await self._batch_fn([key])

    async def load_many(self, keys):
        return [await self.load(k) for k in keys]

# --- Django ORM: prefetch_related / select_related ---
# users = User.objects.prefetch_related('posts').all()  # 2 queries
# users = User.objects.select_related('profile').all()  # 1 query with JOIN
```

## Common Mistakes

```python
# WRONG: N+1 query (1 query for list + N queries for relations)
users = await session.execute(select(User))
for user in users.scalars():
    posts = await session.execute(
        select(Post).where(Post.user_id == user.id)  # N queries!
    )
    user.posts = posts.scalars().all()

# CORRECT: Eager load
stmt = select(User).options(selectinload(User.posts))
users = await session.execute(stmt)

# WRONG: Lazy loading in a loop
for user in users:
    print(user.posts)  # Triggers a query per user!

# CORRECT: Eager load or batch
users = session.query(User).options(selectinload(User.posts)).all()
for user in users:
    print(user.posts)  # Already loaded

# WRONG: Using JOIN for collection relationships (Cartesian product)
stmt = select(User).join(User.posts)  # Returns duplicate users!

# CORRECT: Use selectinload for collections, joinedload for single
stmt = select(User).options(selectinload(User.posts))  # 2 queries, no duplicates
```

## Gotchas
- `selectinload` fires a separate `IN` query — better for collections
- `joinedload` uses SQL JOIN — better for one-to-one/many-to-one
- N+1 queries are the #1 performance issue in ORM-heavy applications
- Use `EXPLAIN ANALYZE` to detect N+1 patterns in slow queries
- DataLoader batches requests within a single request lifecycle — prevents N+1 in GraphQL
- `prefetch_related` (Django) is like `selectinload`; `select_related` is like `joinedload`

## Related
- db/postgres/indexes.md
- db/postgres/query-optimization.md
- patterns/api-design.md
