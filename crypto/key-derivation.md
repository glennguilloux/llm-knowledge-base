---
id: "crypto-key-derivation"
title: "Key Derivation: PBKDF2, bcrypt, scrypt, and argon2"
language: "python"
category: "crypto"
tags: ["crypto", "key-derivation", "pbkdf2", "bcrypt", "scrypt", "argon2", "password-storage"]
version: "3.12+"
retrieval_hint: "crypto PBKDF2 bcrypt scrypt argon2 when to use which parameter selection password storage best practices"
last_verified: "2026-05-24"
confidence: "high"
---

# Key Derivation: PBKDF2, bcrypt, scrypt, and argon2

## When to Use
- Storing passwords securely
- Deriving encryption keys from passwords
- Understanding when to use each algorithm
- Choosing appropriate work factors

## Standard Pattern

```python
import hashlib
import secrets
import argon2
import bcrypt

# === argon2 (RECOMMENDED — winner of Password Hashing Competition) ===
# pip install argon2-cffi

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher(
    time_cost=3,       # Number of iterations
    memory_cost=65536,  # 64 MB memory usage
    parallelism=4,      # Number of parallel threads
    hash_len=32,        # Output hash length
    salt_len=16,        # Salt length
)

# Hash a password
hash = ph.hash("user_password")
# $argon2id$v=19$m=65536,t=3,p=4$...

# Verify a password
try:
    ph.verify(hash, "user_password")
    print("Password is correct")
except VerifyMismatchError:
    print("Password is wrong")

# Check if hash needs rehashing (parameters changed)
if ph.check_needs_rehash(hash):
    new_hash = ph.hash("user_password")
    # Update stored hash

# === bcrypt (widely supported, good default) ===
# pip install bcrypt

# Hash a password
salt = bcrypt.gensalt(rounds=12)  # rounds=12 is current recommendation
hashed = bcrypt.hashpw(b"user_password", salt)
# $2b$12$...

# Verify
if bcrypt.checkpw(b"user_password", hashed):
    print("Password is correct")

# === PBKDF2 (NIST-approved, FIPS-compliant) ===
# Built into Python standard library

def hash_password_pbkdf2(password: str) -> str:
    """Hash password with PBKDF2-HMAC-SHA256."""
    salt = secrets.token_bytes(32)
    dk = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        iterations=600_000,  # OWASP 2023 recommendation
    )
    # Store as: algorithm$iterations$salt$hash
    return f"pbkdf2_sha256$600000${salt.hex()}${dk.hex()}"

def verify_password_pbkdf2(password: str, stored: str) -> bool:
    """Verify password against PBKDF2 hash."""
    parts = stored.split('$')
    iterations = int(parts[1])
    salt = bytes.fromhex(parts[2])
    expected_hash = bytes.fromhex(parts[3])
    
    dk = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        iterations,
    )
    return hmac.compare_digest(dk, expected_hash)

# === scrypt (memory-hard, good alternative) ===
import scrypt

def hash_password_scrypt(password: str) -> bytes:
    """Hash password with scrypt."""
    return scrypt.hash(
        password.encode('utf-8'),
        salt=secrets.token_bytes(32),
        N=2**17,  # CPU/memory cost (131072)
        r=8,      # Block size
        p=1,      # Parallelization
        buflen=32,
    )

# === Comparison ===
# Algorithm  | Memory-Hard | GPU-Resistant | Recommended
# -----------|-------------|---------------|------------
# argon2id   | Yes         | Yes           | BEST (new projects)
# bcrypt     | Somewhat    | Somewhat      | GOOD (widely supported)
# scrypt     | Yes         | Yes           | GOOD (if argon2 unavailable)
# PBKDF2     | No          | No            | OK (FIPS compliance needed)
# SHA-256    | No          | No            | NEVER for passwords
# MD5        | No          | No            | NEVER (broken)

# === When to use which ===
# argon2id: New projects, best security
# bcrypt: When you need wide library support
# scrypt: When memory-hardness is required but argon2 unavailable
# PBKDF2: When FIPS 140-2 compliance is required
# NEVER: MD5, SHA-1, SHA-256 alone (too fast, no salt by default)
```

## Common Mistakes

```python
# WRONG: Using SHA-256 for password hashing (too fast!)
import hashlib
hash = hashlib.sha256(password.encode()).hexdigest()
# GPUs can compute billions of SHA-256 hashes per second!

# CORRECT: Use a proper password hashing function
hash = ph.hash(password)  # argon2

# WRONG: Using a fixed salt
salt = b"my-app-salt"  # Same salt for all passwords!

# CORRECT: Generate random salt for each password
salt = secrets.token_bytes(32)

# WRONG: Too few iterations
dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 1000)
# 1000 iterations is way too few!

# CORRECT: Use OWASP-recommended iterations
dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 600_000)

# WRONG: Not checking for rehashing
# If you increase work factors, old hashes remain weak

# CORRECT: Check and rehash on login
if ph.verify(stored_hash, password):
    if ph.check_needs_rehash(stored_hash):
        new_hash = ph.hash(password)
        update_stored_hash(user_id, new_hash)

# WRONG: Storing passwords in plain text
db.store(user_id, password)  # NEVER!

# CORRECT: Store only the hash
db.store(user_id, ph.hash(password))
```

## Gotchas
- **argon2id** is the recommended algorithm for new projects (winner of Password Hashing Competition).
- **bcrypt** is a good fallback with wide library support. Limit: 72-byte password input.
- **PBKDF2** is NIST-approved and FIPS-compliant but NOT memory-hard (vulnerable to GPU attacks).
- **scrypt** is memory-hard but less widely supported than bcrypt.
- **NEVER** use plain SHA-256, MD5, or SHA-1 for password hashing. They're too fast.
- Work factors should increase over time as hardware improves. Rehash on login.
- Always use a unique random salt per password. `secrets.token_bytes(32)`.
- OWASP 2023 recommendations: PBKDF2=600K iterations, bcrypt=12 rounds, argon2=3 iterations.
- Store the algorithm, salt, and hash together so you can verify and upgrade.
- Password hashing is for authentication. Use proper key derivation (HKDF) for encryption keys.

## Related
- crypto/password-hashing.md
- crypto/hmac.md
- crypto/secure-random.md
- crypto/digital-signatures.md
