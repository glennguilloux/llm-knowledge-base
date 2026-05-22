---
id: "python-web-fastapi-file-upload"
title: "FastAPI File Upload and Form Handling"
language: "python"
category: "web"
subcategory: "api-framework"
tags: ["fastapi", "upload", "file", "form", "multipart", "binary"]
version: "3.10+"
retrieval_hint: "FastAPI file upload form multipart UploadFile File binary"
last_verified: "2026-05-22"
confidence: "high"
---

# FastAPI File Upload and Form Handling

## When to Use
- User file uploads (images, documents, CSVs)
- Multipart form submissions (form fields + files)
- Processing uploaded data before storage (validation, transformation)
- Handling large file uploads with streaming

## Standard Pattern

```python
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import aiofiles

app = FastAPI()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_SIZE = 10 * 1024 * 1024  # 10MB


# --- Single file upload ---
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)) -> dict:
    # Validate file type
    allowed_types = {"image/jpeg", "image/png", "application/pdf"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"File type {file.content_type} not allowed")

    # Stream to disk (memory efficient)
    dest = UPLOAD_DIR / file.filename
    size = 0
    async with aiofiles.open(dest, "wb") as f:
        while chunk := await file.read(8192):
            size += len(chunk)
            if size > MAX_SIZE:
                dest.unlink()  # Clean up partial file
                raise HTTPException(status_code=413, detail="File too large")
            await f.write(chunk)

    return {"filename": file.filename, "size": size, "content_type": file.content_type}


# --- Multiple files ---
@app.post("/upload/multiple")
async def upload_multiple(files: list[UploadFile] = File(...)) -> list[dict]:
    results = []
    for file in files:
        dest = UPLOAD_DIR / file.filename
        content = await file.read()
        if len(content) > MAX_SIZE:
            raise HTTPException(status_code=413, detail=f"{file.filename} too large")
        dest.write_bytes(content)
        results.append({"filename": file.filename, "size": len(content)})
    return results


# --- Form fields + file ---
@app.post("/upload/with-metadata")
async def upload_with_metadata(
    title: str = Form(...),
    description: str = Form(""),
    category: str = Form(...),
    file: UploadFile = File(...),
) -> dict:
    dest = UPLOAD_DIR / file.filename
    dest.write_bytes(await file.read())
    return {
        "title": title,
        "description": description,
        "category": category,
        "filename": file.filename,
    }


# --- Serve uploaded files ---
@app.get("/files/{filename}")
async def serve_file(filename: str):
    file_path = UPLOAD_DIR / filename
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, filename=filename)
```

## Common Mistakes

```python
# WRONG: Reading entire file into memory
content = await file.read()  # 1GB file = 1GB RAM

# CORRECT: Stream in chunks
async with aiofiles.open(dest, "wb") as f:
    while chunk := await file.read(8192):
        await f.write(chunk)

# WRONG: No file type validation
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    dest.write_bytes(await file.read())  # Could be .exe, .sh, etc.

# CORRECT: Validate content type and extension
ALLOWED_TYPES = {"image/jpeg", "image/png", "application/pdf"}
if file.content_type not in ALLOWED_TYPES:
    raise HTTPException(status_code=400, detail="File type not allowed")

# WRONG: Using user-provided filename directly (path traversal)
dest = UPLOAD_DIR / file.filename  # Could be "../../etc/passwd"

# CORRECT: Sanitize filename or use UUID
import uuid
safe_name = f"{uuid.uuid4()}{Path(file.filename).suffix}"
dest = UPLOAD_DIR / safe_name

# WRONG: Using Form() for JSON body
@app.post("/items")
async def create_item(name: str = Form(...)):  # Expects form data, not JSON

# CORRECT: Use Body/Pydantic for JSON, Form for form data
@app.post("/items")
async def create_item(item: ItemCreate):  # JSON body
    pass
```

## Gotchas
- `UploadFile` is a spooled temporary file — small files in memory, large files on disk
- `file.read()` reads the entire file; use `file.read(size)` for chunked reading
- `Form()` and `File()` can be mixed in the same endpoint — both use multipart encoding
- `file.filename` comes from the client — never trust it for storage paths
- Use `aiofiles` for async file I/O; `Path.write_bytes()` is synchronous
- `file.content_type` comes from the client's `Content-Type` header — validate it
- For large uploads, configure the reverse proxy (Nginx) `client_max_body_size`
- `UploadFile` has `.file` attribute for the underlying `SpooledTemporaryFile`

## Related
- python/web/fastapi/cors-static.md
- python/web/fastapi/basics.md
- python/web/fastapi/request-validation.md
