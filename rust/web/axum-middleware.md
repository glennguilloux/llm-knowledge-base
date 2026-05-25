---
id: "rust-web-axum-middleware"
title: "Axum Middleware and Layers"
language: "rust"
category: "web"
tags: ["axum", "middleware", "tower", "cors", "tracing", "layer", "from_fn"]
version: "1.75+"
retrieval_hint: "axum middleware from_fn layer cors tracing tower request response"
last_verified: "2026-05-24"
confidence: "high"
---

# Axum Middleware and Layers

## When to Use
- Cross-cutting concerns: logging, auth, CORS, rate limiting
- Modifying requests before handlers or responses after handlers
- Composing reusable behavior via Tower layers
- Adding tracing/metrics to every request

## Standard Pattern

```rust
use axum::{
    http::{HeaderValue, Method, StatusCode, Request},
    middleware::{self, Next},
    response::{IntoResponse, Response},
    routing::get,
    Router,
};
use tower_http::{
    cors::{Any, CorsLayer},
    trace::TraceLayer,
};
use tracing::Span;

// Simple logging middleware using from_fn
async fn logging_middleware(
    req: Request<axum::body::Body>,
    next: Next,
) -> Response {
    let method = req.method().clone();
    let uri = req.uri().clone();
    let start = std::time::Instant::now();

    let response = next.run(req).await;

    let duration = start.elapsed();
    tracing::info!(
        method = %method,
        uri = %uri,
        status = %response.status(),
        duration_ms = duration.as_millis(),
        "request completed"
    );
    response
}

// Request ID middleware — injects header into request
async fn request_id_middleware(
    mut req: Request<axum::body::Body>,
    next: Next,
) -> Response {
    let id = uuid::Uuid::new_v4().to_string();
    req.headers_mut().insert(
        "x-request-id",
        HeaderValue::from_str(&id).unwrap(),
    );
    let mut response = next.run(req).await;
    response.headers_mut().insert(
        "x-request-id",
        HeaderValue::from_str(&id).unwrap(),
    );
    response
}

// Error-handling middleware — catches panics gracefully
async fn error_handler(
    req: Request<axum::body::Body>,
    next: Next,
) -> Response {
    let response = next.run(req).await;
    if response.status().is_server_error() {
        tracing::error!("server error: {}", response.status());
    }
    response
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();

    // CORS configuration
    let cors = CorsLayer::new()
        .allow_origin("http://localhost:3000".parse::<HeaderValue>().unwrap())
        .allow_methods([Method::GET, Method::POST, Method::DELETE])
        .allow_headers(Any);

    let app = Router::new()
        .route("/", get(|| async { "Hello" }))
        // Middleware runs bottom-to-top for requests:
        // 1. error_handler (outermost)
        // 2. request_id_middleware
        // 3. logging_middleware
        // 4. cors
        // 5. handler (innermost)
        .layer(middleware::from_fn(error_handler))
        .layer(middleware::from_fn(request_id_middleware))
        .layer(middleware::from_fn(logging_middleware))
        .layer(cors)
        .layer(TraceLayer::new_for_http());

    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000")
        .await
        .unwrap();
    axum::serve(listener, app).await.unwrap();
}
```

## Common Mistakes

```rust
// WRONG: Applying middleware in wrong order — CORS must be outermost
let app = Router::new()
    .route("/", get(handler))
    .layer(CorsLayer::new())           // runs last for requests
    .layer(middleware::from_fn(auth));  // runs first — CORS headers missing on auth errors

// CORRECT: Put CORS outermost (first in chain = runs last for requests)
let app = Router::new()
    .route("/", get(handler))
    .layer(middleware::from_fn(auth))   // runs first for requests
    .layer(CorsLayer::new());           // adds CORS headers to all responses

// WRONG: Calling next.run() multiple times
async fn middleware(req: Request, next: Next) -> Response {
    let r1 = next.run(req).await;  // consumes body
    let r2 = next.run(req).await;  // ERROR: body already consumed
    r1
}

// CORRECT: Call next.run() exactly once
async fn middleware(req: Request, next: Next) -> Response {
    let response = next.run(req).await;
    // post-processing here
    response
}

// WRONG: Cloning request for middleware — body is not Clone
async fn middleware(req: Request, next: Next) -> Response {
    let req2 = req.clone(); // ERROR: Body is not Clone
    next.run(req).await
}

// CORRECT: Extract what you need before consuming the request
async fn middleware(req: Request, next: Next) -> Response {
    let method = req.method().clone();
    let uri = req.uri().clone();
    let response = next.run(req).await;
    tracing::info!(%method, %uri, "done");
    response
}
```

## Gotchas
- Middleware runs bottom-to-top for requests (last `.layer()` runs first) but top-to-bottom for responses
- `next.run(req)` consumes the request — extract headers/URI before calling it
- `from_fn` closures must be `async fn`, not closures returning futures — use `async fn` items
- Tower layers and axum `from_fn` middleware are different: layers implement `tower::Layer`, `from_fn` wraps a function
- The `Extension` extractor in middleware is per-request — use `State` for shared state
- CORS must be outermost layer or preflight OPTIONS requests may hit auth middleware first
- `TraceLayer` from `tower-http` integrates with `tracing` — don't duplicate logging in custom middleware
- Middleware applied to nested routes via `nest()` only affects routes inside that nest

## Related
- rust/web/axum-deep.md
- rust/web/axum-deep.md
- rust/concurrency/async-tokio.md
