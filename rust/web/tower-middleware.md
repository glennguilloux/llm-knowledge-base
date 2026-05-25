---
id: "rust-web-tower-middleware"
title: "Tower Service and Layer Middleware"
language: "rust"
category: "web"
tags: ["tower", "service", "layer", "middleware", "rate-limit", "timeout", "compression"]
version: "1.75+"
retrieval_hint: "tower service layer middleware rate limit timeout compression reusable"
last_verified: "2026-05-24"
confidence: "high"
---

# Tower Service and Layer Middleware

## When to Use
- Building reusable middleware that works across Axum, Tonic, Hyper
- Implementing rate limiting, timeouts, retries, compression
- Creating middleware with complex state (counters, connection pools)
- Wrapping services with cross-cutting behavior

## Standard Pattern

```rust
use std::future::Future;
use std::pin::Pin;
use std::task::{Context, Poll};
use std::time::{Duration, Instant};
use tower::{Layer, Service};
use axum::{
    http::{Request, Response, StatusCode},
    routing::get,
    Router,
};
use tower::limit::RateLimitLayer;
use tower_http::compression::CompressionLayer;
use tower_http::timeout::TimeoutLayer;

// Custom middleware: request timing
#[derive(Clone)]
struct TimingLayer;

impl<S> Layer<S> for TimingLayer {
    type Service = TimingService<S>;

    fn layer(&self, inner: S) -> Self::Service {
        TimingService { inner }
    }
}

#[derive(Clone)]
struct TimingService<S> {
    inner: S,
}

impl<S, ReqBody, ResBody> Service<Request<ReqBody>> for TimingService<S>
where
    S: Service<Request<ReqBody>, Response = Response<ResBody>> + Clone + Send + 'static,
    S::Future: Send + 'static,
    ReqBody: Send + 'static,
    ResBody: Send + 'static,
{
    type Response = S::Response;
    type Error = S::Error;
    type Future = Pin<Box<dyn Future<Output = Result<Self::Response, Self::Error>> + Send>>;

    fn poll_ready(&mut self, cx: &mut Context<'_>) -> Poll<Result<(), Self::Error>> {
        self.inner.poll_ready(cx)
    }

    fn call(&mut self, req: Request<ReqBody>) -> Self::Future {
        let start = Instant::now();
        let method = req.method().clone();
        let uri = req.uri().clone();
        let mut inner = self.inner.clone();
        Box::pin(async move {
            let mut response = inner.call(req).await?;
            let duration = start.elapsed();
            response.headers_mut().insert(
                "x-response-time",
                header::HeaderValue::from_str(&format!("{}ms", duration.as_millis())).unwrap(),
            );
            tracing::info!(%method, %uri, duration_ms = duration.as_millis(), "request");
            Ok(response)
        })
    }
}

// Custom middleware: API key validation
#[derive(Clone)]
struct ApiKeyLayer {
    valid_keys: Vec<String>,
}

impl<S> Layer<S> for ApiKeyLayer {
    type Service = ApiKeyService<S>;

    fn layer(&self, inner: S) -> Self::Service {
        ApiKeyService {
            inner,
            valid_keys: self.valid_keys.clone(),
        }
    }
}

#[derive(Clone)]
struct ApiKeyService<S> {
    inner: S,
    valid_keys: Vec<String>,
}

impl<S, ReqBody, ResBody> Service<Request<ReqBody>> for ApiKeyService<S>
where
    S: Service<Request<ReqBody>, Response = Response<ResBody>> + Clone + Send + 'static,
    S::Future: Send + 'static,
    ReqBody: Send + 'static,
    ResBody: Default + Send + 'static,
{
    type Response = S::Response;
    type Error = S::Error;
    type Future = Pin<Box<dyn Future<Output = Result<Self::Response, Self::Error>> + Send>>;

    fn poll_ready(&mut self, cx: &mut Context<'_>) -> Poll<Result<(), Self::Error>> {
        self.inner.poll_ready(cx)
    }

    fn call(&mut self, req: Request<ReqBody>) -> Self::Future {
        let api_key = req
            .headers()
            .get("x-api-key")
            .and_then(|v| v.to_str().ok())
            .unwrap_or("");

        if !self.valid_keys.iter().any(|k| k == api_key) {
            return Box::pin(async {
                let mut resp = Response::new(ResBody::default());
                *resp.status_mut() = StatusCode::UNAUTHORIZED;
                Ok(resp)
            });
        }

        let mut inner = self.inner.clone();
        Box::pin(async move { inner.call(req).await })
    }
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();

    let app = Router::new()
        .route("/", get(|| async { "Hello" }))
        // Built-in tower layers
        .layer(TimeoutLayer::new(Duration::from_secs(30)))
        .layer(RateLimitLayer::new(100, Duration::from_secs(1)))
        .layer(CompressionLayer::new())
        // Custom layers
        .layer(TimingLayer)
        .layer(ApiKeyLayer {
            valid_keys: vec!["secret-key-1".into(), "secret-key-2".into()],
        });

    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000")
        .await
        .unwrap();
    axum::serve(listener, app).await.unwrap();
}
```

## Common Mistakes

```rust
// WRONG: Cloning service in call() without Clone bound
impl<S> Service<Request<Body>> for MyMiddleware<S> {
    fn call(&mut self, req: Request<Body>) -> Self::Future {
        let fut = self.inner.call(req); // ERROR: &mut self consumed
        // Can't call again after this
    }
}

// CORRECT: Clone the inner service in call()
fn call(&mut self, req: Request<Body>) -> Self::Future {
    let mut inner = self.inner.clone(); // Clone for the async block
    Box::pin(async move { inner.call(req).await })
}

// WRONG: Blocking in poll_ready
fn poll_ready(&mut self, cx: &mut Context<'_>) -> Poll<Result<(), Self::Error>> {
    std::thread::sleep(Duration::from_millis(10)); // blocks runtime!
    Poll::Ready(Ok(()))
}

// CORRECT: Delegate to inner service
fn poll_ready(&mut self, cx: &mut Context<'_>) -> Poll<Result<(), Self::Error>> {
    self.inner.poll_ready(cx)
}

// WRONG: Forgetting to call poll_ready before call
fn call(&mut self, req: Request<Body>) -> Self::Future {
    let mut inner = self.inner.clone();
    // Didn't check poll_ready — may not be ready
    Box::pin(async move { inner.call(req).await })
}

// CORRECT: poll_ready is checked by tower before call() is invoked
// But your implementation must delegate it correctly
```

## Gotchas
- `poll_ready` must delegate to `self.inner.poll_ready(cx)` — tower calls it before `call()`
- `call()` must clone `self.inner` into the async block — the original `self` may be reused for concurrent requests
- `Service` trait requires `Clone` bound on inner service for axum compatibility — axum clones services for each request
- `Layer` is a simple factory — it takes the inner service and wraps it; keep it stateless
- Rate limiting uses `tower::limit::RateLimitLayer` — needs `tower` with `limit` feature
- Timeout wraps the future with `tokio::time::timeout` — doesn't cancel in-flight work, just returns 503
- Compression uses `tower_http::compression` — needs `tower-http` with `compression` feature
- Middleware order matters: `TimeoutLayer` should wrap `RateLimitLayer` so timeouts don't count against rate limit

## Related
- rust/web/axum-deep.md
- rust/web/axum-middleware.md
- rust/concurrency/async-tokio.md
