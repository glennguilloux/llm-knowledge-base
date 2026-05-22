---
id: "python-web-file-uploads"
title: "File Upload Patterns"
language: "python"
category: "web"
tags: ["upload", "multipart", "presigned-url", "s3", "file", "form-data"]
version: "3.10+"
retrieval_hint: "file upload multipart presigned URL S3 form data"
last_verified: "2026-05-22"
confidence: "high"
---

# File Upload Patterns

## When to Use
- Accepting file uploads from users
- Uploading to cloud storage (S3, GCS, Azure Blob)
- Processing uploaded documents, images, or CSVs
- Building file-sharing features

## Standard Pattern

```python
# FastAPI file upload
from fastapi import FastAPI, UploadFile, File, HTTPException
from pathlib import Path
import shutil

app = FastAPI()
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if file.content_type not in ("image/jpeg", "image/png", "application/pdf"):
        raise HTTPException(400, "Unsupported file type")

    # Stream to disk (memory efficient)
    dest = UPLOAD_DIR / file.filename
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return {"filename": file.filename, "size": dest.stat().st_size}

# Multiple file upload
@app.post("/upload/batch")
async def upload_batch(files: list[UploadFile] = File(...)):
    results = []
    for file in files:
        dest = UPLOAD_DIR / file.filename
        with open(dest, "wb") as f:
            shutil.copyfileobj(file.file, f)
        results.append({"filename": file.filename})
    return results

# Presigned URL for S3 direct upload
import boto3
from botocore.config import Config

s3 = boto3.client("s3", config=Config(signature_version="s3v4"))

@app.post("/upload/presigned")
async def get_presigned_url(filename: str, content_type: str):
    presigned = s3.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": "my-bucket",
            "Key": f"uploads/{filename}",
            "ContentType": content_type,
        },
        ExpiresIn=3600,
    )
    return {"upload_url": presigned, "expires_in": 3600}

# Client uploads directly to S3 using presigned URL
# Frontend: PUT request to upload_url with file as body

# Upload with size limit
from fastapi import Request

@app.post("/upload/limited")
async def upload_limited(
    request: Request,
    file: UploadFile = File(...),
):
    max_size = 10 * 1024 * 1024  # 10MB
    size = 0
    content = bytearray()
    while chunk := await file.read(8192):
        size += len(chunk)
        if size > max_size:
            raise HTTPException(413, "File too large")
        content.extend(chunk)

    dest = UPLOAD_DIR / file.filename
    dest.write_bytes(content)
    return {"filename": file.filename, "size": size}
```

## Common Mistakes

```python
# WRONG: Loading entire file into memory
content = await file.read()  # OOM for large files!

# CORRECT: Stream to disk
with open(dest, "wb") as f:
    while chunk := await file.read(8192):
        f.write(chunk)

# WRONG: Using user-provided filename directly (path traversal)
dest = UPLOAD_DIR / file.filename  # Could be "../../../etc/passwd"

# CORRECT: Sanitize filename
from werkzeug.utils import secure_filename
safe_name = secure_filename(file.filename)
dest = UPLOAD_DIR / safe_name

# WRONG: No file type validation
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    # Accepts any file type — security risk

# CORRECT: Validate content type
ALLOWED_TYPES = {"image/jpeg", "image/png", "application/pdf"}
if file.content_type not in ALLOWED_TYPES:
    raise HTTPException(400, "Unsupported file type")

# WRONG: No file size limit — DoS vector
# CORRECT: Limit size in nginx config or application code
```

## Gotchas
- `UploadFile.file` is a `SpooledTemporaryFile` — small files in memory, large files on disk
- `file.filename` is user-provided — NEVER trust it for paths without sanitization
- `shutil.copyfileobj` streams efficiently — better than `file.read()` for large files
- Presigned URLs bypass your server — users upload directly to S3
- Content-Type from the client can be spoofed — verify file content, not just header
- Large uploads should use chunked transfer or presigned URLs
- `multipart/form-data` encoding is what browsers use for file uploads
- Production: set limits in reverse proxy (nginx: `client_max_body_size`)

## Related
- python/web/fastapi/basics.md
- python/web/fastapi/request-validation.md
- security/web-security-basics.md
