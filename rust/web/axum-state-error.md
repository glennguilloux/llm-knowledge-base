---
id: "rust-web-axum-state-error"
title: "Axum State Sharing and Error Handling"
language: "rust"
category: "web"
tags: ["axum", "state", "error", "into_response", "extension", "database", "pool"]
version: "1.75+"
retrieval_hint: "axum state sharing error handling IntoResponse database pool AppState extractor"
last_verified: "2026-05-24"
confidence: "high"
---

# Axum State Sharing and Error Handling

## When to Use
- Injecting database pools, config, or shared services into handlers
- Defining custom error types that convert to HTTP responses
- Sharing state across all routes without `Extension` boilerplate
- Building production APIs with structured error responses

## Standard Pattern

```rust
use axum::{
    extract::State,
    http::StatusCode,
    response::{IntoResponse, Response},
    routing::{get, post},
    Json, Router,
};
use serde::{Deserialize, Serialize};
use sqlx::PgPool;

// Application state — holds database pool and config
#[derive(Clone)]
struct AppState {
    db: PgPool,
    jwt_secret: String,
}

// Custom error enum
#[derive(Debug)]
enum AppError {
    NotFound(String),
    BadRequest(String),
    Unauthorized,
    Forbidden,
    Internal(anyhow::Error),
}

// Implement IntoResponse for clean error-to-HTTP conversion
impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let (status, error_code, message) = match self {
            AppError::NotFound(msg) => (
                StatusCode::NOT_FOUND,
                "NOT_FOUND",
                msg,
            ),
            AppError::BadRequest(msg) => (
                StatusCode::BAD_REQUEST,
                "BAD_REQUEST",
                msg,
            ),
            AppError::Unauthorized => (
                StatusCode::UNAUTHORIZED,
                "UNAUTHORIZED",
                "Authentication required".into(),
            ),
            AppError::Forbidden => (
                StatusCode::FORBIDDEN,
                "FORBIDDEN",
                "Insufficient permissions".into(),
            ),
            AppError::Internal(err) => {
                tracing::error!(?err, "internal error");
                (
                    StatusCode::INTERNAL_SERVER_ERROR,
                    "INTERNAL_ERROR",
                    "An internal error occurred".into(),
                )
            }
        };

        let body = Json(serde_json::json!({
            "error": {
                "code": error_code,
                "message": message,
            }
        }));
        (status, body).into_response()
    }
}

// Implement From for common error types
impl From<sqlx::Error> for AppError {
    fn from(err: sqlx::Error) -> Self {
        match err {
            sqlx::Error::RowNotFound => AppError::NotFound("Resource not found".into()),
            _ => AppError::Internal(err.into()),
        }
    }
}

impl From<anyhow::Error> for AppError {
    fn from(err: anyhow::Error) -> Self {
        AppError::Internal(err)
    }
}

// Handler using State extractor and ? operator
async fn get_user(
    State(state): State<AppState>,
    Path(id): Path<i64>,
) -> Result<Json<serde_json::Value>, AppError> {
    let row = sqlx::query!("SELECT id, name, email FROM users WHERE id = $1", id)
        .fetch_optional(&state.db)
        .await?
        .ok_or_else(|| AppError::NotFound(format!("User {} not found", id)))?;

    Ok(Json(serde_json::json!({
        "id": row.id,
        "name": row.name,
        "email": row.email,
    })))
}

async fn create_user(
    State(state): State<AppState>,
    Json(input): Json<CreateUser>,
) -> Result<(StatusCode, Json<serde_json::Value>), AppError> {
    if input.name.is_empty() {
        return Err(AppError::BadRequest("name is required".into()));
    }

    let row = sqlx::query!(
        "INSERT INTO users (name, email) VALUES ($1, $2) RETURNING id",
        input.name,
        input.email
    )
    .fetch_one(&state.db)
    .await?;

    Ok((
        StatusCode::CREATED,
        Json(serde_json::json!({"id": row.id})),
    ))
}

#[derive(Deserialize)]
struct CreateUser {
    name: String,
    email: String,
}

// Health check — always returns 200
async fn health_check() -> &'static str {
    "ok"
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt::init();

    let db = PgPool::connect(&std::env::var("DATABASE_URL")?).await?;
    let jwt_secret = std::env::var("JWT_SECRET")?;

    let state = AppState { db, jwt_secret };

    let app = Router::new()
        .route("/health", get(health_check))
        .route("/users/{id}", get(get_user))
        .route("/users", post(create_user))
        .with_state(state);

    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000").await?;
    axum::serve(listener, app).await?;
    Ok(())
}
```

## Common Mistakes

```rust
// WRONG: Using Extension for state — requires middleware to inject
use axum::Extension;
async fn handler(Extension(state): Extension<AppState>) -> &'static str { "ok" }
// State isn't injected automatically — handler panics at runtime

// CORRECT: Use State extractor with Router::with_state
use axum::extract::State;
async fn handler(State(state): State<AppState>) -> &'static str { "ok" }
let app = Router::new().route("/", get(handler)).with_state(state);

// WRONG: Using std::sync::Mutex in shared state
use std::sync::Mutex;
#[derive(Clone)]
struct AppState {
    cache: Arc<Mutex<HashMap<String, String>>>, // blocks tokio runtime
}

// CORRECT: Use tokio::sync::Mutex for async state
use tokio::sync::Mutex;
#[derive(Clone)]
struct AppState {
    cache: Arc<Mutex<HashMap<String, String>>>, // yields to runtime on lock
}

// WRONG: Returning (StatusCode, String) — no JSON content type
async fn handler() -> (StatusCode, String) {
    (StatusCode::OK, "ok".into()) // client gets text/plain
}

// CORRECT: Return Json for API responses
async fn handler() -> Json<serde_json::Value> {
    Json(serde_json::json!({"status": "ok"}))
}

// WRONG: Logging error details to client
AppError::Internal(err) => {
    (StatusCode::INTERNAL_SERVER_ERROR, format!("DB error: {}", err))
    // Leaks database internals!
}

// CORRECT: Log server-side, return generic message
AppError::Internal(err) => {
    tracing::error!(?err, "internal error");
    (StatusCode::INTERNAL_SERVER_ERROR, "Internal error".to_string())
}
```

## Gotchas
- `Router::with_state()` consumes the router — call it last in the builder chain
- `State` extractor must be the first parameter in the handler — axum evaluates extractors left-to-right
- The `?` operator works with custom errors only if `From<SourceError>` is implemented
- `PgPool` is already `Clone` (it's an `Arc` internally) — wrapping in `Arc` is redundant
- Use `fetch_optional` + `ok_or` for single-row lookups; `fetch_all` for lists
- `anyhow::Error` doesn't implement `IntoResponse` — wrap it in your custom error type
- Health check endpoints should NOT require state extraction to work even if DB is down
- axum 0.7+ uses `Router::with_state` instead of `Extension` for type-safe state

## Related
- rust/web/axum-deep.md
- rust/web/axum-middleware.md
- rust/db/sqlx-patterns.md
