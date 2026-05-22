---
id: "crypto-password-hashing"
title: "Password Hashing with bcrypt and argon2"
language: "multi"
category: "crypto"
subcategory: "passwords"
tags: ["password", "hash", "bcrypt", "argon2", "security", "authentication"]
version: "n/a"
retrieval_hint: "password hash bcrypt argon2 secure storage authentication"
last_verified: "2026-05-22"
confidence: "high"
---

# Password Hashing with bcrypt and argon2

## When to Use
- Storing user passwords securely
- Any credential storage where you need to verify (not retrieve) the original
- Session tokens that need to be compared, not decrypted

## NEVER Use For
- Data you need to decrypt later → use AES-GCM
- Non-secret identifiers → use SHA-256
- Encryption → hashing is one-way

## Standard Pattern

### Python — argon2 (Recommended)

```python
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher()

# Hash a password
hash = ph.hash("my_secure_password")

# Verify a password
try:
    ph.verify(hash, "my_secure_password")
    print("Password correct")
except VerifyMismatchError:
    print("Wrong password")

# Check if hash needs rehashing (e.g., after changing parameters)
if ph.check_needs_rehash(hash):
    hash = ph.hash("my_secure_password")  # Rehash with new params
```

### Python — bcrypt

```python
import bcrypt

# Hash a password
password = b"my_secure_password"
salt = bcrypt.gensalt(rounds=12)  # Cost factor (default: 12)
hash = bcrypt.hashpw(password, salt)

# Verify a password
if bcrypt.checkpw(password, hash):
    print("Password correct")
else:
    print("Wrong password")
```

### Java — bcrypt

```java
import org.mindrot.jbcrypt.BCrypt;

// Hash a password
String hash = BCrypt.hashpw("my_secure_password", BCrypt.gensalt(12));

// Verify a password
if (BCrypt.checkpw("my_secure_password", hash)) {
    System.out.println("Password correct");
}
```

### TypeScript — bcrypt

```typescript
import bcrypt from "bcrypt";

// Hash a password
const hash = await bcrypt.hash("my_secure_password", 12);

// Verify a password
const isValid = await bcrypt.compare("my_secure_password", hash);
```

## Common Mistakes

```python
# WRONG: Using SHA-256 for passwords
import hashlib
hash = hashlib.sha256(password.encode()).hexdigest()  # Vulnerable to rainbow tables

# CORRECT: Use argon2 or bcrypt
from argon2 import PasswordHasher
hash = PasswordHasher().hash(password)

# WRONG: Using a weak or no salt
hash = hashlib.md5(password.encode()).hexdigest()  # No salt, weak algorithm

# CORRECT: Let bcrypt/argon2 handle salt generation
hash = bcrypt.hashpw(password, bcrypt.gensalt())

# WRONG: Comparing hashes directly (timing attack vulnerable)
if stored_hash == computed_hash:  # Vulnerable to timing attacks

# CORRECT: Use constant-time comparison (bcrypt/argon2 do this internally)
if bcrypt.checkpw(password, stored_hash):
    pass
```

## Gotchas
- **argon2** is the recommended algorithm (OWASP, 2024) — memory-hard, GPU-resistant
- **bcrypt** has a 72-byte password limit; longer passwords are silently truncated
- Always use `bcrypt.checkpw()` or `argon2.verify()` — they handle constant-time comparison
- Cost factor / rounds should be as high as tolerable (bcrypt: 12+, argon2: defaults are fine)
- Never store passwords in plain text, even temporarily
- Salt is automatically generated and embedded in the hash string
- Rehash passwords when upgrading cost factors (check with `check_needs_rehash`)

## Related
- crypto/sha256.md
- crypto/jwt-tokens.md
