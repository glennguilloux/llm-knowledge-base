---
id: "crypto-tls-basics"
title: "TLS Basics: HTTPS Configuration, Certificate Pinning, and Self-Signed Certs"
language: "python"
category: "crypto"
tags: ["crypto", "tls", "https", "certificate", "ssl", "pinning", "self-signed"]
version: "3.12+"
retrieval_hint: "crypto TLS 1.3 concepts certificate pinning configuring HTTPS Python Java Node self-signed cert handling SNI"
last_verified: "2026-05-24"
confidence: "high"
---

# TLS Basics: HTTPS Configuration, Certificate Pinning, and Self-Signed Certs

## When to Use
- Configuring HTTPS for web services
- Understanding TLS 1.3 handshake
- Implementing certificate pinning for mobile apps
- Handling self-signed certificates in development
- Configuring TLS in various languages

## Standard Pattern

```python
import ssl
import httpx
import requests

# Python: Configure HTTPS client with proper TLS
# Modern TLS configuration (Python 3.10+)
ctx = ssl.create_default_context()
ctx.minimum_version = ssl.TLSVersion.TLSv1_2  # Minimum TLS 1.2
ctx.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM')  # Strong ciphers

# Make HTTPS request with custom TLS config
response = requests.get("https://api.example.com", verify=True)
# verify=True (default) checks the server certificate

# Client certificate authentication
ctx.load_cert_chain(
    certfile="client-cert.pem",
    keyfile="client-key.pem",
)
response = requests.get("https://api.example.com", cert=("client-cert.pem", "client-key.pem"))

# Certificate pinning (pin the expected certificate or CA)
import certifi

# Pin specific CA bundle
response = requests.get("https://api.example.com", verify=certifi.where())

# Custom certificate pinning with httpx
import ssl

class PinnedSSLContext:
    """SSL context that pins specific certificates."""
    
    def __init__(self, pinned_certs: list[str]):
        self.pinned_certs = pinned_certs
        self.ctx = ssl.create_default_context()
    
    def verify(self, conn, cert, errno, depth, ok):
        if not ok:
            return False
        # Check certificate against pinned certs
        fingerprint = cert.digest("sha256")
        return fingerprint in self.pinned_certs

# Self-signed certificate handling (development only!)
# WRONG: Disabling verification in production
response = requests.get("https://localhost:8443", verify=False)  # INSECURE!

# CORRECT: Use self-signed cert with verification
# Generate self-signed cert:
# openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
response = requests.get("https://localhost:8443", verify="./self-signed-cert.pem")

# Node.js TLS configuration (for reference)
# const https = require('https');
# const fs = require('fs');
# const options = {
#     key: fs.readFileSync('key.pem'),
#     cert: fs.readFileSync('cert.pem'),
#     minVersion: 'TLSv1.2',
#     ciphers: 'ECDHE+AESGCM:ECDHE+CHACHA20',
# };
# https.createServer(options, app).listen(443);

# Java TLS configuration (for reference)
# SSLContext ctx = SSLContext.getInstance("TLSv1.3");
# ctx.init(keyManagers, trustManagers, new SecureRandom());
# HttpsURLConnection.setDefaultSSLSocketFactory(ctx.getSocketFactory());

# TLS 1.3 handshake overview
# 1. Client Hello (supported ciphers, key share)
# 2. Server Hello (selected cipher, key share, certificate)
# 3. Finished (encrypted communication begins)
# Total: 1-RTT (vs 2-RTT in TLS 1.2)

# SNI (Server Name Indication)
# Allows multiple domains on same IP with different certificates
ctx = ssl.create_default_context()
ctx.check_hostname = True  # Verify hostname matches certificate

# Certificate validation checklist
# 1. Certificate is not expired
# 2. Certificate is signed by a trusted CA
# 3. Hostname matches certificate CN or SAN
# 4. Certificate is not revoked (check CRL/OCSP)
# 5. Certificate chain is complete
```

## Common Mistakes

```python
# WRONG: Disabling certificate verification
import urllib3
urllib3.disable_warnings()  # Suppresses ALL SSL warnings!
response = requests.get("https://api.example.com", verify=False)

# CORRECT: Use proper certificate verification
response = requests.get("https://api.example.com", verify=True)
# For self-signed certs in dev:
response = requests.get("https://localhost:8443", verify="./cert.pem")

# WRONG: Not checking hostname
ctx = ssl.create_default_context()
ctx.check_hostname = False  # Accepts any hostname!

# CORRECT: Always check hostname
ctx.check_hostname = True

# WRONG: Using outdated TLS version
ctx = ssl.SSLContext(ssl.PROTOCOL_TLS)  # May allow TLS 1.0/1.1!

# CORRECT: Set minimum version
ctx = ssl.create_default_context()
ctx.minimum_version = ssl.TLSVersion.TLSv1_2

# WRONG: Not handling certificate errors properly
try:
    response = requests.get("https://api.example.com")
except requests.exceptions.SSLError as e:
    print(f"SSL error: {e}")
    # Don't just ignore it!

# CORRECT: Handle specific SSL errors
from ssl import SSLCertVerificationError
try:
    response = requests.get("https://api.example.com")
except SSLCertVerificationError as e:
    print(f"Certificate verification failed: {e}")
except requests.exceptions.SSLError as e:
    print(f"SSL error: {e}")
```

## Gotchas
- TLS 1.3 reduces handshake to 1-RTT (faster than TLS 1.2's 2-RTT).
- `verify=False` disables ALL certificate checks. Never use in production.
- Self-signed certificates are fine for development. Use `verify="/path/to/cert.pem"`.
- Certificate pinning adds security but makes certificate rotation harder.
- SNI (Server Name Indication) is required for multiple HTTPS domains on one IP.
- `check_hostname=True` verifies the certificate's CN/SAN matches the requested hostname.
- OCSP stapling allows the server to prove its certificate is not revoked.
- HSTS (HTTP Strict Transport Security) tells browsers to always use HTTPS.
- Let's Encrypt provides free certificates with automatic renewal.
- Certificate transparency logs help detect misissued certificates.

## Related
- crypto/hmac.md
- crypto/key-derivation.md
- crypto/digital-signatures.md
- crypto/secure-random.md
