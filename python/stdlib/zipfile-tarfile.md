---
id: "python-stdlib-zipfile-tarfile"
title: "Working with ZIP and TAR Archives"
language: "python"
category: "stdlib"
subcategory: "file-formats"
tags: ["zipfile", "tarfile", "archive", "compress", "gzip", "extract"]
version: "3.10+"
retrieval_hint: "zipfile tarfile archive compress extract gzip tar zip"
last_verified: "2026-05-24"
confidence: "high"
---

# Working with ZIP and TAR Archives

## When to Use
- Bundling multiple files for download or transfer
- Extracting uploaded archives from users
- Creating backups or snapshots of directories
- Reading data from compressed datasets without extracting to disk

## Standard Pattern

```python
import zipfile
import tarfile
from pathlib import Path


# --- ZIP operations ---
def create_zip(output_path: str, files: list[str | Path]) -> None:
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in files:
            file = Path(file)
            zf.write(file, file.name)  # arcname = just filename, not full path


def extract_zip(zip_path: str, dest_dir: str) -> list[str]:
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest_dir)
        return zf.namelist()


def read_zip_member(zip_path: str, member_name: str) -> bytes:
    with zipfile.ZipFile(zip_path, "r") as zf:
        return zf.read(member_name)


def list_zip_contents(zip_path: str) -> list[dict]:
    with zipfile.ZipFile(zip_path, "r") as zf:
        return [
            {"name": info.filename, "size": info.file_size, "compressed": info.compress_size}
            for info in zf.infolist()
        ]


# --- TAR operations ---
def create_tar(output_path: str, source_dir: str) -> None:
    with tarfile.open(output_path, "w:gz") as tf:
        tf.add(source_dir, arcname=Path(source_dir).name)


def extract_tar(tar_path: str, dest_dir: str) -> list[str]:
    with tarfile.open(tar_path, "r:*") as tf:  # auto-detect compression
        tf.extractall(dest_dir, filter="data")  # Python 3.12+ safe filter
        return tf.getnames()


# --- Streaming large archives ---
def stream_zip_to_client(files: dict[str, bytes]):
    """Generate ZIP bytes for streaming response."""
    import io
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    buffer.seek(0)
    return buffer
```

## Common Mistakes

```python
# WRONG: Extracting untrusted ZIP (path traversal attack!)
with zipfile.ZipFile("user_upload.zip", "r") as zf:
    zf.extractall("/data")  # Could write to /data/../../etc/passwd

# CORRECT: Validate paths before extraction
import os

def safe_extract(zip_path: str, dest_dir: str) -> None:
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            target = os.path.join(dest_dir, member.filename)
            if not os.path.abspath(target).startswith(os.path.abspath(dest_dir)):
                raise ValueError(f"Path traversal: {member.filename}")
        zf.extractall(dest_dir)

# WRONG: Not using ZIP_DEFLATED (no compression)
with zipfile.ZipFile("out.zip", "w") as zf:  # ZIP_STORED = no compression
    zf.write("data.csv")

# CORRECT: Use ZIP_DEFLATED for compression
with zipfile.ZipFile("out.zip", "w", zipfile.ZIP_DEFLATED) as zf:
    zf.write("data.csv")

# WRONG: Reading entire ZIP into memory
data = read_zip_member("huge.zip", "big_file.csv")  # OOM risk

# CORRECT: Stream from ZIP
with zipfile.ZipFile("huge.zip", "r") as zf:
    with zf.open("big_file.csv") as f:
        for line in f:  # Iterates in chunks
            process(line)
```

## Gotchas
- `ZIP_DEFLATED` requires `zlib` (built-in on most systems); `ZIP_BZIP2` and `ZIP_LZMA` are alternatives
- `tarfile.open("file.tar.gz", "r:*")` auto-detects gzip/bzip2/xz compression
- Python 3.12+ `tarfile.extractall(filter="data")` prevents path traversal — always use it
- ZIP files support random access; TAR files are sequential (better for streaming)
- `ZipFile.open()` returns a binary file-like object — wrap in `io.TextIOWrapper` for text
- Use `arcname` in `zf.write()` to control the path inside the archive
- ZIP64 support is automatic for files >4GB
- `tarfile.add()` follows symlinks by default — use `recursive=False` to skip

## Related
- python/stdlib/file-io.md
- python/stdlib/pathlib.md
- python/web/fastapi/sse-streaming.md
