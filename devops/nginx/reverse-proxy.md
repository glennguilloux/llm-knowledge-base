---
id: "devops-nginx-reverse-proxy"
title: "Nginx Reverse Proxy, Load Balancing, and SSL Termination"
language: "shell"
category: "devops"
subcategory: "web-server"
tags: ["nginx", "reverse-proxy", "load-balancing", "ssl", "caching", "rate-limiting"]
version: "latest"
retrieval_hint: "Nginx reverse proxy upstream proxy_pass WebSocket caching rate limiting SSL termination load balancing"
last_verified: "2026-05-22"
confidence: "high"
---

# Nginx Reverse Proxy, Load Balancing, and SSL Termination

## When to Use
- Fronting application servers (Node, Python, Go) with a battle-tested HTTP layer
- SSL/TLS termination before traffic reaches backend services
- Load balancing across multiple backend instances
- Rate limiting, caching, and request transformation at the edge

## Standard Pattern

```nginx
# --- /etc/nginx/nginx.conf ---
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;

events {
    worker_connections 2048;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] '
                    '"$request" $status $body_bytes_sent '
                    '"$http_referer" "$http_user_agent"';

    access_log /var/log/nginx/access.log main;

    # --- Upstream backend pool ---
    upstream app_backend {
        least_conn;
        server 127.0.0.1:8000 weight=3;
        server 127.0.0.1:8001 weight=2;
        server 127.0.0.1:8002 backup;
        keepalive 32;
    }

    # --- Rate limiting ---
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_conn_zone $binary_remote_addr zone=conn:10m;

    # --- Caching ---
    proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=app_cache:10m
                     max_size=1g inactive=60m use_temp_path=off;

    # --- HTTP to HTTPS redirect ---
    server {
        listen 80;
        server_name example.com;
        return 301 https://$host$request_uri;
    }

    # --- Main HTTPS server ---
    server {
        listen 443 ssl http2;
        server_name example.com;

        ssl_certificate     /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols       TLSv1.2 TLSv1.3;
        ssl_ciphers         HIGH:!aNULL:!MD5;
        ssl_session_cache   shared:SSL:10m;
        ssl_session_timeout 10m;

        # Security headers
        add_header X-Frame-Options DENY always;
        add_header X-Content-Type-Options nosniff always;
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        # API endpoints with rate limiting
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            limit_conn conn 50;

            proxy_pass http://app_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            proxy_connect_timeout 5s;
            proxy_read_timeout 30s;
            proxy_send_timeout 30s;
        }

        # Static files with caching
        location /static/ {
            alias /var/www/static/;
            expires 30d;
            add_header Cache-Control "public, immutable";
            access_log off;
        }

        # WebSocket support
        location /ws/ {
            proxy_pass http://app_backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_read_timeout 86400s;
        }

        # Proxy cache for GET requests
        location / {
            proxy_pass http://app_backend;
            proxy_cache app_cache;
            proxy_cache_valid 200 10m;
            proxy_cache_valid 404 1m;
            proxy_cache_use_stale error timeout updating;
            add_header X-Cache-Status $upstream_cache_status;
        }
    }
}
```

## Common Mistakes

```nginx
# WRONG: Missing Host and X-Forwarded-For headers — backend sees 127.0.0.1 as client
location /api/ {
    proxy_pass http://app_backend;
}

# CORRECT: Forward real client information
location /api/ {
    proxy_pass http://app_backend;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

```nginx
# WRONG: WebSocket location without upgrade headers — connection falls back to polling
location /ws/ {
    proxy_pass http://app_backend;
}

# CORRECT: Enable WebSocket upgrade
location /ws/ {
    proxy_pass http://app_backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 86400s;
}
```

```nginx
# WRONG: Rate limiting without burst — legitimate traffic gets 503'd
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

location /api/ {
    limit_req zone=api;
    proxy_pass http://app_backend;
}

# CORRECT: Allow burst for short spikes
location /api/ {
    limit_req zone=api burst=20 nodelay;
    proxy_pass http://app_backend;
}
```

## Gotchas
- `proxy_pass` with a trailing slash strips the location prefix; without it, the full URI is forwarded — `location /api/` + `proxy_pass http://backend/` sends `/foo` not `/api/foo`
- `nginx -t` validates syntax but NOT runtime behavior — a valid config can still cause 502s if backends are down
- `keepalive 32` on upstream enables persistent connections — your backend must support HTTP/1.1 keep-alive or connections will be silently dropped
- Rate limiting uses `$binary_remote_addr` by default — behind a load balancer, use `$http_x_forwarded_for` or all clients share one bucket
- `ssl_session_cache shared:SSL:10m` is shared across all worker processes — too small causes SSL handshake overhead; 10MB handles ~40,000 sessions
- `proxy_cache` serves stale content during backend failures only with `proxy_cache_use_stale error timeout` — without it, backend errors propagate to clients
- `limit_req burst=20 nodelay` processes burst requests immediately rather than queuing — this means no delay but still rejects above the burst limit
- Adding a new `server_name` requires `nginx -s reload` — a `restart` drops existing connections; `reload` gracefully transitions

## Related
- devops/docker/compose.md
- devops/terraform/basics.md
- devops/ssl-tls/certbot-letsencrypt.md
