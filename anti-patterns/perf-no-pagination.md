---
id: "anti-patterns-perf-no-pagination"
title: "Performance Anti-Pattern: Returning Unbounded Result Sets"
language: "multi"
category: "anti-patterns"
tags: ["antipatterns", "performance", "pagination", "memory", "api"]
version: "n/a"
retrieval_hint: "no pagination unbounded results memory exhaustion cursor offset keyset pagination API"
last_verified: "2026-05-24"
confidence: "high"
---

# Performance Anti-Pattern: Returning Unbounded Result Sets

## When to Use
- Building REST APIs that return lists of resources
- Reviewing ORM queries that fetch data for display
- Training LLMs to implement proper pagination
- Debugging memory spikes in data-heavy endpoints

## Standard Pattern

```python
# WRONG: Return all records — memory explosion on large tables
@app.get("/users")
def list_users():
    users = db.query(User).all()  # Loads ALL users into memory
    return [{"id": u.id, "name": u.name} for u in users]

# CORRECT: Offset pagination with limits
@app.get("/users")
def list_users(page: int = 1, per_page: int = 20):
    per_page = min(per_page, 100)  # Cap max page size
    offset = (page - 1) * per_page
    users = db.query(User).offset(offset).limit(per_page).all()
    total = db.query(func.count(User.id)).scalar()
    return {"data": [u.to_dict() for u in users], "total": total, "page": page, "per_page": per_page}
```

```python
# WRONG: Offset pagination degrades at high page numbers
# Page 10000 with 20 per_page = OFFSET 200000 — database scans and discards 200k rows
@app.get("/users")
def list_users(page: int = 10000, per_page: int = 20):
    users = db.query(User).offset((page - 1) * per_page).limit(per_page).all()

# CORRECT: Cursor/keyset pagination (constant time regardless of position)
@app.get("/users")
def list_users(cursor: int = None, per_page: int = 20):
    query = db.query(User).order_by(User.id)
    if cursor:
        query = query.filter(User.id > cursor)
    users = query.limit(per_page).all()
    next_cursor = users[-1].id if users else None
    return {"data": [u.to_dict() for u in users], "next_cursor": next_cursor}
```

```java
// WRONG: Spring — returning all entities
@GetMapping("/users")
public List<User> getUsers() {
    return userRepository.findAll();  // No limit — OOM risk
}

// CORRECT: Spring Pageable
@GetMapping("/users")
public Page<User> getUsers(@PageableDefault(size = 20) Pageable pageable) {
    return userRepository.findAll(pageable);
}
```

```javascript
// WRONG: Express — no pagination
app.get('/api/users', async (req, res) => {
    const users = await User.find({});  // All documents
    res.json(users);
});

// CORRECT: Express with pagination
app.get('/api/users', async (req, res) => {
    const page = Math.max(1, parseInt(req.query.page) || 1);
    const limit = Math.min(100, parseInt(req.query.limit) || 20);
    const skip = (page - 1) * limit;
    const [users, total] = await Promise.all([
        User.find({}).skip(skip).limit(limit).sort({ _id: 1 }),
        User.countDocuments()
    ]);
    res.json({ data: users, total, page, pages: Math.ceil(total / limit) });
});
```

```python
# WRONG: LIMIT without ORDER BY (non-deterministic results)
@app.get("/users")
def list_users():
    users = db.query(User).limit(20).all()  # Which 20? Random each time!

# CORRECT: Always ORDER BY with LIMIT
@app.get("/users")
def list_users():
    users = db.query(User).order_by(User.id).limit(20).all()
```

```python
# WRONG: Streaming all results to response (still loads into DB memory)
@app.get("/export/users")
def export_users():
    users = db.query(User).all()  # All in memory
    return StreamingResponse(generate_csv(users))

# CORRECT: Stream from database with server-side cursor
@app.get("/export/users")
def export_users():
    def generate():
        with db.engine.connect() as conn:
            result = conn.execution_options(stream_results=True).execute("SELECT * FROM users")
            for row in result:
                yield f"{row.id},{row.name}\n"
    return StreamingResponse(generate(), media_type="text/csv")
```

## Common Mistakes
The most common pagination anti-pattern is returning unbounded result sets, which causes memory exhaustion when tables grow. Offset pagination (`OFFSET N LIMIT M`) works for small page numbers but degrades as the offset increases — the database must scan and discard all preceding rows. `LIMIT` without `ORDER BY` returns non-deterministic results, meaning the same page request can return different data. Many developers also forget to cap the maximum page size, allowing clients to request `per_page=100000` and defeat the purpose of pagination.

## Gotchas
- Offset pagination is fine for small datasets (<10k rows) and admin UIs that rarely go past page 10
- Cursor pagination requires a stable sort column (usually the primary key or created_at)
- Cursor pagination cannot jump to arbitrary pages — use offset for that use case
- Always cap `per_page` at a reasonable maximum (50-100) to prevent abuse
- `COUNT(*)` on large PostgreSQL tables can be slow — consider caching the count or using estimated counts
- GraphQL connections (Relay spec) mandate cursor-based pagination — don't fight the spec
- For APIs, return pagination metadata: total count, next/prev links, current page
- `stream_results=True` (SQLAlchemy) uses server-side cursors — don't forget to close the connection

## Related
- anti-patterns/api-antipatterns.md
- api-design/pagination-patterns.md
- anti-patterns/perf-n-plus-one.md
