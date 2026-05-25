---
id: "security-https-tls-must-know"
title: "HTTPS and TLS Essentials"
language: "multi"
category: "security"
tags: ["https", "tls", "ssl", "certificates", "hsts", "mixed-content", "security"]
version: "n/a"
retrieval_hint: "HTTPS TLS SSL certificates HSTS mixed content secure transport encryption Let's Encrypt certificate management"
last_verified: "2026-05-24"
confidence: "high"
---

# HTTPS and TLS Essentials

## When to Use
- Configuring web servers for production
- Setting up SSL/TLS certificates
- Handling redirects from HTTP to HTTPS
- Managing certificate renewal and security headers

## Standard Pattern

```nginx
# === Nginx: HTTPS Configuration ===

# HTTP → HTTPS redirect
server {
    listen 80;
    server_name example.com www.example.com;
    return 301 https://$host$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name example.com www.example.com;

    # CORRECT: Modern TLS configuration
    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    # CORRECT: TLS 1.2+ only (disable TLS 1.0, 1.1)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;

    # CORRECT: HSTS (force HTTPS for all future visits)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    # CORRECT: Security headers
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Content-Security-Policy "default-src 'self'" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # OCSP stapling for faster TLS handshakes
    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
}
```

```python
# === Python: Enforce HTTPS in application ===

from fastapi import FastAPI, Request
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app = FastAPI()

# CORRECT: Force HTTPS redirect (behind reverse proxy)
app.add_middleware(HTTPSRedirectMiddleware)

# CORRECT: Trust proxy headers for HTTPS detection
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response
```

```bash
# === Let's Encrypt: Free Certificate Management ===

# Install certbot
apt install certbot python3-certbot-nginx

# Get certificate (interactive)
certbot --nginx -d example.com -d www.example.com

# Auto-renewal (certbot installs a cron job)
certbot renew --dry-run  # Test renewal

# Check certificate expiry
echo | openssl s_client -connect example.com:443 2>/dev/null | openssl x509 -noout -dates
```

```python
# === Application-Level HTTPS Checks ===

def ensure_https(url: str) -> str:
    """Ensure a URL uses HTTPS."""
    if url.startswith("http://"):
        return "https://" + url[7:]  # Force HTTPS
    if not url.startswith("https://"):
        raise ValueError(f"Invalid URL scheme: {url}")
    return url

# CORRECT: Block mixed content in API responses
def validate_api_url(url: str) -> str:
    """API URLs must use HTTPS in production."""
    if os.environ.get("ENVIRONMENT") == "production":
        if not url.startswith("https://"):
            raise ValueError("Only HTTPS URLs allowed in production")
    return url
```

## Common Mistakes

```nginx
# WRONG: Allowing TLS 1.0 and 1.1 (vulnerable to POODLE, BEAST)
ssl_protocols TLSv1 TLSv1.1 TLSv1.2 TLSv1.3;

# CORRECT: TLS 1.2+ only
ssl_protocols TLSv1.2 TLSv1.3;
```

```python
# WRONG: Redirecting after processing the request
@app.post("/login")
async def login(request: Request):
    user = authenticate(request)  # Credentials sent over HTTP!
    return RedirectResponse(url="/dashboard")  # Then redirect to HTTPS

# CORRECT: Redirect at the server/proxy level BEFORE the request reaches the app
# Nginx: return 301 https://$host$request_uri;
```

```python
# WRONG: Missing HSTS header (browser can try HTTP first)
# Without HSTS, user types example.com → browser tries HTTP first → redirected

# CORRECT: Set HSTS to tell browser to ALWAYS use HTTPS
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

```python
# WRONG: Serving HTTP for API endpoints
http://api.example.com/users  # Credentials in Authorization header sent in cleartext

# CORRECT: All API traffic over HTTPS
https://api.example.com/users
```

## Gotchas
- HSTS `max-age` starts at 1 day for testing (`max-age=86400`), then increase to 1 year (`max-age=31536000`)
- HSTS `preload` submits your domain to browser HSTS preload lists — hard to remove, plan carefully
- Mixed content: an HTTPS page loading an HTTP resource (script, image, iframe) — browsers block active mixed content
- TLS termination at a load balancer means app server sees HTTP — use `X-Forwarded-Proto: https` header
- Certificate pinning is deprecated in favor of Certificate Transparency and HSTS preload
- Self-signed certificates cause browser warnings — use Let's Encrypt (free) in production
- TLS 1.3 removes cipher negotiation (faster handshake) — enable it when available
- `Secure` cookie flag means the cookie is only sent over HTTPS — always set for session cookies
- HTTP→HTTPS redirect is important but the first HTTP request is still unencrypted — HSTS fixes this
- Auto-renew Let's Encrypt certs before expiry (default: 30 days before)

## Related
- security/web-security-basics.md
- security/owasp-top-10.md
- security/authentication-best-practices.md
- devops/ssl-tls/certbot-letsencrypt.md
