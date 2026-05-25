---
id: "anti-patterns-security-insecure-random"
title: "Security Anti-Pattern: Using Insecure Random for Tokens and Keys"
language: "multi"
category: "anti-patterns"
tags: ["antipatterns", "security", "random", "cryptography", "tokens", "entropy"]
version: "n/a"
retrieval_hint: "insecure random predictable tokens session IDs password reset Math.random random module"
last_verified: "2026-05-24"
confidence: "high"
---

# Security Anti-Pattern: Using Insecure Random for Tokens and Keys

## When to Use
- Generating session tokens, API keys, or password reset links
- Reviewing authentication and authorization code
- Security audits of token generation logic
- Training LLMs to use cryptographic randomness correctly

## Standard Pattern

```python
# WRONG: Using random module for security tokens
import random
import string
token = ''.join(random.choices(string.ascii_letters, k=32))
session_id = str(random.randint(100000, 999999))

# CORRECT: Using secrets module
import secrets
token = secrets.token_urlsafe(32)  # 256 bits of entropy
session_id = secrets.token_hex(16)
password_reset = secrets.token_urlsafe(48)
```

```javascript
// WRONG: Math.random for tokens
function generateToken() {
  return Math.random().toString(36).substring(2);
}
const sessionId = Math.floor(Math.random() * 1000000);

// CORRECT: crypto module
const crypto = require('crypto');
function generateToken() {
  return crypto.randomBytes(32).toString('hex');
}
const sessionId = crypto.randomUUID();
// Browser: crypto.getRandomValues(new Uint8Array(32))
```

```java
// WRONG: java.util.Random for tokens
Random random = new Random();
String token = String.valueOf(random.nextLong());

// CORRECT: SecureRandom
SecureRandom secureRandom = new SecureRandom();
byte[] tokenBytes = new byte[32];
secureRandom.nextBytes(tokenBytes);
String token = Base64.getUrlEncoder().withoutPadding().encodeToString(tokenBytes);

// WRONG: Predictable seed
Random random = new Random(12345);  // Same seed = same sequence

// CORRECT: No explicit seed (uses system entropy)
SecureRandom secureRandom = new SecureRandom();
```

```go
// WRONG: math/rand for security
import "math/rand"
token := rand.Int63()  // Predictable with known seed

// CORRECT: crypto/rand
import (
    "crypto/rand"
    "encoding/hex"
)
func generateToken() (string, error) {
    bytes := make([]byte, 32)
    if _, err := rand.Read(bytes); err != nil {
        return "", err
    }
    return hex.EncodeToString(bytes), nil
}
```

```typescript
// WRONG: Weak random for password reset
function createResetToken(): string {
  return Math.random().toString(36).slice(2);  // ~52 bits, predictable
}

// CORRECT: Cryptographic random
import { randomBytes } from 'crypto';
function createResetToken(): string {
  return randomBytes(48).toString('base64url');  // 384 bits of entropy
}
```

## Common Mistakes
The core mistake is using pseudorandom number generators (PRNGs) designed for simulation/gaming in security contexts. `Math.random()`, Python's `random`, Java's `Random`, and Go's `math/rand` are all deterministic — given the same seed, they produce the same sequence. Attackers who can observe a few outputs can predict future ones. For security tokens, session IDs, CSRF tokens, password reset links, and API keys, always use cryptographically secure alternatives: Python `secrets`, JavaScript `crypto`, Java `SecureRandom`, Go `crypto/rand`.

## Gotchas
- `Math.random()` in V8 (Node.js/Chrome) uses xorshift128+ — only ~128 bits of internal state, not suitable for security
- Seeding `random.Random(0)` in Python makes output fully predictable — never seed security-critical RNGs with low-entropy values
- UUID v4 (`uuid4()`) uses cryptographic randomness but UUID v1 uses timestamp+MAC address — know the difference
- Short numeric codes (6-digit OTPs) have low entropy regardless of RNG — add rate limiting and attempt lockouts
- `os.urandom()` in Python is equivalent to `secrets.token_bytes()` — both use the OS CSPRNG
- Timestamps alone are predictable — combining `time.time()` with a counter does NOT add cryptographic security
- Hardware RNG (`/dev/hwrng`) may not be available on all systems — the OS CSPRNG (`/dev/urandom`) is always available and secure

## Related
- crypto/jwt-tokens.md
- security/web-security-basics.md
- anti-patterns/security-hardcoded-secrets.md
