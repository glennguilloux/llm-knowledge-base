---
id: "crypto-secure-random"
title: "Secure Random Generation: Python, Java, Node.js, and When NOT to Use Math.random"
language: "python"
category: "crypto"
tags: ["crypto", "secure-random", "secrets", "SecureRandom", "crypto-random", "math-random", "token-generation"]
version: "3.12+"
retrieval_hint: "crypto secure random generation per language secrets module Python SecureRandom Java crypto.randomBytes Node when NOT to use Math.random rand()"
last_verified: "2026-05-24"
confidence: "high"
---

# Secure Random Generation: Python, Java, Node.js, and When NOT to Use Math.random

## When to Use
- Generating tokens, API keys, and session IDs
- Creating cryptographic keys and nonces
- Generating passwords
- Any security-sensitive random data
- Understanding why Math.random() / rand() is insecure

## Standard Pattern

```python
import secrets
import string

# Python: secrets module (RECOMMENDED)
random_bytes = secrets.token_bytes(32)
random_hex = secrets.token_hex(32)
api_key = secrets.token_urlsafe(32)
random_int = secrets.randbelow(1_000_000)

# Generate secure password
password_chars = string.ascii_letters + string.digits + "!@#$%"
password = ''.join(secrets.choice(password_chars) for _ in range(16))

# Java: SecureRandom (RECOMMENDED)
# SecureRandom random = new SecureRandom();
# byte[] bytes = new byte[32];
# random.nextBytes(bytes);
# String token = Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);

# Node.js: crypto.randomBytes (RECOMMENDED)
# const crypto = require('crypto');
# const token = crypto.randomBytes(32).toString('hex');

# Go: crypto/rand (RECOMMENDED)
# import crypto_rand "crypto/rand"
# bytes := make([]byte, 32)
# crypto_rand.Read(bytes)

# When NOT to use insecure random
# Python: random module (NOT secure)
import random
token = random.randint(0, 1_000_000)  # NOT secure! Predictable!

# JavaScript: Math.random() (NOT secure)
# const token = Math.random().toString(36);  # NOT secure!

# Java: java.util.Random (NOT secure)
# Random random = new Random();  # NOT secure!

# C/C++: rand() (NOT secure)
# srand(time(NULL)); int token = rand();  # NOT secure!

# Secure password generation
def generate_password(length: int = 20) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    while True:
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        if (any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and any(c.isdigit() for c in password)
            and any(c in "!@#$%^&*" for c in password)):
            return password

# Secure token comparison (constant-time)
import hmac
def verify_token(provided: str, expected: str) -> bool:
    return hmac.compare_digest(provided, expected)

# UUID4 (uses os.urandom — secure)
import uuid
unique_id = uuid.uuid4()
```

## Common Mistakes

```python
# WRONG: Using random module for security-sensitive operations
import random
api_key = random.getrandbits(256)  # NOT secure! Predictable!

# CORRECT: Use secrets module
import secrets
api_key = secrets.token_bytes(32)  # Secure

# WRONG: Using Math.random() in JavaScript
# const token = Math.random().toString(36).substring(2);  # NOT secure!

# CORRECT: Use crypto.getRandomValues() in browser
# const array = new Uint8Array(32);
# crypto.getRandomValues(array);

# WRONG: Using java.util.Random in Java
# Random random = new Random();  # NOT secure for tokens!

# CORRECT: Use SecureRandom
# SecureRandom random = new SecureRandom();

# WRONG: Modulo bias when generating random integers
byte_val = secrets.token_bytes(1)[0]
random_num = byte_val % 100  # Biased! 0-55 appear more often

# CORRECT: Use secrets.randbelow (avoids modulo bias)
random_num = secrets.randbelow(100)  # Uniform distribution

# WRONG: Not using constant-time comparison for tokens
if provided_token == expected_token:  # Timing attack!
    grant_access()

# CORRECT: Use constant-time comparison
if hmac.compare_digest(provided_token, expected_token):
    grant_access()
```

## Gotchas
- secrets module uses os.urandom() which uses the OS cryptographic RNG.
- random module uses Mersenne Twister — fast but NOT cryptographically secure.
- Math.random() in JavaScript is NOT secure. Use crypto.getRandomValues().
- java.util.Random in Java is NOT secure. Use java.security.SecureRandom.
- rand() in C/C++ is NOT secure. Use getrandom() or /dev/urandom.
- Modulo bias: random_byte % N is biased if 256 is not divisible by N. Use secrets.randbelow().
- Constant-time comparison prevents timing attacks. Use hmac.compare_digest().
- UUID4 uses os.urandom() in Python — it's secure for uniqueness.
- For session IDs, use at least 128 bits (16 bytes) of randomness.
- For API keys, use at least 256 bits (32 bytes) of randomness.

## Related
- crypto/hmac.md
- crypto/key-derivation.md
- crypto/digital-signatures.md
- crypto/tls-basics.md
