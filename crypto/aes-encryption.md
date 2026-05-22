---
id: "crypto-aes-encryption"
title: "AES-GCM Encryption Across Languages"
language: "multi"
category: "crypto"
subcategory: "encryption"
tags: ["aes", "gcm", "encryption", "decryption", "symmetric", "authenticated"]
version: "n/a"
retrieval_hint: "AES GCM encryption decryption symmetric authenticated"
last_verified: "2026-05-22"
confidence: "high"
---

# AES-GCM Encryption Across Languages

## When to Use
- Encrypting sensitive data at rest
- Secure data transmission
- Token encryption
- Configuration encryption

## NEVER Use For
- Password storage → use bcrypt/argon2
- Key derivation → use PBKDF2, scrypt, or argon2
- Hashing → use SHA-256

## Standard Pattern

### Python

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

def encrypt(plaintext: bytes, key: bytes) -> bytes:
    """Encrypt with AES-256-GCM. Returns nonce + ciphertext + tag."""
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 96-bit nonce
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    return nonce + ciphertext

def decrypt(data: bytes, key: bytes) -> bytes:
    """Decrypt AES-256-GCM."""
    aesgcm = AESGCM(key)
    nonce = data[:12]
    ciphertext = data[12:]
    return aesgcm.decrypt(nonce, ciphertext, None)

# Usage
key = AESGCM.generate_key(bit_length=256)
encrypted = encrypt(b"secret message", key)
decrypted = decrypt(encrypted, key)
```

### Java

```java
import javax.crypto.Cipher;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import java.security.SecureRandom;

public static byte[] encrypt(byte[] plaintext, byte[] key) throws Exception {
    Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
    SecretKeySpec keySpec = new SecretKeySpec(key, "AES");
    byte[] nonce = new byte[12];
    new SecureRandom().nextBytes(nonce);
    GCMParameterSpec spec = new GCMParameterSpec(128, nonce);
    cipher.init(Cipher.ENCRYPT_MODE, keySpec, spec);
    byte[] ciphertext = cipher.doFinal(plaintext);
    byte[] result = new byte[nonce.length + ciphertext.length];
    System.arraycopy(nonce, 0, result, 0, nonce.length);
    System.arraycopy(ciphertext, 0, result, nonce.length, ciphertext.length);
    return result;
}
```

### TypeScript (Node.js)

```typescript
import { createCipheriv, createDecipheriv, randomBytes } from 'crypto';

function encrypt(plaintext: Buffer, key: Buffer): Buffer {
  const nonce = randomBytes(12);
  const cipher = createCipheriv('aes-256-gcm', key, nonce);
  const encrypted = Buffer.concat([cipher.update(plaintext), cipher.final()]);
  const tag = cipher.getAuthTag();
  return Buffer.concat([nonce, encrypted, tag]);
}

function decrypt(data: Buffer, key: Buffer): Buffer {
  const nonce = data.subarray(0, 12);
  const tag = data.subarray(data.length - 16);
  const ciphertext = data.subarray(12, data.length - 16);
  const decipher = createDecipheriv('aes-256-gcm', key, nonce);
  decipher.setAuthTag(tag);
  return Buffer.concat([decipher.update(ciphertext), decipher.final()]);
}
```

## Common Mistakes

```python
# WRONG: Using ECB mode
cipher = AES.new(key, AES.MODE_ECB)  # Deterministic, leaks patterns!

# CORRECT: Use GCM (authenticated encryption)
aesgcm = AESGCM(key)

# WRONG: Reusing nonce
nonce = b"fixed_nonce"  # NEVER reuse nonce with same key!

# CORRECT: Generate random nonce each time
nonce = os.urandom(12)
```

## Gotchas
- AES-GCM provides both encryption and authentication (AEAD)
- Nonce must be unique for each encryption with the same key
- 12-byte (96-bit) nonce is recommended for GCM
- Key must be 16 (AES-128), 24 (AES-192), or 32 (AES-256) bytes
- Never reuse nonce+key combination
- Use `os.urandom()` or `crypto.randomBytes()` for nonce generation
- Store nonce with ciphertext (it's not secret)

## Related
- crypto/sha256.md
- crypto/password-hashing.md
- crypto/jwt-tokens.md
