---
id: "python-web-fastapi-cors-static"
title: "FastAPI CORS and Static Files"
language: "python"
category: "web"
subcategory: "api-framework"
tags: ["fastapi", "cors", "static", "files", "middleware", "origins"]
version: "3.10+"
retrieval_hint: "FastAPI CORS cross-origin static files mount middleware origins"
last_verified: "2026-05-24"
confidence: "high"
---

# FastAPI CORS and Static Files

## When to Use
- Frontend on a different port/domain needs to call the API (CORS)
- Serving uploaded images, documents, or generated reports
- Serving a single-page application (SPA) from the same server
- Development: React/Vue dev server on :3000 calling API on :8000

## Standard Pattern

```python
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

app = FastAPI()

# --- CORS Configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://myapp.com",
    ],
    allow_credentials=True,  # Allow cookies/auth headers
    allow_methods=["*"],     # GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],     # Authorization, Content-Type, etc.
)

# --- Static file serving ---
# Mount a directory at /static URL path
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Serve uploaded files ---
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)) -> dict:
    dest = UPLOAD_DIR / file.filename
    dest.write_bytes(await file.read())
    return {"url": f"/files/{file.filename}"}


@app.get("/files/{filename}")
async def serve_upload(filename: str):
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)


# --- Serve SPA (catch-all for client-side routing) ---
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    file_path = Path("dist") / full_path
    if file_path.is_file():
        return FileResponse(file_path)
    return FileResponse("dist/index.html")  # Fallback to SPA entry
```

## Common Mistakes

```python
# WRONG: Using allow_origins=["*"] with allow_credentials=True
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,  # Browsers reject this combination!
)

# CORRECT: Either use wildcard OR credentials, not both
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://myapp.com"],  # Specific origins
    allow_credentials=True,
)

# WRONG: CORS middleware added after routes
app = FastAPI()
@app.get("/api/data")
async def get_data():
    return {"data": 1}

app.add_middleware(CORSMiddleware, allow_origins=["*"])  # May not work as expected

# CORRECT: CORS middleware first (executes last in middleware stack)
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])  # Add early

# WRONG: Serving static files without size limits
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()  # 10GB file = OOM

# CORRECT: Check file size before reading
from fastapi import HTTPException

MAX_SIZE = 10 * 1024 * 1024  # 10MB

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = bytearray()
    while chunk := await file.read(8192):
        content.extend(chunk)
        if len(content) > MAX_SIZE:
            raise HTTPException(status_code=413, detail="File too large")
    dest = UPLOAD_DIR / file.filename
    dest.write_bytes(content)
    return {"size": len(content)}
```

## Gotchas
- CORS middleware must be added BEFORE route definitions for consistent behavior
- `allow_credentials=True` forbids `allow_origins=["*"]` — browsers enforce this
- Preflight `OPTIONS` requests are handled automatically by the middleware
- `StaticFiles` must be mounted AFTER route definitions to avoid shadowing API routes
- Use `FileResponse` for single files, `StaticFiles` for directory serving
- Path traversal attacks: always validate filenames against a whitelist or use UUIDs
- In production, serve static files through Nginx/CDN, not FastAPI

## Real-World Example

### Production CORS + Static File Serving with Security Headers

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import uuid

app = FastAPI()

# CORS: restrict to known origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://myapp.com", "https://www.myapp.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Static files with cache headers
static_dir = Path("./static")
static_dir.mkdir(exist_ok=True)


@app.get("/static/{filename:path}")
async def serve_static(filename: str):
    # Prevent path traversal
    file_path = (static_dir / filename).resolve()
    if not file_path.is_relative_to(static_dir.resolve()):
        return {"error": "Invalid path"}, 400
    if not file_path.exists():
        return {"error": "Not found"}, 404
    return FileResponse(
        file_path,
        headers={"Cache-Control": "public, max-age=31536000"},
    )


@app.post("/upload")
async def upload_file(file: UploadFile):
    # Generate safe filename to prevent path traversal
    ext = Path(file.filename or "").suffix
    safe_name = f"{uuid.uuid4().hex}{ext}"
    dest = static_dir / safe_name
    content = await file.read()
    dest.write_bytes(content)
    return {"url": f"/static/{safe_name}"}
```

## Related
- python/web/fastapi/basics.md
- python/web/fastapi/middleware.md
- python/web/fastapi/background-tasks.md
