---
id: "performance-api-performance"
title: "API Performance Optimization"
language: "multi"
category: "performance"
tags: ["api", "performance", "pagination", "caching", "compression", "rate-limiting", "etags"]
version: "n/a"
retrieval_hint: "API performance pagination caching compression ETags rate limiting cursor offset gzip response optimization"
last_verified: "2026-05-24"
confidence: "high"
---

# API Performance Optimization

## When to Use
- Building APIs that serve high traffic
- Implementing pagination for large datasets
- Setting up caching headers and response compression
- Optimizing database-backed API endpoints

## Standard Pattern

```python
# === Cursor-Based Pagination (most efficient) ===

from fastapi import FastAPI, Query
from sqlalchemy import select
import base64

app = FastAPI()

@app.get("/api/articles")
async def list_articles(
    cursor: str | None = Query(None),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(Article).order_by(Article.created_at.desc()).limit(limit + 1)

    if cursor:
        # Decode cursor to created_at + id for stable pagination
        decoded = base64.b64decode(cursor).decode()
        created_at_str, last_id = decoded.split("|")
        query = query.where(
            (Article.created_at < created_at_str) |
            ((Article.created_at == created_at_str) & (Article.id < int(last_id)))
        )

    results = (await db.execute(query)).scalars().all()
    has_more = len(results) > limit
    articles = results[:limit]

    next_cursor = None
    if has_more:
        last = articles[-1]
        next_cursor = base64.b64encode(
            f"{last.created_at.isoformat()}|{last.id}".encode()
        ).decode()

    return {
        "data": [article_schema(a) for a in articles],
        "next_cursor": next_cursor,
        "has_more": has_more,
    }
```

```python
# === Response Compression ===

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=1000)  # Compress responses > 1KB

# For JSON APIs, compression typically reduces response size by 60-80%
```

```python
# === HTTP Caching with ETags ===

import hashlib
import json
from fastapi import Request, Response
from fastapi.responses import JSONResponse

@app.get("/api/articles/{article_id}")
async def get_article(article_id: int, request: Request):
    article = await get_article_from_db(article_id)

    # Generate ETag from content hash
    content_hash = hashlib.md5(
        json.dumps({"title": article.title, "body": article.body}).encode()
    ).hexdigest()
    etag = f'"{content_hash}"'

    # Check If-None-Match header
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304)  # Not Modified — client uses cache

    response = JSONResponse({
        "id": article.id,
        "title": article.title,
        "body": article.body,
    })
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "max-age=300"  # Cache for 5 minutes
    return response
```

```python
# === Rate Limiting ===

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/search")
@limiter.limit("30/minute")
async def search(request: Request, q: str):
    results = await perform_search(q)
    return {"results": results}

@app.post("/api/generate")
@limiter.limit("10/minute")
async def generate(request: Request):
    return {"result": await expensive_operation()}
```

```typescript
// === Frontend: Debounced Search + AbortController ===

import { useState, useEffect, useRef } from "react";

function useSearch(query: string) {
    const [results, setResults] = useState([]);
    const abortRef = useRef<AbortController | null>(null);

    useEffect(() => {
        // Abort previous request
        abortRef.current?.abort();

        if (!query.trim()) {
            setResults([]);
            return;
        }

        const timeout = setTimeout(async () => {
            abortRef.current = new AbortController();
            const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`, {
                signal: abortRef.current.signal,
            });
            setResults(await res.json());
        }, 300); // 300ms debounce

        return () => {
            clearTimeout(timeout);
            abortRef.current?.abort();
        };
    }, [query]);

    return results;
}
```

## Common Mistakes

```python
# WRONG: Offset pagination on large datasets (gets slower as offset grows)
@app.get("/api/articles")
async def list_articles(page: int, limit: int):
    offset = (page - 1) * limit
    articles = await db.query(Article).offset(offset).limit(limit).all()
    # Page 1000 with limit 20: database scans past 20,000 rows

# CORRECT: Cursor-based pagination (constant speed regardless of position)
articles = await db.query(Article).filter(Article.id > last_id).limit(20).all()
```

```python
# WRONG: No compression on JSON API responses
# A 500KB JSON response sent as-is to every client

# CORRECT: Enable GZip middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
# Same response: ~100KB with gzip
```

```python
# WRONG: No caching headers — browser refetches on every page load
@app.get("/api/config")
async def get_config():
    return {"theme": "dark", "language": "en"}

# CORRECT: Add Cache-Control for rarely-changing data
@app.get("/api/config")
async def get_config(response: Response):
    response.headers["Cache-Control"] = "public, max-age=3600"
    return {"theme": "dark", "language": "en"}
```

```typescript
// WRONG: Firing a search request on every keystroke
const handleInput = (e) => {
    fetch(`/api/search?q=${e.target.value}`);  // 10 requests for "javascript"
};

// CORRECT: Debounce + abort previous requests
const handleInput = useSearch(query);  // 1 request, 300ms after typing stops
```

## Gotchas
- Cursor pagination can't jump to arbitrary pages — if you need "page 5", use offset (with its performance cost)
- `COUNT(*)` for total results can be expensive on large tables — consider approximate counts or omit totals
- ETags use `304 Not Modified` which saves bandwidth but still requires a round-trip — `Cache-Control` avoids the request entirely
- GZip compression adds CPU overhead — set `minimum_size` to avoid compressing tiny responses
- Rate limiting by IP fails behind CDNs/proxies — use `X-Forwarded-For` or user ID in authenticated contexts
- `AbortController` in JavaScript prevents race conditions where slow responses arrive after faster ones
- Redis-based rate limiting is needed for multi-instance deployments (in-memory only works for single process)
- `max-age=0` with `must-revalidate` means "always check but cache if unchanged" — good for frequently-updated APIs

## Related
- performance/caching-strategies.md
- performance/database-optimization.md
- performance/connection-pooling.md
- api-design/pagination-patterns.md
- api-design/rest-conventions.md
