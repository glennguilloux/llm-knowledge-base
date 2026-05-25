---
id: "devops-ssl-tls-certbot"
title: "Certbot and Let's Encrypt: Automated SSL Certificate Management"
language: "shell"
category: "devops"
subcategory: "security"
tags: ["ssl", "tls", "certbot", "letsencrypt", "certificates", "https", "renewal"]
version: "latest"
retrieval_hint: "Certbot Let's Encrypt SSL TLS certificate renewal wildcard automated HTTPS"
last_verified: "2026-05-24"
confidence: "high"
---

# Certbot and Let's Encrypt: Automated SSL Certificate Management

## When to Use
- Enabling HTTPS on web servers without purchasing commercial certificates
- Automating certificate issuance and renewal for multiple domains
- Securing staging/development environments with valid (not self-signed) certificates
- Managing wildcard certificates for multi-subdomain applications

## Standard Pattern

```bash
# --- Install certbot ---
# Ubuntu/Debian
sudo apt update && sudo apt install -y certbot python3-certbot-nginx

# --- Obtain a certificate (Nginx plugin — auto-configures server block) ---
sudo certbot --nginx -d example.com -d www.example.com

# --- Obtain a certificate (standalone — for non-Nginx servers) ---
sudo certbot certonly --standalone -d example.com -d www.example.com

# --- Obtain a wildcard certificate (requires DNS challenge) ---
sudo certbot certonly --manual --preferred-challenges dns \
  -d "*.example.com" -d "example.com"

# --- Certificate files location ---
# /etc/letsencrypt/live/example.com/fullchain.pem  (cert + intermediates)
# /etc/letsencrypt/live/example.com/privkey.pem    (private key)
# /etc/letsencrypt/live/example.com/chain.pem      (intermediate certs)
# /etc/letsencrypt/live/example.com/cert.pem       (certificate only)

# --- Test renewal ---
sudo certbot renew --dry-run

# --- Auto-renewal via systemd timer (installed automatically) ---
sudo systemctl status certbot.timer

# --- Manual renewal hook to reload Nginx ---
# /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
#!/bin/bash
systemctl reload nginx
```

### Docker Compose with Certbot

```yaml
# --- docker-compose.yml ---
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    command: "/bin/sh -c 'while :; do sleep 6h & wait $${!}; nginx -s reload; done & nginx -g \"daemon off;\"'"

  certbot:
    image: certbot/certbot
    volumes:
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"

# --- Initial certificate request ---
# docker compose run --rm certbot certonly --webroot \
#   -w /var/www/certbot -d example.com -d www.example.com
```

### Nginx ACME Challenge Config

```nginx
# Allow certbot webroot verification
server {
    listen 80;
    server_name example.com www.example.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}
```

## Common Mistakes

```bash
# WRONG: Using --standalone with Nginx running — both fight for port 80
sudo certbot certonly --standalone -d example.com
# Error: Problem binding to port 80: Address already in use

# CORRECT: Use the Nginx plugin or webroot mode
sudo certbot --nginx -d example.com
# OR
sudo certbot certonly --webroot -w /var/www/certbot -d example.com
```

```bash
# WRONG: No auto-renewal configured — certificate expires after 90 days
sudo certbot certonly --standalone -d example.com
# ... forgets about it, site goes down in 90 days

# CORRECT: Verify renewal timer is active
sudo certbot renew --dry-run
sudo systemctl enable --now certbot.timer
sudo systemctl list-timers | grep certbot
```

```bash
# WRONG: Forgetting to reload web server after renewal
# Certificate files are updated but Nginx still serves old cert from memory

# CORRECT: Add a renewal hook
echo '#!/bin/bash
systemctl reload nginx' | sudo tee /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
sudo chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
```

## Gotchas
- Let's Encrypt rate limits: 50 certificates per registered domain per week, 5 duplicate certificates per week — test with `--staging` first to avoid hitting limits
- Wildcard certificates require DNS-01 challenge (not HTTP-01) — you need API access to your DNS provider, or manual TXT record creation each renewal
- `certbot renew` only renews certificates expiring within 30 days — if you need immediate renewal, use `certbot renew --force-renewal`
- Certificate files in `/etc/letsencrypt/live/` are symlinks to `/etc/letsencrypt/archive/` — never edit them directly; certbot manages the chain
- `--nginx` plugin modifies your Nginx config — back up before running; it adds SSL directives and may change listen ports
- Revoked or expired certificates are NOT auto-renewed — if a renewal fails silently (DNS issue, port blocked), your site goes down with no alert unless you monitor
- Multi-domain (SAN) certificates are issued as one unit — adding a domain requires reissuing the entire certificate, not just adding a name
- Certbot's webroot mode needs the `.well-known/acme-challenge/` path to be accessible on port 80 — firewalls, CDNs, or auth middleware can block it

## Related
- devops/nginx/reverse-proxy.md
- devops/docker/compose.md
