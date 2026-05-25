---
id: "crypto-hmac"
title: "HMAC-SHA256: Message Authentication and API Signature Verification"
language: "python"
category: "crypto"
tags: ["crypto", "hmac", "sha256", "authentication", "signature", "webhook", "api-security"]
version: "3.12+"
retrieval_hint: "crypto HMAC-SHA256 message authentication constant-time comparison API signature verification webhook verification"
last_verified: "2026-05-24"
confidence: "high"
---

# HMAC-SHA256: Message Authentication and API Signature Verification

## When to Use
- Verifying message integrity and authenticity
- Signing API requests (AWS, Stripe, GitHub webhooks)
- Constant-time comparison to prevent timing attacks
- Webhook signature verification

## Standard Pattern

```python
import hmac
import hashlib
import secrets

# Basic HMAC-SHA256
def sign_message(key: bytes, message: bytes) -> str:
    """Sign a message with HMAC-SHA256."""
    h = hmac.new(key, message, hashlib.sha256)
    return h.hexdigest()

def verify_signature(key: bytes, message: bytes, signature: str) -> bool:
    """Verify HMAC signature using constant-time comparison."""
    expected = hmac.new(key, message, hashlib.sha256).hexdigest()
    # Use hmac.compare_digest for constant-time comparison!
    return hmac.compare_digest(expected, signature)

# API request signing (like AWS Signature V4, simplified)
import time

def sign_api_request(
    secret_key: str,
    method: str,
    path: str,
    body: str = "",
    timestamp: str | None = None,
) -> dict:
    """Sign an API request with HMAC-SHA256."""
    ts = timestamp or str(int(time.time()))
    message = f"{ts}\n{method}\n{path}\n{body}"
    
    signature = hmac.new(
        secret_key.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()
    
    return {
        "X-Timestamp": ts,
        "X-Signature": signature,
    }

def verify_api_request(
    secret_key: str,
    method: str,
    path: str,
    body: str,
    timestamp: str,
    signature: str,
    max_age: int = 300,
) -> bool:
    """Verify a signed API request."""
    # Check timestamp freshness (prevent replay attacks)
    ts = int(timestamp)
    if abs(time.time() - ts) > max_age:
        return False
    
    # Verify signature
    expected = sign_api_request(secret_key, method, path, body, timestamp)
    return hmac.compare_digest(expected["X-Signature"], signature)

# Webhook signature verification (like Stripe/GitHub)
def verify_webhook(
    payload: bytes,
    signature: str,
    secret: str,
) -> bool:
    """Verify a webhook signature (GitHub-style)."""
    # GitHub sends: sha256=<hex>
    if not signature.startswith("sha256="):
        return False
    
    sig_hex = signature[7:]  # Remove "sha256=" prefix
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    
    return hmac.compare_digest(expected, sig_hex)

# Stripe-style webhook verification
def verify_stripe_webhook(
    payload: bytes,
    signature_header: str,
    secret: str,
    tolerance: int = 300,
) -> bool:
    """Verify Stripe webhook signature."""
    # Stripe sends: t=<timestamp>,v1=<hash>
    elements = dict(item.split("=") for item in signature_header.split(","))
    timestamp = elements.get("t", "")
    signature = elements.get("v1", "")
    
    # Check timestamp
    if abs(time.time() - int(timestamp)) > tolerance:
        return False
    
    # Compute expected signature
    signed_payload = f"{timestamp}.{payload.decode()}"
    expected = hmac.new(
        secret.encode(),
        signed_payload.encode(),
        hashlib.sha256,
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature)

# Generate secure API keys
def generate_api_key() -> str:
    """Generate a secure random API key."""
    return secrets.token_urlsafe(32)

# Example usage
if __name__ == "__main__":
    key = b"my-secret-key"
    message = b"Hello, World!"
    
    # Sign
    sig = sign_message(key, message)
    print(f"Signature: {sig}")
    
    # Verify
    is_valid = verify_signature(key, message, sig)
    print(f"Valid: {is_valid}")
    
    # Tampered message
    is_valid = verify_signature(key, b"Tampered!", sig)
    print(f"Tampered valid: {is_valid}")
```

## Common Mistakes

```python
# WRONG: Using == for signature comparison (timing attack!)
expected = hmac.new(key, message, hashlib.sha256).hexdigest()
if expected == signature:  # Timing attack vulnerability!
    print("Valid")

# CORRECT: Use hmac.compare_digest for constant-time comparison
if hmac.compare_digest(expected, signature):
    print("Valid")

# WRONG: Not checking timestamp (replay attack!)
def verify_webhook(payload, signature, secret):
    expected = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
    # Attacker can replay old valid requests!

# CORRECT: Include and verify timestamp
def verify_webhook(payload, signature, secret, timestamp, max_age=300):
    if time.time() - int(timestamp) > max_age:
        return False  # Too old — possible replay attack
    expected = hmac.new(secret, f"{timestamp}.{payload}", hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)

# WRONG: Using a weak key
key = b"password123"  # Easily guessable!

# CORRECT: Use a cryptographically random key
key = secrets.token_bytes(32)  # 256-bit random key

# WRONG: Not encoding strings consistently
sig1 = hmac.new(key, "hello".encode("utf-8"), hashlib.sha256).hexdigest()
sig2 = hmac.new(key, "hello".encode("ascii"), hashlib.sha256).hexdigest()
# May differ for non-ASCII characters!

# CORRECT: Always use UTF-8 encoding
sig = hmac.new(key, message.encode("utf-8"), hashlib.sha256).hexdigest()
```

## Gotchas
- **ALWAYS** use `hmac.compare_digest()` for signature comparison. `==` is vulnerable to timing attacks.
- Timing attacks can extract signatures by measuring response time differences.
- Include timestamps in signed messages to prevent replay attacks.
- Use `secrets.token_bytes()` or `secrets.token_urlsecure()` for generating keys.
- HMAC keys should be at least 256 bits (32 bytes) for SHA-256.
- Webhook signatures typically include a timestamp prefix. Parse it correctly.
- Different services use different signature formats (GitHub: `sha256=`, Stripe: `t=,v1=`).
- Store secrets in environment variables, never in code.
- Rotate keys periodically and support key rotation in verification.

## Related
- crypto/sha256.md
- crypto/tls-basics.md
- crypto/key-derivation.md
- crypto/secure-random.md
