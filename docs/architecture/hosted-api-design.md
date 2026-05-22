# Hosted API Design (Future)

> **Status:** Design document — not implemented.
> This describes how a hosted version of the knowledge base could work when someone wants to deploy it as a public API.

---

## Why

Not everyone wants to clone a repo and `pip install`. A hosted API would let anyone query the knowledge base with a single HTTP call — no setup, no Python environment, no dependencies. LLM tools (Claude, Cursor, Continue) could point directly at a hosted endpoint instead of running an MCP server locally.

---

## API Design

### Base URL

```
https://api.llm-kb.example.com/v1
```

### `GET /v1/search`

Search the knowledge base for relevant code patterns.

| Param   | Type   | Default | Description                                |
|---------|--------|---------|--------------------------------------------|
| `q`     | string | (req)   | Natural language query                     |
| `lang`  | string | `null`  | Filter by language (python, java, etc.)    |
| `top_k` | int    | `3`     | Number of results (1-10)                   |

**Response:**
```json
{
  "query": "FastAPI JWT authentication",
  "results": [
    {
      "id": "python-web-fastapi-auth-jwt",
      "title": "JWT Authentication with FastAPI",
      "language": "python",
      "category": "web",
      "tags": ["fastapi", "jwt", "auth", "security"],
      "confidence": "high",
      "content_snippet": "## Standard Pattern\n...",
      "url": "https://api.llm-kb.example.com/v1/entry/python-web-fastapi-auth-jwt"
    }
  ],
  "total": 1
}
```

### `GET /v1/prompt`

Build a complete system prompt with retrieved knowledge injected — ready to send to an LLM.

| Param        | Type   | Default  | Description                             |
|-------------|--------|----------|-----------------------------------------|
| `q`         | string | (req)    | What the user wants to code             |
| `lang`      | string | `null`   | Target language (auto-detected if null) |
| `max_tokens`| int    | `8192`   | Model's context window size             |
| `format`    | string | `text`   | `text` or `json` (for API consumers)    |

**Response (text):**
```
You are a coding assistant with access to verified knowledge base entries.

## Retrieved Knowledge

### JWT Authentication with FastAPI
**Language:** python | **Category:** web
...full entry content...

## Instructions
- Use the knowledge above to write correct, production-quality code
...
```

**Response (json):**
```json
{
  "query": "write a REST API",
  "language": "python",
  "prompt_text": "You are a coding assistant...",
  "metadata": {
    "query_tokens": 50,
    "system_prompt_tokens": 300,
    "knowledge_tokens": 2400,
    "total_tokens": 2750,
    "max_tokens": 8192,
    "entries_included": ["python-web-fastapi-auth-jwt", "python-stdlib-hashlib-sha256"],
    "entries_truncated": [],
    "budget_remaining": 5442
  }
}
```

### `GET /v1/entry/{entry_id}`

Return a single entry with full content.

**Response:**
```json
{
  "id": "python-web-fastapi-auth-jwt",
  "title": "JWT Authentication with FastAPI",
  "language": "python",
  "category": "web",
  "tags": ["fastapi", "jwt", "auth", "security"],
  "version": "3.10+",
  "confidence": "high",
  "last_verified": "2025-01-15",
  "content": "# JWT Authentication with FastAPI\n\n## When to Use\n..."
}
```

### `GET /v1/stats`

Return knowledge base statistics.

**Response:**
```json
{
  "total_entries": 276,
  "languages": ["bash", "csharp", "go", "java", "python", "rust", "sql", "typescript"],
  "categories": ["stdlib", "web", "db", "testing", "data", "patterns", "crypto", "devops"],
  "quality_score": 92,
  "last_updated": "2025-01-15"
}
```

### `GET /v1/scorecard`

Return quality metrics.

**Response:**
```json
{
  "coverage": 100,
  "depth": 94,
  "cross_references": 94,
  "freshness": 99,
  "anti_patterns": 80,
  "retrieval_accuracy": 87,
  "overall": 92
}
```

---

## Deployment Options

### Option A: Cloudflare Workers (Recommended)

- **Architecture:** Worker + KV Store
- **Latency:** < 50ms globally (edge-deployed)
- **Cost:** Free tier: 100K reads/day, 1K writes/day
- **Fit:** Perfect for read-heavy knowledge base. Entries change rarely (on release), served from KV.

```javascript
// Conceptual Cloudflare Worker
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname.split('/').filter(Boolean);

    switch (path[path.length - 1]) {
      case 'search':
        return handleSearch(request, env);
      case 'prompt':
        return handlePrompt(request, env);
      case 'stats':
        return jsonResponse(getStats(env));
      case 'scorecard':
        return jsonResponse(getScorecard(env));
      default:
        // Match /entry/{id}
        return handleEntry(path, env);
    }
  }
};

async function handleSearch(request, env) {
  const params = new URL(request.url).searchParams;
  const query = params.get('q');
  const lang = params.get('lang');
  const topK = parseInt(params.get('top_k') || '3');

  const entries = await env.KB_KV.get('entries_index', 'json');
  // Simple keyword search against the index
  const results = searchIndex(entries, query, lang).slice(0, topK);
  return jsonResponse({ query, results });
}
```

**Indexing at deploy time:**
```bash
# Build step: generate search index and bundle entries
python -c "
from llm_kb.retrieve import load_entries
import json

entries = load_entries()
index = [
    {
        'id': e.id, 'title': e.title, 'language': e.language,
        'category': e.category, 'tags': e.tags, 'confidence': e.confidence,
        'keywords': f'{e.title} {e.retrieval_hint} {\" \".join(e.tags)}'.lower()
    }
    for e in entries
]

# Upload to KV
with open('index.json', 'w') as f:
    json.dump(index, f)
"
wrangler kv:key put --binding=KB_KV "entries_index" --path index.json
```

### Option B: Vercel Serverless

- **Architecture:** Next.js API Routes with entries bundled at build time
- **Latency:** < 200ms (serverless cold start possible)
- **Cost:** Free tier: 100K function invocations/month
- **Fit:** Good for projects already on Vercel. Entries are `import`ed directly — no external DB.

```typescript
// pages/api/v1/search.ts
import type { NextApiRequest, NextApiResponse } from 'next';
import { entries } from '@/lib/entries';  // Bundled at build time

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  const { q, lang, top_k = '3' } = req.query as Record<string, string>;

  let filtered = entries;
  if (lang) {
    filtered = filtered.filter(e => e.language === lang);
  }

  const results = keywordSearch(filtered, q || '').slice(0, parseInt(top_k));

  res.status(200).json({
    query: q,
    results: results.map(e => ({
      id: e.id,
      title: e.title,
      language: e.language,
      category: e.category,
      tags: e.tags,
      confidence: e.confidence,
      url: `/api/v1/entry/${e.id}`,
    })),
  });
}
```

**Build step:**
```javascript
// next.config.js
module.exports = {
  // Pre-load entries at build time
  webpack: (config) => {
    config.module.rules.push({
      test: /entries\.ts$/,
      loader: 'val-loader',
      options: {
        // Load and serialize all entries for bundling
      },
    });
    return config;
  },
};
```

### Option C: Simple Python (FastAPI)

- **Architecture:** Single-file FastAPI app
- **Latency:** < 100ms on same-region deploy
- **Cost:** ~$5/month on Railway/Fly.io/Render
- **Fit:** Simplest option. Same Python code as local, just behind HTTP.

```python
# server.py — Production-hosted knowledge base API
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from llm_kb.retrieve import search, load_entries
from llm_kb.prompt import build_prompt as build_system_prompt
from llm_kb.scorecard import get_scorecard_data

app = FastAPI(title="LLM Knowledge Base API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"])

entries = load_entries()

@app.get("/v1/search")
async def search_endpoint(
    q: str = Query(..., description="Natural language query"),
    lang: str | None = Query(None),
    top_k: int = Query(3, ge=1, le=10),
):
    results = search(q, language=lang, top_k=top_k)
    return {
        "query": q,
        "results": [
            {
                "id": e.id,
                "title": e.title,
                "language": e.language,
                "category": e.category,
                "tags": e.tags,
                "confidence": e.confidence,
                "content_snippet": e.content[:500],
            }
            for e in results
        ],
    }

@app.get("/v1/prompt")
async def prompt_endpoint(
    q: str = Query(...),
    lang: str | None = Query(None),
    max_tokens: int = Query(8192),
):
    prompt, metadata = build_system_prompt(q, language=lang, max_tokens=max_tokens)
    return {
        "query": q,
        "language": lang or "auto",
        "prompt_text": prompt,
        "metadata": {
            "query_tokens": metadata.query_tokens,
            "system_prompt_tokens": metadata.system_prompt_tokens,
            "knowledge_tokens": metadata.knowledge_tokens,
            "total_tokens": metadata.total_tokens,
            "max_tokens": metadata.max_tokens,
            "entries_included": metadata.entries_included,
            "budget_remaining": metadata.budget_remaining,
        },
    }

@app.get("/v1/entry/{entry_id}")
async def entry_endpoint(entry_id: str):
    for entry in entries:
        if entry.id == entry_id:
            return {
                "id": entry.id,
                "title": entry.title,
                "language": entry.language,
                "category": entry.category,
                "tags": entry.tags,
                "confidence": entry.confidence,
                "content": entry.content,
            }
    return {"error": "Not found"}, 404

@app.get("/v1/stats")
async def stats_endpoint():
    languages = sorted(set(e.language for e in entries))
    categories = sorted(set(e.category for e in entries))
    return {
        "total_entries": len(entries),
        "languages": languages,
        "categories": categories,
        "quality_score": get_scorecard_data()["overall"],
    }

@app.get("/v1/scorecard")
async def scorecard_endpoint():
    return get_scorecard_data()
```

**Deploy (Railway/Fly.io/Render):**
```bash
# requirements.txt
fastapi>=0.100.0
uvicorn>=0.20.0
llm-knowledge-base==1.0.0

# Procfile
web: uvicorn server:app --host 0.0.0.0 --port $PORT
```

---

## Considerations

### Authentication
For public APIs (anyone can query), no auth needed. For rate-limited APIs, use API keys:

```python
# Simple API key middleware
from fastapi import Header, HTTPException
API_KEYS = {"sk-..."}  # From environment

async def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key not in API_KEYS:
        raise HTTPException(401, "Invalid API key")
```

### Rate Limiting
Knowledge base queries are cheap (grep-based, no LLM calls). Rate limits prevent abuse:

| Tier    | Requests/min | Requests/day | Cost   |
|---------|-------------|--------------|--------|
| Free    | 10          | 1,000        | $0     |
| Pro     | 100         | 10,000       | $5/mo  |
| Team    | 500         | 100,000      | $20/mo |

### Caching
Entries change rarely (on release). Cache aggressively:
- CDN cache entries for 24 hours
- `ETag` based on knowledge base version
- Service worker cache for browser-based clients

### Versioning
API versioned via URL prefix (`/v1/`). When schema changes break compatibility, deploy `/v2/` alongside `/v1/`.

### Monitoring
- Track query volume per language
- Track cache hit rate
- Track most-requested entries
- Alert if `/v1/scorecard` overall drops below 90

### Future: Semantic Search
If the hosted version wants to support semantic search (not just keyword matching):
- Embed entries once at deploy time using `sentence-transformers`
- Store embeddings in Cloudflare Vectorize or Pinecone
- `GET /v1/search?semantic=true` to use vector search
- Cost increase: Vector DB hosting + embedding computation

---

## Decision Matrix

| Factor              | Cloudflare Workers | Vercel Serverless | FastAPI (Railway) |
|---------------------|-------------------|-------------------|-------------------|
| **Setup complexity** | Medium            | Low               | Very Low          |
| **Latency**          | < 50ms            | < 200ms           | < 100ms           |
| **Free tier**        | Generous          | Generous          | Limited           |
| **Cold start**       | None              | Possible          | None (always-on)  |
| **Python native**    | No (JS)           | No (JS/TS)        | Yes               |
| **DB needed**        | KV (built-in)     | None (build-time) | None (in-memory)  |
| **Best for**         | Production scale  | Vercel projects   | Quick deployment  |

**Recommendation:** Start with Option C (FastAPI on Railway) for fastest time-to-deploy. Migrate to Cloudflare Workers when traffic exceeds 10K requests/day.
