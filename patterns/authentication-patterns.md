---
id: "patterns-authentication-patterns"
title: "Authentication Patterns: Sessions, Tokens, OAuth2, and API Keys"
language: "multi"
category: "patterns"
tags: ["authentication", "sessions", "tokens", "oauth2", "api-keys", "jwt", "pkce"]
version: "n/a"
retrieval_hint: "authentication patterns session-based token-based OAuth2 flows authorization code client credentials PKCE API key patterns token refresh strategies"
last_verified: "2026-05-24"
confidence: "high"
---

# Authentication Patterns: Sessions, Tokens, OAuth2, and API Keys

## When to Use
- Choosing an authentication strategy for your application
- Implementing OAuth2 flows
- Managing API keys
- Understanding session vs token-based auth
- Implementing token refresh strategies

## Standard Pattern

```markdown
# Session-Based Authentication (Server-Side)
Best for: Traditional web apps, server-rendered pages

Flow:
1. User submits login form (POST /login)
2. Server validates credentials
3. Server creates session (stores in DB/cache)
4. Server sets session ID in HTTP-only cookie
5. Browser sends cookie with each request
6. Server looks up session to identify user

Pros: Simple, secure (HTTP-only cookie), easy to invalidate
Cons: Server-side state, doesn't scale horizontally without shared store

# Token-Based Authentication (JWT)
Best for: SPAs, mobile apps, microservices, APIs

Flow:
1. User submits login form (POST /auth/login)
2. Server validates credentials
3. Server creates JWT (signed, contains user claims)
4. Server returns JWT to client
5. Client stores JWT (memory > localStorage > cookie)
6. Client sends JWT in Authorization header
7. Server verifies JWT signature and extracts claims

JWT Structure: header.payload.signature
- Header: algorithm (HS256/RS256), type (JWT)
- Payload: sub, exp, iat, roles, custom claims
- Signature: HMAC or RSA signature

Pros: Stateless, scalable, works across domains
Cons: Cannot revoke individual tokens, token size, must handle refresh

# OAuth2 Flows

## Authorization Code Flow (with PKCE) — RECOMMENDED for SPAs and mobile
1. Client generates code_verifier and code_challenge
2. Redirect to authorization server with code_challenge
3. User authenticates and authorizes
4. Authorization server redirects with authorization code
5. Client exchanges code + code_verifier for tokens
6. Client uses access_token for API calls

## Authorization Code Flow (with client secret) — for server-side apps
1. Redirect to authorization server
2. User authenticates and authorizes
3. Authorization server redirects with authorization code
4. Server exchanges code + client_secret for tokens
5. Server uses access_token for API calls

## Client Credentials Flow — for service-to-service
1. Client sends client_id + client_secret to token endpoint
2. Authorization server returns access_token
3. Client uses access_token for API calls
4. No user context — machine-to-machine

## Device Code Flow — for input-constrained devices
1. Device requests device_code and user_code
2. User visits URL and enters user_code on another device
3. Device polls for token
4. User authorizes on the other device
5. Device receives access_token

# API Key Patterns
Best for: Service-to-service, third-party API access

1. Generate API key: secrets.token_urlsafe(32)
2. Store hashed version in database
3. Client sends key in header: X-API-Key: <key>
4. Server hashes provided key and compares with stored hash
5. Support key rotation and revocation

# Token Refresh Strategy
1. Access token: short-lived (15-60 minutes)
2. Refresh token: long-lived (days/weeks), stored securely
3. When access token expires, use refresh token to get new access token
4. Refresh token rotation: new refresh token issued with each refresh
5. If refresh token is reused, revoke all tokens (theft detection)
```

## Common Mistakes

```markdown
# WRONG: Storing JWT in localStorage (XSS vulnerability)
localStorage.setItem('token', jwt);
// Any JavaScript on the page can read this!

# CORRECT: Store in memory (best) or HTTP-only cookie
# Memory: let token = response.token; (lost on page refresh)
# Cookie: Set-Cookie: token=xxx; HttpOnly; Secure; SameSite=Strict

# WRONG: Using Authorization Code flow without PKCE for SPAs
# Client secret cannot be stored securely in a browser!

# CORRECT: Use PKCE (Proof Key for Code Exchange)
# code_challenge = BASE64URL(SHA256(code_verifier))

# WRONG: Long-lived access tokens without refresh
# If token is stolen, attacker has access until it expires!

# CORRECT: Short-lived access tokens + refresh tokens
# Access: 15 minutes, Refresh: 7 days with rotation

# WRONG: Storing API keys in plain text in database
db.store('api_key', plaintext_key);

# CORRECT: Store hashed API keys
db.store('api_key_hash', hashlib.sha256(key.encode()).hexdigest());

# WRONG: Not validating JWT signature
# Just decoding the payload without verifying the signature!

# CORRECT: Always verify signature and claims
jwt.decode(token, secret, algorithms=['HS256'], options={
    'verify_exp': True,
    'verify_iat': True,
    'require': ['exp', 'sub']
});

# WRONG: Using HS256 (symmetric) when RS256 (asymmetric) is needed
# HS256: same key signs and verifies — all servers know the secret
# RS256: private key signs, public key verifies — only auth server has private key

# CORRECT: Use RS256 for microservices (only auth server signs)
```

## Gotchas
- **Session vs Token**: Sessions are stateful (server stores data). Tokens are stateless (all data in the token).
- **JWT cannot be revoked** without a blacklist. Use short expiry + refresh tokens.
- **PKCE is mandatory** for public clients (SPAs, mobile apps) per OAuth 2.1.
- **HTTP-only cookies** prevent XSS from reading tokens. Use `Secure` and `SameSite` flags.
- **Refresh token rotation** detects theft: if a refresh token is reused, revoke all tokens.
- **API keys should be hashed** before storage, just like passwords.
- **RS256 (asymmetric)** is better than HS256 (symmetric) for distributed systems.
- **Client Credentials** flow has no user context. Use for service-to-service only.
- **Device Code** flow is for smart TVs, CLI tools, and other input-constrained devices.
- **Token storage hierarchy**: Memory > HTTP-only cookie > localStorage (least secure).

## Related
- crypto/jwt-tokens.md
- crypto/hmac.md
- crypto/key-derivation.md
- security/web-security-basics.md
