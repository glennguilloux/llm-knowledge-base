---
id: "rust-stdlib-error-crates"
title: "Rust Error Handling with thiserror and anyhow"
language: "rust"
category: "stdlib"
subcategory: "error-handling"
tags: ["rust", "error", "thiserror", "anyhow", "result", "custom-error"]
version: "1.75+"
retrieval_hint: "Rust thiserror anyhow error handling custom error Result context"
last_verified: "2026-05-24"
confidence: "high"
---

# Rust Error Handling with thiserror and anyhow

## When to Use
- `thiserror`: Defining custom error types for libraries and APIs
- `anyhow`: Application-level error handling with context
- Converting between error types automatically
- Adding context to errors for debugging

## Standard Pattern

```rust
// --- thiserror: library/binary error types ---
use thiserror::Error;

#[derive(Error, Debug)]
pub enum AppError {
    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),

    #[error("Not found: {resource} with id {id}")]
    NotFound { resource: String, id: i64 },

    #[error("Validation error: {0}")]
    Validation(String),

    #[error("Unauthorized")]
    Unauthorized,

    #[error("Internal error: {0}")]
    Internal(#[from] std::io::Error),
}

// Custom error can be used with ?
fn get_user(id: i64) -> Result<User, AppError> {
    let user = db.query_user(id)?;  // sqlx::Error -> AppError::Database
    user.ok_or(AppError::NotFound {
        resource: "User".to_string(),
        id,
    })
}

// Implement axum::IntoResponse for HTTP
impl axum::response::IntoResponse for AppError {
    fn into_response(self) -> axum::response::Response {
        let (status, message) = match &self {
            AppError::NotFound { .. } => (StatusCode::NOT_FOUND, self.to_string()),
            AppError::Validation(_) => (StatusCode::BAD_REQUEST, self.to_string()),
            AppError::Unauthorized => (StatusCode::UNAUTHORIZED, self.to_string()),
            _ => (StatusCode::INTERNAL_SERVER_ERROR, "Internal error".to_string()),
        };
        (status, Json(serde_json::json!({ "error": message }))).into_response()
    }
}

// --- anyhow: application-level error handling ---
use anyhow::{Context, Result, bail, ensure};

fn load_config(path: &str) -> Result<Config> {
    let content = std::fs::read_to_string(path)
        .context(format!("Failed to read config file: {path}"))?;

    let config: Config = serde_yaml::from_str(&content)
        .context("Failed to parse config YAML")?;

    ensure!(!config.database_url.is_empty(), "database_url must not be empty");

    if config.port == 0 {
        bail!("port must be non-zero");
    }

    Ok(config)
}

// anyhow with ? for any error type
fn run() -> Result<()> {
    let config = load_config("config.yaml")?;
    let db = connect(&config.database_url)?;
    let server = start_server(&config, db)?;
    server.await?;
    Ok(())
}
```

## Common Mistakes

```rust
// WRONG: Using String for all errors
fn get_user(id: i64) -> Result<User, String> {
    db.query(id).map_err(|e| e.to_string())  // Loses type information
}

// CORRECT: Use thiserror for typed errors
fn get_user(id: i64) -> Result<User, AppError> {
    Ok(db.query(id)?)  // Automatic conversion via #[from]
}

// WRONG: Using unwrap() in library code
fn process(data: &[u8]) -> Vec<u8> {
    let parsed = parse(data).unwrap();  // Panics on bad input!
    transform(parsed)
}

// CORRECT: Return Result and propagate
fn process(data: &[u8]) -> Result<Vec<u8>, AppError> {
    let parsed = parse(data)?;
    Ok(transform(parsed))
}

// WRONG: Not adding context to anyhow errors
fn load(path: &str) -> Result<Config> {
    let content = std::fs::read_to_string(path)?;  // "No such file" — which file?
    Ok(serde_yaml::from_str(&content)?)
}

// CORRECT: Add context
fn load(path: &str) -> Result<Config> {
    let content = std::fs::read_to_string(path)
        .context(format!("Reading {path}"))?;
    Ok(serde_yaml::from_str(&content)
        .context("Parsing config YAML")?)
}
```

## Gotchas
- `thiserror` derives `Error` trait and `Display` — no manual implementation needed
- `#[from]` auto-implements `From` for error conversion — one variant per source type
- `anyhow::Result<T>` is `Result<T, anyhow::Error>` — works with any error type
- `bail!()` returns early with an error; `ensure!()` is like `assert!` but returns `Result`
- Use `thiserror` in libraries (typed errors); `anyhow` in applications (ergonomic handling)
- `anyhow::Error` is `Send + Sync` — safe across threads
- `.context()` wraps errors with additional info — chain for debugging
- Don't use `anyhow` in library APIs — consumers can't match on `anyhow::Error`

## Related
- rust/stdlib/result-option.md
- rust/web/axum-basics.md
- rust/stdlib/error-handling.md
