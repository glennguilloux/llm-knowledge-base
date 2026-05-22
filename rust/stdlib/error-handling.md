---
id: "rust-stdlib-error-handling"
title: "Error Handling Strategies"
language: "rust"
category: "stdlib"
tags: ["error-handling", "thiserror", "anyhow", "panic", "Result", "From"]
version: "1.75+"
retrieval_hint: "error handling thiserror anyhow panic Result custom error From"
last_verified: "2026-05-22"
confidence: "high"
---

# Error Handling Strategies

## When to Use
- Libraries: define structured error types with `thiserror`
- Applications: use `anyhow` for ergonomic error propagation
- Needing to distinguish error variants for recovery logic
- Converting between error types across module boundaries

## Standard Pattern

```rust
use std::io;
use std::num::ParseIntError;

// --- Library-style: thiserror for structured errors ---
#[derive(Debug, thiserror::Error)]
pub enum ConfigError {
    #[error("IO error: {0}")]
    Io(#[from] io::Error),

    #[error("Invalid port: {0}")]
    InvalidPort(#[from] ParseIntError),

    #[error("Missing required field: {field}")]
    MissingField { field: String },

    #[error("Value {value} out of range [{min}, {max}]")]
    OutOfRange {
        value: f64,
        min: f64,
        max: f64,
    },
}

pub fn load_config(path: &str) -> Result<ServerConfig, ConfigError> {
    let content = std::fs::read_to_string(path)?;
    let port: u16 = content
        .lines()
        .find(|l| l.starts_with("port="))
        .ok_or(ConfigError::MissingField {
            field: "port".into(),
        })?
        .trim_start_matches("port=")
        .parse()?;

    Ok(ServerConfig { port })
}

// --- Application-style: anyhow for quick propagation ---
use anyhow::{Context, Result, bail, ensure};

fn run_server() -> Result<()> {
    let config = load_config("server.conf")
        .context("Failed to load server configuration")?;

    ensure!(config.port > 0, "Port must be positive, got {}", config.port);

    if config.port > 65535 {
        bail!("Port {} exceeds maximum", config.port);
    }

    println!("Listening on port {}", config.port);
    Ok(())
}

// --- Manual error conversion with From ---
#[derive(Debug)]
enum AppError {
    Database(String),
    Auth(String),
    NotFound(String),
}

impl std::fmt::Display for AppError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            AppError::Database(msg) => write!(f, "Database error: {}", msg),
            AppError::Auth(msg) => write!(f, "Auth error: {}", msg),
            AppError::NotFound(msg) => write!(f, "Not found: {}", msg),
        }
    }
}

impl std::error::Error for AppError {}

impl From<io::Error> for AppError {
    fn from(e: io::Error) -> Self {
        AppError::Database(e.to_string())
    }
}

struct ServerConfig {
    port: u16,
}

fn main() {
    if let Err(e) = run_server() {
        eprintln!("Error: {:#}", e); // {:#} prints the full chain
        std::process::exit(1);
    }
}
```

## Common Mistakes

```rust
// WRONG: Panicking on errors in library code
pub fn parse_config(s: &str) -> Config {
    let port: u16 = s.parse().unwrap(); // panics on bad input
    Config { port }
}

// CORRECT: Return Result in library code
pub fn parse_config(s: &str) -> Result<Config, ConfigError> {
    let port: u16 = s.parse().map_err(ConfigError::InvalidPort)?;
    Ok(Config { port })
}

// WRONG: Catch-all String errors lose information
fn do_work() -> Result<(), String> {
    std::fs::read_to_string("config.toml")
        .map_err(|e| e.to_string())?; // lost error kind
    Ok(())
}

// CORRECT: Preserve error types or use thiserror
fn do_work() -> Result<(), ConfigError> {
    std::fs::read_to_string("config.toml")?; // From<io::Error>
    Ok(())
}

// WRONG: Ignoring errors with let _ = ...
fn cleanup() {
    let _ = std::fs::remove_file("temp.txt"); // silently fails
}

// CORRECT: At minimum, log the error
fn cleanup() {
    if let Err(e) = std::fs::remove_file("temp.txt") {
        eprintln!("Warning: cleanup failed: {}", e);
    }
}

// WRONG: Using panic! for expected failures
fn divide(a: f64, b: f64) -> f64 {
    if b == 0.0 {
        panic!("Division by zero");
    }
    a / b
}

// CORRECT: Return Result for expected failures
fn divide(a: f64, b: f64) -> Result<f64, String> {
    if b == 0.0 {
        Err("Division by zero".into())
    } else {
        Ok(a / b)
    }
}
```

## Gotchas
- `panic!` is for bugs (unrecoverable); `Result` is for expected failures (recoverable)
- `thiserror` generates `Display` and `From` impls — no boilerplate
- `anyhow::Result` is `Result<T, anyhow::Error>` — great for applications, avoid in libraries
- `{:#}` in format strings prints the full error chain (source errors)
- `#[from]` on a thiserror variant auto-generates `From` conversion
- `anyhow::Context` adds human-readable messages to errors as you propagate
- `bail!` and `ensure!` are shortcuts for returning errors early
- In libraries, expose specific error variants so callers can match on them

## Related
- rust/stdlib/result-option.md
- rust/stdlib/traits.md
- rust/stdlib/ownership.md
