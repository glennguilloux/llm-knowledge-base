---
id: "rust-http-client"
title: "HTTP Clients: reqwest, Headers, JSON, Error Handling"
language: "rust"
category: "stdlib"
tags: ["rust", "http", "reqwest", "client", "json", "async"]
version: "n/a"
retrieval_hint: "rust http client reqwest async JSON headers error handling retry timeout"
last_verified: "2026-05-24"
confidence: "high"
---

# HTTP Clients: reqwest, Headers, JSON, Error Handling

## When to Use
- Making HTTP requests from Rust applications
- Consuming REST APIs with JSON payloads
- Implementing API clients with error handling and retries
- File uploads and streaming downloads

## Standard Pattern

```rust
use reqwest::{Client, StatusCode, header};
use serde::{Deserialize, Serialize};
use std::time::Duration;
use thiserror::Error;

// === Dependencies (Cargo.toml) ===
// reqwest = { version = "0.12", features = ["json", "gzip", "brotli"] }
// serde = { version = "1", features = ["derive"] }
// serde_json = "1"
// thiserror = "1"
// tokio = { version = "1", features = ["full"] }


// === Types ===

#[derive(Debug, Deserialize)]
struct ApiResponse {
    id: i64,
    name: String,
    email: String,
}

#[derive(Debug, Serialize)]
struct CreateUser {
    name: String,
    email: String,
}

#[derive(Debug, Error)]
enum ApiError {
    #[error("Request failed: {0}")]
    Request(#[from] reqwest::Error),

    #[error("API error: {status} - {message}")]
    Api { status: StatusCode, message: String },

    #[error("Rate limited, retry after {retry_after}s")]
    RateLimited { retry_after: u64 },
}


// === Client Setup ===

fn build_client() -> Client {
    let mut headers = header::HeaderMap::new();
    headers.insert(
        header::USER_AGENT,
        "MyApp/1.0".parse().unwrap(),
    );
    headers.insert(
        header::ACCEPT,
        "application/json".parse().unwrap(),
    );

    Client::builder()
        .default_headers(headers)
        .timeout(Duration::from_secs(30))
        .connect_timeout(Duration::from_secs(10))
        .gzip(true)
        .brotli(true)
        .build()
        .expect("Failed to build HTTP client")
}


// === Basic Requests ===

async fn get_user(client: &Client, user_id: i64) -> Result<ApiResponse, ApiError> {
    let response = client
        .get(format!("https://api.example.com/users/{user_id}"))
        .header("X-Request-ID", uuid::Uuid::new_v4().to_string())
        .send()
        .await?;

    // Check status first
    let status = response.status();
    if !status.is_success() {
        let text = response.text().await?;
        return Err(ApiError::Api {
            status,
            message: text,
        });
    }

    let user: ApiResponse = response.json().await?;
    Ok(user)
}

async fn create_user(client: &Client, user: &CreateUser) -> Result<ApiResponse, ApiError> {
    let response = client
        .post("https://api.example.com/users")
        .json(user)
        .send()
        .await?;

    response.error_for_status_ref()?;
    Ok(response.json().await?)
}


// === Authentication ===

async fn authenticated_request(client: &Client, token: &str) -> Result<(), ApiError> {
    let response = client
        .get("https://api.example.com/protected")
        .bearer_auth(token)
        .send()
        .await?;

    response.error_for_status()?;
    Ok(())
}


// === File Upload (multipart) ===

use reqwest::multipart;

async fn upload_file(
    client: &Client,
    file_path: &str,
) -> Result<serde_json::Value, ApiError> {
    let file_bytes = tokio::fs::read(file_path).await
        .map_err(|e| ApiError::Api {
            status: StatusCode::INTERNAL_SERVER_ERROR,
            message: e.to_string(),
        })?;

    let part = multipart::Part::bytes(file_bytes)
        .file_name("report.pdf")
        .mime_str("application/pdf")?;

    let form = multipart::Form::new()
        .text("description", "Monthly report")
        .part("file", part);

    let response = client
        .post("https://api.example.com/upload")
        .multipart(form)
        .send()
        .await?;

    Ok(response.json().await?)
}


// === Retry Pattern ===

async fn retry_request<F, Fut, T>(operation: F, max_retries: u32) -> Result<T, ApiError>
where
    F: Fn() -> Fut,
    Fut: std::future::Future<Output = Result<T, ApiError>>,
{
    let mut last_error = None;

    for attempt in 0..=max_retries {
        match operation().await {
            Ok(result) => return Ok(result),
            Err(ApiError::RateLimited { retry_after }) => {
                tokio::time::sleep(Duration::from_secs(retry_after)).await;
                continue;
            }
            Err(e) if attempt < max_retries => {
                last_error = Some(e);
                // Exponential backoff
                tokio::time::sleep(Duration::from_millis(100 * 2u64.pow(attempt))).await;
            }
            Err(e) => return Err(e),
        }
    }

    Err(last_error.unwrap())
}
```

## Common Mistakes

```rust
// WRONG: Not checking response status before parsing JSON
let user: ApiResponse = client
    .get(url)
    .send()
    .await?
    .json()  // Panics on 404/500 because body isn't JSON!
    .await?;

// CORRECT: Check status first
let response = client.get(url).send().await?;
if !response.status().is_success() {
    let text = response.text().await?;
    return Err(ApiError::Api { status: response.status(), message: text });
}
let user: ApiResponse = response.json().await?;


// WRONG: No timeout (request hangs forever)
let response = reqwest::get("https://slow-api.com").await?;  // May hang!

// CORRECT: Set timeout
let client = Client::builder()
    .timeout(Duration::from_secs(30))
    .build()?;


// WRONG: Rebuilding Client for every request
fn make_request() {
    let client = reqwest::Client::new();  // Expensive!
}

// CORRECT: Reuse Client (uses connection pooling)
// Build once, share via Arc or dependency injection
let client = build_client();


// WRONG: Not handling redirects explicitly
// reqwest follows up to 10 redirects by default (potential SSRF!)

// CORRECT: Configure redirect behavior
let client = Client::builder()
    .redirect(reqwest::redirect::Policy::limited(5))
    .build()?;

// Or disable for security-sensitive endpoints
// .redirect(reqwest::redirect::Policy::none())


// WRONG: Blocking the async runtime with reqwest::blocking
// Use blocking::Client ONLY in synchronous contexts (not async tasks)

// CORRECT: Use async Client in async contexts
```

## Gotchas
- **Connection pool exhaustion**: reqwest's default connection pool has no size limit, but the OS may limit file descriptors. For high-throughput services, set `pool_max_idle_per_host()` to avoid socket exhaustion under load.
- **TLS configuration**: reqwest uses `native-tls` by default (platform SSL). For cross-compilation or minimal containers, enable the `rustls-tls` feature instead of `default-features` to avoid linking OpenSSL.
- **Redirect chains**: reqwest follows redirects with the original method by default. POST → 302 → GET can cause unexpected behavior. Configure `redirect::Policy` explicitly for POST endpoints.
- **Large responses**: `response.json()` buffers the entire body into memory. For streaming JSON, use `response.chunk()` or `response.bytes_stream()` with serde `StreamDeserializer`.
- **Error for_status vs manual**: `response.error_for_status()` clones the response on success (consumes self). Use `response.error_for_status_ref()` for borrowing. Prefer manual checks for better error messages.
- **Proxy support**: reqwest supports HTTP and SOCKS5 proxies via the `proxy` feature. System proxy configuration (HTTP_PROXY env var) is supported out of the box.
- **Cookie handling**: reqwest has a `cookies` feature that enables a cookie store. Without it, cookies are not stored between requests. Enable the feature for session-based APIs.

## Related
- rust/web/axum-middleware.md
- rust/testing/integration.md
- rust/stdlib/serde.md
