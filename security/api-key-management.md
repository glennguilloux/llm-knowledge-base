---
id: "security-api-key-management"
title: "API Key Management"
language: "multi"
category: "security"
tags: ["api-key-management", "security", "secrets", "rotation", "hashing", "revocation", "rate-limiting"]
version: "n/a"
retrieval_hint: "API key management rotation storage secrets hashing revocation rate limiting environment variables secure headers"
last_verified: "2026-06-20"
confidence: "medium"
---

# API Key Management

## When to Use
- Issuing or consuming API keys for service-to-service access
- Designing secret storage, rotation, and revocation for API credentials
- Reviewing API gateway, webhook, and integration security
- Adding defensive controls around key scope, rate limits, and audit logs

## Standard Pattern

```python
# === Python: Store Only Hashes and Metadata ===
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

def create_api_key(owner_id: int) -> tuple[str, str]:
    raw_key = secrets.token_urlsafe(32)
    prefix = "ak_live_" + secrets.token_hex(3)
    stored_key = prefix + raw_key
    return stored_key, hash_api_key(stored_key)

def verify_api_key(candidate: str, stored_hash: str) -> bool:
    digest = hash_api_key(candidate)
    return hmac.compare_digest(digest, stored_hash)
```

```python
# === Python: Rotation and Revocation ===
class ApiKeyStore:
    def __init__(self):
        self.keys: dict[str, dict] = {}

    def revoke(self, key_id: str) -> None:
        self.keys[key_id]["revoked_at"] = datetime.now(timezone.utc)

    def is_valid(self, key_id: str, expires_at: datetime) -> bool:
        key = self.keys.get(key_id)
        if not key or key.get("revoked_at"):
            return False
        return datetime.now(timezone.utc) < expires_at

    def rotate(self, key_id: str, new_hash: str, expires_at: datetime) -> None:
        self.keys[key_id]["hash"] = new_hash
        self.keys[key_id]["expires_at"] = expires_at
```

```java
// === Java: Constant-Time API Key Comparison ===
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;

String hashApiKey(String rawKey) throws Exception {
    MessageDigest digest = MessageDigest.getInstance("SHA-256");
    return HexFormat.of().formatHex(digest.digest(rawKey.getBytes(StandardCharsets.UTF_8)));
}

boolean verifyApiKey(String candidate, String storedHash) throws Exception {
    return MessageDigest.isEqual(
        hashApiKey(candidate).getBytes(StandardCharsets.UTF_8),
        storedHash.getBytes(StandardCharsets.UTF_8)
    );
}
```

```python
# === Python: Rate Limit and Audit by Key ===
from collections import defaultdict
from datetime import datetime, timedelta

request_counts: dict[str, list[datetime]] = defaultdict(list)

def allow_request(api_key_id: str, limit: int = 100, window: timedelta = timedelta(minutes=1)) -> bool:
    now = datetime.now()
    recent = [t for t in request_counts[api_key_id] if now - t < window]
    request_counts[api_key_id] = recent
    if len(recent) >= limit:
        return False
    recent.append(now)
    return True
```

## Common Mistakes

```python
# WRONG: Store raw API keys in the database
api_keys.append({"key": "example-secret"})

# CORRECT: Store a hash and display only a prefix
api_keys.append({"key_hash": hash_api_key(raw_key), "prefix": "ak_live_abc"})
```

```python
# WRONG: Reuse the same key forever
create_api_key(owner_id)

# CORRECT: Rotate keys on a schedule and after suspected exposure
rotate(old_key_id, new_hash, expires_at)
```

```python
# WRONG: Compare keys with direct equality
if candidate == stored_hash:
    grant_access()

# CORRECT: Use constant-time comparison
if hmac.compare_digest(candidate_hash, stored_hash):
    grant_access()
```

```python
# WRONG: Allow unlimited requests per key
handle_request(api_key_id)

# CORRECT: Rate limit and log usage by key identity
if allow_request(api_key_id):
    handle_request(api_key_id)
```

## Gotchas
- Show only a short prefix to humans; never echo the full API key after creation
- Hash API keys before storing them so a database leak does not reveal usable credentials
- Rotation should overlap old and new keys briefly, then revoke the old key deliberately
- Revocation must be checked on every request, not only when issuing a key
- Rate limits should be enforced by key identity, owner, and route sensitivity
- API keys should be scoped narrowly and should not be used for interactive user login

## Related
- security/authentication-best-practices.md
- security/owasp-top-10.md
- security/web-security-basics.md
- security/https-tls-must-know.md
