---
id: "crypto-digital-signatures"
title: "Digital Signatures: RSA and ECDSA Signing and Verification"
language: "python"
category: "crypto"
tags: ["crypto", "digital-signatures", "rsa", "ecdsa", "signing", "verification", "certificates"]
version: "3.12+"
retrieval_hint: "crypto RSA ECDSA signing verification when to sign vs encrypt certificate chains code signing concepts"
last_verified: "2026-05-24"
confidence: "high"
---

# Digital Signatures: RSA and ECDSA Signing and Verification

## When to Use
- Verifying data integrity and authenticity
- Signing software releases and packages
- Certificate-based authentication
- Code signing
- Understanding when to sign vs encrypt

## Standard Pattern

```python
from cryptography.hazmat.primitives.asymmetric import rsa, ec, padding, utils
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from cryptography.x509 import load_pem_x509_certificate
import hashlib

# === RSA Signatures ===
# Generate RSA key pair
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=4096,  # 4096-bit RSA
    backend=default_backend(),
)
public_key = private_key.public_key()

# Sign data
message = b"Hello, World!"
signature = private_key.sign(
    message,
    padding.PSS(
        mgf=padding.MGF1(hashes.SHA256()),
        salt_length=padding.PSS.MAX_LENGTH,
    ),
    hashes.SHA256(),
)

# Verify signature
try:
    public_key.verify(
        signature,
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )
    print("Signature is valid!")
except Exception:
    print("Signature is INVALID!")

# === ECDSA Signatures (smaller keys, faster) ===
# Generate ECDSA key pair (P-256 curve)
ec_private_key = ec.generate_private_key(
    ec.SECP256R1(),  # P-256 curve
    backend=default_backend(),
)
ec_public_key = ec_private_key.public_key()

# Sign with ECDSA
ec_signature = ec_private_key.sign(
    message,
    ec.ECDSA(hashes.SHA256()),
)

# Verify ECDSA
try:
    ec_public_key.verify(ec_signature, message, ec.ECDSA(hashes.SHA256()))
    print("ECDSA signature is valid!")
except Exception:
    print("ECDSA signature is INVALID!")

# === Key serialization ===
# Serialize private key (encrypted)
pem_private = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.BestAvailableEncryption(b"password"),
)

# Serialize public key
pem_public = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
)

# Load keys from PEM
loaded_private = serialization.load_pem_private_key(
    pem_private, password=b"password", backend=default_backend()
)
loaded_public = serialization.load_pem_public_key(
    pem_public, backend=default_backend()
)

# === Sign vs Encrypt ===
# Signing: Prove authenticity (private key signs, public key verifies)
# Encryption: Ensure confidentiality (public key encrypts, private key decrypts)

# Sign then encrypt pattern:
# 1. Sign with sender's private key (proves sender identity)
# 2. Encrypt with recipient's public key (ensures only recipient can read)

# === Certificate chain verification (simplified) ===
def verify_certificate_chain(cert_pem: bytes, ca_bundle_pem: bytes) -> bool:
    """Verify a certificate against a CA bundle."""
    cert = load_pem_x509_certificate(cert_pem)
    # In production, use a proper certificate validation library
    # This is a simplified example
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    if cert.not_valid_before_utc > now or cert.not_valid_after_utc < now:
        return False  # Certificate expired
    return True

# === Hash-then-sign pattern ===
# For large data, hash first then sign the hash
def sign_large_data(private_key, data: bytes) -> bytes:
    """Sign large data by hashing first."""
    digest = hashlib.sha256(data).digest()
    return private_key.sign(
        digest,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        utils.Prehashed(hashes.SHA256()),
    )
```

## Common Mistakes

```python
# WRONG: Using PKCS#1 v1.5 padding (vulnerable to padding oracle attacks)
signature = private_key.sign(
    message,
    padding.PKCS1v15(),  # Legacy padding — avoid!
    hashes.SHA256(),
)

# CORRECT: Use PSS padding (more secure)
signature = private_key.sign(
    message,
    padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
    hashes.SHA256(),
)

# WRONG: Signing without hashing (RSA can only sign small data)
# RSA-2048 can only sign ~256 bytes directly

# CORRECT: Always hash before signing (or use Prehashed)
signature = private_key.sign(message, padding.PSS(...), hashes.SHA256())

# WRONG: Confusing signing with encryption
# Signing does NOT hide the message — it proves who sent it
# Encryption hides the message — but doesn't prove who sent it

# CORRECT: Use signing for authenticity, encryption for confidentiality
# For both: sign then encrypt

# WRONG: Using weak key sizes
private_key = rsa.generate_private_key(public_exponent=65537, key_size=1024)
# 1024-bit RSA is considered weak!

# CORRECT: Use at least 2048-bit RSA (4096 recommended)
private_key = rsa.generate_private_key(public_exponent=65537, key_size=4096)

# WRONG: Not handling verification exceptions
public_key.verify(signature, message, padding.PSS(...), hashes.SHA256())
# If invalid, raises exception — must catch it!

# CORRECT: Catch verification exceptions
try:
    public_key.verify(signature, message, padding.PSS(...), hashes.SHA256())
    print("Valid")
except Exception:
    print("Invalid signature")
```

## Gotchas
- **RSA**: Use PSS padding (not PKCS#1 v1.5). Minimum 2048-bit keys (4096 recommended).
- **ECDSA**: Smaller keys than RSA for equivalent security. P-256 is standard.
- **Sign vs Encrypt**: Signing proves authenticity. Encryption ensures confidentiality.
- **Hash-then-sign**: For large data, hash first then sign the hash.
- **Certificate chains**: Root CA → Intermediate CA → End-entity certificate.
- **Code signing**: Sign software releases so users can verify authenticity.
- **Key storage**: Private keys must be stored securely (HSM, key vault, encrypted file).
- **Nonce reuse**: ECDSA requires a unique random nonce for each signature. Reuse leaks the private key.
- **Algorithm choice**: ECDSA for performance, RSA for compatibility.

## Related
- crypto/hmac.md
- crypto/tls-basics.md
- crypto/key-derivation.md
- crypto/secure-random.md
