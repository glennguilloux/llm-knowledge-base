---
id: "rust-web-axum-deep"
title: "Axum Deep Dive: Extractors, Middleware, State"
language: "rust"
category: "web"
subcategory: "api-framework"
tags: ["rust", "axum", "extractor", "middleware", "state", "tower", "handler"]
version: "1.75+"
retrieval_hint: "Axum extractor middleware state tower handler routing JSON body"
last_verified: "2026-05-24"
confidence: "high"
---

# Axum Deep Dive: Extractors, Middleware, State

## When to Use
- Building REST APIs in Rust with type-safe extractors
- Shared application state (database, config) across handlers
- Middleware for logging, auth, CORS
- Production-grade async HTTP services

## Standard Pattern

```rust
use axum::{
    extract::{Path, Query, State, Json},
    http::StatusCode,
    middleware::{self, Next},
    response::IntoResponse,
    routing::{get, post, delete},
    Router,
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tower_http::cors::CorsLayer;

// --- Shared state ---
#[derive(Clone)]
struct AppState {
    db: Arc<Database>,
    config: Arc<Config>,
}

// --- Handlers with extractors ---
#[derive(Deserialize)]
struct Pagination {
    page: Option<u32>,
    limit: Option<u32>,
}

#[derive(Serialize)]
struct User {
    id: i64,
    name: String,
    email: String,
}

async fn list_users(
    State(state): State<AppState>,
    Query(pagination): Query<Pagination>,
) -> Result<Json<Vec<User>>, AppError> {
    let page = pagination.page.unwrap_or(0);
    let limit = pagination.limit.unwrap_or(20).min(100);

    let users = state.db.list_users(page, limit).await?;
    Ok(Json(users))
}

async fn get_user(
    State(state): State<AppState>,
    Path(id): Path<i64>,
) -> Result<Json<User>, AppError> {
    let user = state.db.get_user(id).await?
        .ok_or(AppError::NotFound { resource: "User".into(), id })?;
    Ok(Json(user))
}

#[derive(Deserialize)]
struct CreateUser {
    name: String,
    email: String,
}

async fn create_user(
    State(state): State<AppState>,
    Json(input): Json<CreateUser>,
) -> Result<(StatusCode, Json<User>), AppError> {
    let user = state.db.create_user(&input.name, &input.email).await?;
    Ok((StatusCode::CREATED, Json(user)))
}

// --- Auth middleware ---
async fn auth_middleware(
    headers: axum::http::HeaderMap,
    request: axum::extract::Request,
    next: Next,
) -> Result<impl IntoResponse, AppError> {
    let token = headers
        .get("Authorization")
        .and_then(|v| v.to_str().ok())
        .and_then(|v| v.strip_prefix("Bearer "))
        .ok_or(AppError::Unauthorized)?;

    let claims = verify_jwt(token)?;
    let response = next.run(request).await;
    Ok(response)
}

// --- Router setup ---
fn app(state: AppState) -> Router {
    let api = Router::new()
        .route("/users", get(list_users).post(create_user))
        .route("/users/{id}", get(get_user).delete(delete_user))
        .route_layer(middleware::from_fn(auth_middleware));

    Router::new()
        .nest("/api/v1", api)
        .route("/health", get(|| async { "ok" }))
        .layer(CorsLayer::permissive())
        .with_state(state)
}

// --- Main ---
#[tokio::main]
async fn main() {
    let state = AppState {
        db: Arc::new(Database::connect().await.unwrap()),
        config: Arc::new(Config::load().unwrap()),
    };

    let listener = tokio::net::TcpListener::bind("0.0.0.0:8080").await.unwrap();
    axum::serve(listener, app(state)).await.unwrap();
}
```

## Common Mistakes

```rust
// WRONG: Extractor order wrong (body must be last)
async fn handler(
    Json(body): Json<CreateUser>,  // Consumes request body
    State(state): State<AppState>,  // Can't access body after
) -> impl IntoResponse { ... }

// CORRECT: Body extractor last
async fn handler(
    State(state): State<AppState>,
    Json(body): Json<CreateUser>,
) -> impl IntoResponse { ... }

// WRONG: Not using Arc for shared state
#[derive(Clone)]
struct AppState {
    db: Database,  // Cloned per request — expensive!
}

// CORRECT: Use Arc for shared resources
#[derive(Clone)]
struct AppState {
    db: Arc<Database>,
}

// WRONG: Forgetting route_layer order
Router::new()
    .route_layer(middleware::from_fn(auth))  // Applied before routes!
    .route("/users", get(list_users))

// CORRECT: Routes first, then layers
Router::new()
    .route("/users", get(list_users))
    .route_layer(middleware::from_fn(auth))  // Applied after routes
```

## Gotchas
- Extractors are evaluated left to right — body extractors must be last
- `State` is a clone of `Arc` — cheap to extract
- `Json<T>` returns 422 on deserialization failure (not 400)
- `Path<i64>` extracts a single path param; `Path<(i64, String)>` extracts multiple
- Middleware runs in order: first added = outermost (runs first)
- `tower_http` provides CORS, compression, tracing middleware
- `Router::with_state()` consumes the router and binds the state type
- Use `#[axum::debug_handler]` for better error messages during development

## Real-World Example

### Full Axum API with Shared State, Middleware, and Error Handling

```rust
use axum::{
    extract::{Path, State},
    http::StatusCode,
    response::Json,
    routing::{get, post},
    Router,
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::Mutex;
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Item {
    id: String,
    name: String,
    quantity: u32,
}

type AppState = Arc<Mutex<Vec<Item>>>;

async fn list_items(State(state): State<AppState>) -> Json<Vec<Item>> {
    let items = state.lock().await;
    Json(items.clone())
}

async fn create_item(
    State(state): State<AppState>,
    Json(body): Json<CreateItemRequest>,
) -> Result<Json<Item>, (StatusCode, String)> {
    if body.name.is_empty() {
        return Err((StatusCode::BAD_REQUEST, "name is required".into()));
    }
    let item = Item {
        id: Uuid::new_v4().to_string(),
        name: body.name,
        quantity: body.quantity.unwrap_or(1),
    };
    state.lock().await.push(item.clone());
    Ok(Json(item))
}

async fn get_item(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Result<Json<Item>, StatusCode> {
    let items = state.lock().await;
    items
        .iter()
        .find(|i| i.id == id)
        .cloned()
        .map(Json)
        .ok_or(StatusCode::NOT_FOUND)
}

#[derive(Deserialize)]
struct CreateItemRequest {
    name: String,
    quantity: Option<u32>,
}

#[tokio::main]
async fn main() {
    let state: AppState = Arc::new(Mutex::new(Vec::new()));
    let app = Router::new()
        .route("/items", get(list_items).post(create_item))
        .route("/items/:id", get(get_item))
        .with_state(state);

    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000").await.unwrap();
    axum::serve(listener, app).await.unwrap();
}
```

## Related
- rust/web/axum-basics.md
- rust/stdlib/error-crates.md
- rust/concurrency/async-tokio.md
