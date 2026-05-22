---
id: "crypto-rsa-keygen"
title: "RSA Key Generation"
language: "multi"
category: "crypto"
subcategory: "asymmetric"
tags: ["rsa", "key", "public", "private", "asymmetric", "signing"]
version: "n/a"
retrieval_hint: "RSA key generation public private asymmetric signing"
last_verified: "2026-05-22"
confidence: "high"
---

# RSA Key Generation

## When to Use
- Digital signatures
- Key exchange
- JWT with RS256
- Certificate generation

## Standard Pattern

### Python

```python
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization

# Generate key pair
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)
public_key = private_key.public_key()

# Serialize keys
private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)
public_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
)

# Sign
signature = private_key.sign(
    data,
    padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
    hashes.SHA256(),
)

# Verify
public_key.verify(signature, data, padding.PSS(...), hashes.SHA256())
```

### Java

```java
import java.security.*;

KeyPairGenerator gen = KeyPairGenerator.getInstance("RSA");
gen.initialize(2048);
KeyPair pair = gen.generateKeyPair();
PrivateKey privateKey = pair.getPrivate();
PublicKey publicKey = pair.getPublic();
```

### TypeScript (Node.js)

```typescript
import { generateKeyPairSync } from 'crypto';

const { publicKey, privateKey } = generateKeyPairSync('rsa', {
  modulusLength: 2048,
  publicKeyEncoding: { type: 'spki', format: 'pem' },
  privateKeyEncoding: { type: 'pkcs8', format: 'pem' },
});
```

## Common Mistakes

```python
# WRONG: Using small key size
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=1024,  # Too small!
)

# CORRECT: Use 2048+ bits
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)

# WRONG: Using public_exponent=3 (vulnerable to attacks)
private_key = rsa.generate_private_key(
    public_exponent=3,  # Small exponent attack
    key_size=2048,
)

# CORRECT: Always use 65537 (standard)
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)

# WRONG: Using PKCS1v15 padding for signatures (vulnerable)
signature = private_key.sign(data, padding.PKCS1v15(), hashes.SHA256())

# CORRECT: Use PSS padding for signatures, OAEP for encryption
signature = private_key.sign(
    data,
    padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
    hashes.SHA256(),
)
```

## Gotchas
- Minimum key size: 2048 bits (3072+ recommended for long-term)
- RSA is slow for large data — use hybrid encryption (RSA + AES)
- Store private keys securely (HSM, key vault)
- Use OAEP padding for encryption, PSS for signing
- Never share private keys

## Related
- crypto/jwt-tokens.md
- crypto/aes-encryption.md
