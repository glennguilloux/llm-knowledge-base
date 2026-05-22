---
id: "python-stdlib-hashlib-sha256"
title: "SHA-256 Hashing with hashlib"
language: "python"
category: "stdlib"
subcategory: "cryptography"
tags: ["hashlib", "sha256", "checksum", "integrity", "hash"]
version: "3.10+"
retrieval_hint: "SHA-256 hashing file checksum integrity verify"
last_verified: "2026-05-22"
confidence: "high"
---

# SHA-256 Hashing with hashlib

## When to Use
- Verifying file integrity (downloads, transfers, backups)
- Creating deterministic fingerprints of data
- Content-addressable storage (git-like hashing)
- Data deduplication identifiers

## Standard Pattern

```python
import hashlib


def hash_string(data: str) -> str:
    """Hash a string with SHA-256."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def hash_bytes(data: bytes) -> str:
    """Hash bytes with SHA-256."""
    return hashlib.sha256(data).hexdigest()


def hash_file(filepath: str, chunk_size: int = 8192) -> str:
    """Hash a file with SHA-256 using streaming (memory-efficient)."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(chunk_size):
            sha256.update(chunk)
    return sha256.hexdigest()


# Incremental hashing (for processing data in chunks)
sha256 = hashlib.sha256()
sha256.update(b"chunk 1 ")
sha256.update(b"chunk 2")
result = sha256.hexdigest()
```

## Common Mistakes

```python
# WRONG: Forgetting to encode strings
hashlib.sha256("hello")  # TypeError: Unicode-objects must be encoded

# CORRECT: Always encode strings first
hashlib.sha256("hello".encode("utf-8")).hexdigest()

# WRONG: Using SHA-256 for passwords
hashlib.sha256(password.encode()).hexdigest()  # Vulnerable to rainbow tables

# CORRECT: For passwords, use argon2 or bcrypt
from argon2 import PasswordHasher
ph = PasswordHasher()
hash = ph.hash(password)

# WRONG: Loading entire large file into memory
hashlib.sha256(open("large_file.bin", "rb").read()).hexdigest()  # Memory explosion

# CORRECT: Stream in chunks
hash_file("large_file.bin")  # Uses 8KB chunks
```

## Gotchas
- `hashlib.sha256()` returns bytes; use `.hexdigest()` for string output
- For HMAC (message authentication), use `hmac` module, not raw SHA-256
- SHA-256 output is always 64 hex characters (256 bits)
- Encoding matters: UTF-8 vs ASCII vs Latin-1 produce different hashes
- `hashlib.sha256()` is not thread-safe for concurrent `update()` calls
- Use `hashlib.file_digest()` (Python 3.11+) for simpler file hashing

## Related
- crypto/password-hashing.md
- crypto/sha256.md
