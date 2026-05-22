---
id: "rust-web-axum-auth"
title: "Authentication in Axum"
language: "rust"
category: "web"
tags: ["axum", "auth", "jwt", "session", "middleware", "tower-cookies", "extractor"]
version: "1.75+"
retrieval_hint: "axum JWT authentication session cookies middleware extractor protected routes"
last_verified: "2026-05-22"
confidence: "high"
---

# Authentication in Axum

## When to Use
- Protecting API routes with JWT tokens
- Implementing session-based auth with cookies
- Building login/logout flows with secure cookies
- Extracting user identity in handlers

## Standard Pattern

```rust
use axum::{
    extract::{FromRequestParts, Request, State},
    http::{header, request::Parts, StatusCode},
    middleware::{self, Next},
    response::{IntoResponse, Response},
    routing::{get, post},
    Json, Router,
};
use jsonwebtoken::{decode, encode, DecodingKey, EncodingKey, Header, Validation};
use serde::{Deserialize, Serialize};
use time::{Duration, OffsetDateTime};
use tower_cookies::{Cookie, CookieManagerLayer, Cookies};

// JWT claims
#[derive(Debug, Serialize, Deserialize, Clone)]
struct Claims {
    sub: String,       // user ID
    email: String,
    exp: usize,        // expiration timestamp
    iat: usize,        // issued at
}

// Auth extractor — extracts claims from Authorization header
#[derive(Clone)]
struct AuthUser {
    user_id: String,
    email: String,
}

impl<S> FromRequestParts<S> for AuthUser
where
    S: Send + Sync,
{
    type Rejection = Response;

    async fn from_request_parts(
        parts: &mut Parts,
        _state: &S,
    ) -> Result<Self, Self::Rejection> {
        let auth_header = parts
            .headers
            .get(header::AUTHORIZATION)
            .and_then(|v| v.to_str().ok())
            .ok_or_else(|| {
                (StatusCode::UNAUTHORIZED, "Missing Authorization header")
                    .into_response()
            })?;

        let token = auth_header
            .strip_prefix("Bearer ")
            .ok_or_else(|| {
                (StatusCode::UNAUTHORIZED, "Invalid Authorization format")
                    .into_response()
            })?;

        let jwt_secret = std::env::var("JWT_SECRET")
            .unwrap_or_else(|_| "secret".into());

        let token_data = decode::<Claims>(
            token,
            &DecodingKey::from_secret(jwt_secret.as_bytes()),
            &Validation::default(),
        )
        .map_err(|_| {
            (StatusCode::UNAUTHORIZED, "Invalid or expired token")
                .into_response()
        })?;

        Ok(AuthUser {
            user_id: token_data.claims.sub,
            email: token_data.claims.email,
        })
    }
}

// Login handler — issues JWT and sets cookie
async fn login(
    State(state): State<AppState>,
    Json(input): Json<LoginRequest>,
) -> Result<Json<serde_json::Value>, (StatusCode, String)> {
    // Verify credentials (simplified — use proper password hashing)
    let user = verify_credentials(&state.db, &input.email, &input.password)
        .await
        .map_err(|_| (StatusCode::UNAUTHORIZED, "Invalid credentials".into()))?;

    let claims = Claims {
        sub: user.id.to_string(),
        email: user.email.clone(),
        exp: (OffsetDateTime::now_utc() + Duration::hours(24)).unix_timestamp() as usize,
        iat: OffsetDateTime::now_utc().unix_timestamp() as usize,
    };

    let token = encode(
        &Header::default(),
        &claims,
        &EncodingKey::from_secret(state.jwt_secret.as_bytes()),
    )
    .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;

    Ok(Json(serde_json::json!({
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
        }
    })))
}

// Protected handler — uses AuthUser extractor
async fn get_profile(
    auth: AuthUser,
) -> Json<serde_json::Value> {
    Json(serde_json::json!({
        "user_id": auth.user_id,
        "email": auth.email,
    }))
}

// Session-based auth using tower-cookies
async fn login_with_session(
    cookies: Cookies,
    State(state): State<AppState>,
    Json(input): Json<LoginRequest>,
) -> Result<Json<serde_json::Value>, (StatusCode, String)> {
    let user = verify_credentials(&state.db, &input.email, &input.password)
        .await
        .map_err(|_| (StatusCode::UNAUTHORIZED, "Invalid credentials".into()))?;

    let claims = Claims {
        sub: user.id.to_string(),
        email: user.email.clone(),
        exp: (OffsetDateTime::now_utc() + Duration::hours(24)).unix_timestamp() as usize,
        iat: OffsetDateTime::now_utc().unix_timestamp() as usize,
    };

    let token = encode(
        &Header::default(),
        &claims,
        &EncodingKey::from_secret(state.jwt_secret.as_bytes()),
    )
    .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;

    let mut cookie = Cookie::new("session", token);
    cookie.set_http_only(true);
    cookie.set_secure(true);
    cookie.set_same_site(tower_cookies::cookie::SameSite::Strict);
    cookie.set_path("/");
    cookies.add(cookie);

    Ok(Json(serde_json::json!({"status": "logged_in"})))
}

async fn logout(cookies: Cookies) -> impl IntoResponse {
    cookies.remove(Cookie::build("session").path("/"));
    Json(serde_json::json!({"status": "logged_out"}))
}

// Middleware-based auth for route groups
async fn require_auth(
    State(state): State<AppState>,
    req: Request,
    next: Next,
) -> Response {
    let auth_header = req
        .headers()
        .get(header::AUTHORIZATION)
        .and_then(|v| v.to_str().ok());

    match auth_header {
        Some(header) if header.starts_with("Bearer ") => {
            let token = &header[7..];
            let result = decode::<Claims>(
                token,
                &DecodingKey::from_secret(state.jwt_secret.as_bytes()),
                &Validation::default(),
            );
            match result {
                Ok(_) => next.run(req).await,
                Err(_) => StatusCode::UNAUTHORIZED.into_response(),
            }
        }
        _ => StatusCode::UNAUTHORIZED.into_response(),
    }
}

#[derive(Deserialize)]
struct LoginRequest {
    email: String,
    password: String,
}

#[derive(Clone)]
struct AppState {
    db: sqlx::PgPool,
    jwt_secret: String,
}

#[tokio::main]
async fn main() {
    let state = AppState {
        db: sqlx::PgPool::connect(&std::env::var("DATABASE_URL").unwrap()).await.unwrap(),
        jwt_secret: std::env::var("JWT_SECRET").unwrap_or_else(|_| "secret".into()),
    };

    // Public routes
    let public = Router::new()
        .route("/login", post(login))
        .route("/login-session", post(login_with_session));

    // Protected routes — require auth
    let protected = Router::new()
        .route("/profile", get(get_profile))
        .route("/logout", post(logout))
        .layer(middleware::from_fn_with_state(
            state.clone(),
            require_auth,
        ));

    let app = Router::new()
        .merge(public)
        .merge(protected)
        .layer(CookieManagerLayer::new())
        .with_state(state);

    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000")
        .await
        .unwrap();
    axum::serve(listener, app).await.unwrap();
}
```

## Common Mistakes

```rust
// WRONG: Hardcoding JWT secret in source code
let jwt_secret = "my-super-secret-key"; // Exposed in git history!

// CORRECT: Load from environment
let jwt_secret = std::env::var("JWT_SECRET")
    .expect("JWT_SECRET environment variable must be set");

// WRONG: Not validating token expiration
let mut validation = Validation::default();
validation.validate_exp = false; // Tokens never expire — security risk!

// CORRECT: Use default validation which checks exp
let token_data = decode::<Claims>(
    token,
    &DecodingKey::from_secret(secret.as_bytes()),
    &Validation::default(), // validates exp by default
)?;

// WRONG: Storing sensitive data in JWT claims
let claims = Claims {
    password: input.password, // JWT is base64, not encrypted!
    ..Default::default()
};

// CORRECT: Store only non-sensitive identifiers
let claims = Claims {
    sub: user.id.to_string(), // user ID only
    email: user.email,
    exp: expiry,
    iat: now,
};
```

## Gotchas
- JWT tokens are base64-encoded, not encrypted — never store passwords or secrets in claims
- The `jsonwebtoken` crate validates `exp` by default — set `validation.validate_exp = false` only for testing
- `FromRequestParts` (not `FromRequest`) is for extractors that don't consume the body — auth headers don't need the body
- `tower-cookies` must be added as a layer (`CookieManagerLayer`) before routes that use `Cookies`
- For production, set `cookie.set_secure(true)` — requires HTTPS; disable only for local dev
- Session cookies should use `SameSite::Strict` or `SameSite::Lax` to prevent CSRF
- JWT secret must be at least 256 bits (32 bytes) for HS256
- In middleware-based auth, the user info isn't available to handlers unless you add it via `Extension` — prefer `AuthUser` extractor for handler-level auth

## Related
- rust/web/axum.md
- rust/web/axum-middleware.md
- rust/web/axum-state-error.md
- rust/stdlib/serde.md
