---
id: "api-design-pagination-patterns"
title: "Pagination Patterns for REST APIs"
language: "multi"
category: "api-design"
tags: ["api-design", "pagination", "cursor", "offset", "rest"]
version: "n/a"
retrieval_hint: "pagination patterns cursor offset REST API best practices"
last_verified: "2026-05-24"
confidence: "high"
---

# Pagination Patterns for REST APIs

## When to Use
- Returning paginated lists from REST API endpoints
- Large collections that would be too slow or memory-intensive to return at once
- Feeds of data that are updated frequently (cursor-based)
- Simple, stable datasets where total count is important (offset-based)

## Standard Pattern

```python
# === Offset-Based Pagination (Simple, common) ===
# GET /api/users?page=2&per_page=20

def paginate_offset(
    session: Session,
    model: type,
    page: int = 1,
    per_page: int = 20,
    max_per_page: int = 100,
) -> dict:
    """Paginate with offset. Simple but unstable under concurrent writes."""
    per_page = min(per_page, max_per_page)
    offset = (page - 1) * per_page

    items = session.query(model).offset(offset).limit(per_page).all()
    total = session.query(model).count()

    return {
        "data": [item.to_dict() for item in items],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page,
        },
    }


# === Cursor-Based Pagination (Stable, preferred for real-time) ===
# GET /api/users?cursor=eyJpZCI6NDJ9&limit=20
import base64
import json


def encode_cursor(data: dict) -> str:
    """Encode cursor as base64 JSON for opaque tokens."""
    return base64.urlsafe_b64encode(json.dumps(data).encode()).decode()


def decode_cursor(cursor: str) -> dict | None:
    """Decode cursor from base64 JSON."""
    try:
        return json.loads(base64.urlsafe_b64decode(cursor.encode()))
    except (json.JSONDecodeError, Exception):
        return None


def paginate_cursor(
    session: Session,
    model: type,
    cursor: str | None = None,
    limit: int = 20,
    max_limit: int = 100,
    sort_field: str = "id",
) -> dict:
    """Paginate with cursor. Stable under concurrent inserts/deletes."""
    limit = min(limit, max_limit)
    query = session.query(model).order_by(sort_field)

    if cursor:
        cursor_data = decode_cursor(cursor)
        if cursor_data and "last_id" in cursor_data:
            query = query.filter(getattr(model, sort_field) > cursor_data["last_id"])

    items = query.limit(limit + 1).all()
    has_next = len(items) > limit
    items = items[:limit]

    next_cursor = None
    if has_next and items:
        next_cursor = encode_cursor({"last_id": getattr(items[-1], sort_field)})

    return {
        "data": [item.to_dict() for item in items],
        "next_cursor": next_cursor,
        "has_more": has_next,
    }


# === Typescript Version (partial) ===
# interface PaginationParams {
#   page?: number;    // offset-based
#   per_page?: number;
#   cursor?: string;  // cursor-based
#   limit?: number;
# }
#
# interface PaginatedResponse<T> {
#   data: T[];
#   pagination?: {
#     page: number;
#     per_page: number;
#     total: number;
#     total_pages: number;
#   };
#   next_cursor?: string;
#   has_more?: boolean;
# }
```

## Common Mistakes

```python
# WRONG: Offset-based pagination on a frequently updated table
# New items inserted at position 1 shift existing items, causing duplicates/skips
GET /api/feed?page=1  # Returns items 1-20
# (new item inserted)
GET /api/feed?page=2  # Item at position 20 now at 21 — skips it entirely

# CORRECT: Use cursor-based pagination for frequently updated data
GET /api/feed?cursor=eyJsYXN0X2lkIjogMjB9&limit=20
# Always returns items strictly after last_id regardless of inserts


# WRONG: No maximum per_page limit (risk of abuse/DoS)
@app.get("/api/users")
def list_users(page: int = 1, per_page: int = 20):
    return paginate(session, User, page, per_page)
    # per_page=1000000 would return a million records


# CORRECT: Enforce a maximum
MAX_PER_PAGE = 100

@app.get("/api/users")
def list_users(page: int = 1, per_page: int = 20):
    per_page = min(per_page, MAX_PER_PAGE)
    return paginate(session, User, page, per_page)


# WRONG: Missing total count in offset pagination
# Client has no way to know total pages or remaining items
{"data": [...]}  # No pagination metadata

# CORRECT: Include pagination metadata
{"data": [...], "pagination": {"page": 1, "per_page": 20, "total": 142, "total_pages": 8}}


# WRONG: Exposing internal IDs in cursor
{"cursor": "42"}  # Client can guess other IDs

# CORRECT: Opaque cursor (base64 encoded)
{"next_cursor": "eyJsYXN0X2lkIjogNDJ9"}  # Not guessable or meaningful
```

## Gotchas
- **Offset instability**: Offset pagination skips or duplicates rows when items are inserted or deleted between page requests. Use cursor-based pagination for real-time data feeds.
- **Cursor encoding**: Always encode cursors opaquely (e.g., base64 JSON). Never expose internal IDs or timestamps directly, as clients may manipulate them.
- **Ordering requirement**: Cursor-based pagination requires a stable, unique sort field. `id` is ideal; `created_at` can have ties unless combined with `id` as a secondary sort.
- **Empty cursor handling**: An empty/null cursor means "start from the beginning." The first page should not require a cursor.
- **Missing totals**: Cursor-based pagination does not easily provide total counts. If clients need "page X of Y", offset-based is simpler.
- **Per-page limits**: Always enforce a server-side maximum (e.g., 100). Large per_page values can cause memory issues and abuse.
- **Filter consistency**: Pagination cursors must respect the same filters. A user who filters by `?status=active` and paginates to page 3 should still have the active filter applied.

## Related
- rest-conventions.md
- api-design/error-response-format.md
