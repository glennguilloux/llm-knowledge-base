---
id: "rust-web-axum"
title: "HTTP Server with Axum"
language: "rust"
category: "web"
tags: ["axum", "http", "server", "rest", "routing", "tower", "extractor"]
version: "1.75+"
retrieval_hint: "axum HTTP server router handler extractor middleware tower REST API"
last_verified: "2026-05-24"
confidence: "high"
---

# HTTP Server with Axum

## When to Use
- Building REST APIs in Rust
- Creating microservices with type-safe request handling
- Leveraging Tower middleware for cross-cutting concerns
- Needing extractors for automatic request parsing

## Standard Pattern

```rust
use axum::{
    extract::{Path, Query, State},
    http::StatusCode,
    middleware,
    response::IntoResponse,
    routing::{delete, get, post},
    Json, Router,
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::Mutex;
use tower_http::trace::TraceLayer;

// Shared application state
#[derive(Clone)]
struct AppState {
    db: Arc<Mutex<Vec<Item>>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Item {
    id: u64,
    name: String,
    price: f64,
}

#[derive(Deserialize)]
struct CreateItem {
    name: String,
    price: f64,
}

#[derive(Deserialize)]
struct Pagination {
    page: Option<u32>,
    per_page: Option<u32>,
}

// Custom error type
#[derive(Debug)]
enum AppError {
    NotFound,
    BadRequest(String),
    Internal(String),
}

impl IntoResponse for AppError {
    fn into_response(self) -> axum::response::Response {
        let (status, message) = match self {
            AppError::NotFound => (StatusCode::NOT_FOUND, "Not found".into()),
            AppError::BadRequest(msg) => (StatusCode::BAD_REQUEST, msg),
            AppError::Internal(msg) => {
                eprintln!("Internal error: {}", msg);
                (StatusCode::INTERNAL_SERVER_ERROR, "Internal error".into())
            }
        };
        (status, Json(serde_json::json!({"error": message}))).into_response()
    }
}

// Handlers
async fn list_items(
    State(state): State<AppState>,
    Query(pagination): Query<Pagination>,
) -> Json<Vec<Item>> {
    let db = state.db.lock().await;
    let page = pagination.page.unwrap_or(0);
    let per_page = pagination.per_page.unwrap_or(10) as usize;
    let items: Vec<Item> = db
        .iter()
        .skip((page as usize) * per_page)
        .take(per_page)
        .cloned()
        .collect();
    Json(items)
}

async fn get_item(
    State(state): State<AppState>,
    Path(id): Path<u64>,
) -> Result<Json<Item>, AppError> {
    let db = state.db.lock().await;
    db.iter()
        .find(|i| i.id == id)
        .cloned()
        .map(Json)
        .ok_or(AppError::NotFound)
}

async fn create_item(
    State(state): State<AppState>,
    Json(input): Json<CreateItem>,
) -> Result<(StatusCode, Json<Item>), AppError> {
    if input.name.is_empty() {
        return Err(AppError::BadRequest("name is required".into()));
    }
    let mut db = state.db.lock().await;
    let id = db.len() as u64 + 1;
    let item = Item {
        id,
        name: input.name,
        price: input.price,
    };
    db.push(item.clone());
    Ok((StatusCode::CREATED, Json(item)))
}

async fn delete_item(
    State(state): State<AppState>,
    Path(id): Path<u64>,
) -> Result<StatusCode, AppError> {
    let mut db = state.db.lock().await;
    let len_before = db.len();
    db.retain(|i| i.id != id);
    if db.len() == len_before {
        Err(AppError::NotFound)
    } else {
        Ok(StatusCode::NO_CONTENT)
    }
}

// Middleware example: logging
async fn log_request(
    req: axum::http::Request<axum::body::Body>,
    next: middleware::Next,
) -> impl IntoResponse {
    let method = req.method().clone();
    let uri = req.uri().clone();
    let response = next.run(req).await;
    println!("{} {} -> {}", method, uri, response.status());
    response
}

#[tokio::main]
async fn main() {
    tracing_subscriber::init();

    let state = AppState {
        db: Arc::new(Mutex::new(vec![])),
    };

    let app = Router::new()
        .route("/items", get(list_items).post(create_item))
        .route("/items/{id}", get(get_item).delete(delete_item))
        .layer(TraceLayer::new_for_http())
        .layer(middleware::from_fn(log_request))
        .with_state(state);

    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000")
        .await
        .unwrap();
    println!("Listening on :3000");
    axum::serve(listener, app).await.unwrap();
}
```

## Common Mistakes

```rust
// WRONG: Using synchronous blocking in handlers
async fn handler() -> Json<Value> {
    let data = std::fs::read_to_string("data.json").unwrap(); // blocks runtime!
    Json(serde_json::from_str(&data).unwrap())
}

// CORRECT: Use tokio::fs for async I/O
async fn handler() -> Result<Json<Value>, AppError> {
    let data = tokio::fs::read_to_string("data.json").await
        .map_err(|e| AppError::Internal(e.to_string()))?;
    Ok(Json(serde_json::from_str(&data)
        .map_err(|e| AppError::BadRequest(e.to_string()))?))
}

// WRONG: Sharing state with Arc<Mutex<T>> from std
use std::sync::Mutex; // Blocks executor thread

// CORRECT: Use tokio::sync::Mutex for async state
use tokio::sync::Mutex;

// WRONG: Returning raw strings as responses
async fn handler() -> String { "OK".into() }

// CORRECT: Use proper status codes and response types
async fn handler() -> impl IntoResponse {
    (StatusCode::OK, "OK")
}

// WRONG: Not handling extraction errors
async fn handler(Json(body): Json<CreateItem>) -> impl IntoResponse {
    // If JSON is malformed, returns 422 automatically — that's fine
    // But if you need custom error handling:
    // Use Result<Json<T>, Rejection>
}
```

## Gotchas
- Extractors are evaluated left to right — put `State` first, `Json` last (body is consumed)
- Path parameters use `{name}` syntax (axum 0.7+), not `:name`
- `Json` extractor returns 422 on deserialization failure — customize with `Result<Json<T>, Rejection>`
- Tower middleware runs bottom-to-top for requests (last `.layer()` runs first)
- `Router::with_state` consumes the router — do it last
- Use `nest()` for grouping routes under a prefix
- `serve()` replaces the older `axum::Server::bind().serve()` (deprecated)
- Handlers can return any type implementing `IntoResponse` — tuples, Json, StatusCode, etc.

## Related
- rust/stdlib/serde.md
- rust/concurrency/async-tokio.md
- rust/stdlib/result-option.md
