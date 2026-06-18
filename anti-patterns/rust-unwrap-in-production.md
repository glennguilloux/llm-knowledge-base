---
id: "anti-patterns-rust-unwrap-in-production"
title: "Rust Anti-Pattern: unwrap/expect in Production Code"
language: "rust"
category: "anti-patterns"
tags: ["antipatterns", "rust", "unwrap", "expect", "error-handling", "panic"]
version: "n/a"
retrieval_hint: "Rust unwrap expect panic production error handling Result Option error propagation anyhow thiserror catch_unwind"
last_verified: "2026-05-24"
confidence: "high"
---

# Rust Anti-Pattern: unwrap/expect in Production Code

## When to Use
- Reviewing Rust code for panic-prone error handling
- Training LLMs to use idiomatic Rust error propagation
- Distinguishing between prototyping `.unwrap()` and production error handling
- Understanding when unwrap is acceptable vs. when to propagate

## Standard Pattern

```rust
use std::fs;
use std::num::ParseIntError;
use std::path::Path;

// ---------------------------------------------------------------------------
// WRONG: Unwrapping Options when pattern matching works
// ---------------------------------------------------------------------------

// WRONG: Unwrap on Option — panics on None
fn find_user(id: u32) -> Option<String> {
    if id == 1 { Some("Alice".into()) } else { None }
}

let user = find_user(42).unwrap(); // PANIC: called `Option::unwrap()` on a `None` value

// CORRECT: Match or use if-let
fn greet_user(id: u32) -> String {
    match find_user(id) {
        Some(name) => format!("Hello, {}!", name),
        None => format!("User {} not found", id),
    }
}

// Or use ? operator if in a function returning Option/Result
fn get_user_or_default(id: u32) -> Option<String> {
    let name = find_user(id)?; // Returns None early if find_user returns None
    Some(name.to_uppercase())
}

// ---------------------------------------------------------------------------
// WRONG: Unwrapping Results that should propagate
// ---------------------------------------------------------------------------

// WRONG: Unwrap on Result in library code
fn read_config() -> String {
    let content = fs::read_to_string("config.toml").unwrap(); // PANIC if file missing
    content
}

// CORRECT: Propagate the error to the caller
fn read_config() -> Result<String, std::io::Error> {
    fs::read_to_string("config.toml") // ? propagates the error
}

// ---------------------------------------------------------------------------
// WRONG: .expect() with unhelpful messages
// ---------------------------------------------------------------------------

// WRONG: Bad expect message — doesn't help debugging
let port: u16 = "abc"
    .parse()
    .expect("Failed to parse"); // What failed? Parsing what?

// CORRECT: Descriptive expect message with context
let port: u16 = "abc"
    .parse()
    .expect("Failed to parse PORT from environment variable PORT");

// Even better: use context from anyhow
use anyhow::{Context, Result};

fn get_port() -> Result<u16> {
    std::env::var("PORT")
        .context("PORT environment variable not set")?
        .parse::<u16>()
        .context("PORT is not a valid number")?
}

// ---------------------------------------------------------------------------
// WRONG: Unwrap in library code vs binary code
// ---------------------------------------------------------------------------

// ACCEPTABLE in binaries (main): unwrap is okay for unrecoverable errors
fn main() {
    let content = fs::read_to_string("config.toml")
        .expect("Failed to read config.toml — application cannot start");
    // Binary exits with clear message — acceptable
}

// WRONG in libraries: library code should never panic
// (library below panics, caller has no control)
pub fn load_data(path: &str) -> Vec<u8> {
    fs::read(path).unwrap() // ❌ Library panics — caller can't handle the error
}

// CORRECT in libraries: return Result
pub fn load_data(path: &str) -> Result<Vec<u8>, std::io::Error> {
    fs::read(path)
}

// ---------------------------------------------------------------------------
// WRONG: Panic in web server request handler
// ---------------------------------------------------------------------------

// WRONG: Unwrap in web handler — takes down all connections
async fn handler(param: String) -> impl Responder {
    let number: i32 = param.parse().unwrap(); // PANIC — whole server crashes!
    HttpResponse::Ok().json(number * 2)
}

// CORRECT: Return error response
async fn handler(param: String) -> Result<impl Responder, actix_web::Error> {
    let number: i32 = param
        .parse()
        .map_err(|_| HttpResponse::BadRequest().body("Invalid number"))?;
    Ok(HttpResponse::Ok().json(number * 2))
}

// ---------------------------------------------------------------------------
// WRONG: .ok() or .unwrap_or_default() instead of proper handling
// ---------------------------------------------------------------------------

// CORRECT: .unwrap_or_default() for truly optional defaults
let count: usize = Some(42).unwrap_or_default(); // 42
let none_count: Option<usize> = None;
let default = none_count.unwrap_or_default(); // 0 — reasonable default for counter

// WRONG: Using ok() to convert Result to Option when you need the error
let file = fs::read_to_string("config.toml").ok()?; // Loses error info
// vs:
let file = fs::read_to_string("config.toml")?; // Preserves error for caller

// ---------------------------------------------------------------------------
// WRONG: Unwrap on Mutex lock (poisoned mutex)
// ---------------------------------------------------------------------------

use std::sync::Mutex;

let counter = Mutex::new(0);

// WRONG: Unwrap on poisoned Mutex — panics
* *counter.lock().unwrap() += 1;

// CORRECT: Handle poison gracefully
let Ok(mut guard) = counter.lock() else {
    println!("Mutex was poisoned, resetting to 0");
    *counter.lock().unwrap() = 0;
    return;
};
*guard += 1;

// ---------------------------------------------------------------------------
// WRONG: Index panic on slices
// ---------------------------------------------------------------------------

// WRONG: Direct indexing — panics on out of bounds
fn get_item(items: &[i32], index: usize) -> i32 {
    items[index] // PANIC if index >= items.len()
}

// CORRECT: Use .get() which returns Option
fn get_item(items: &[i32], index: usize) -> Option<&i32> {
    items.get(index)
}
```

## Common Mistakes
The most dangerous Rust anti-pattern is pervasive `.unwrap()` in production code — every unwrap is a potential panic that crashes the entire process. In library code, unwraps deny callers the ability to handle errors. In web servers, a single unwrap in a request handler crashes all concurrent connections. `.expect()` with vague messages like "unwrap failed" provides no debugging context when the inevitable panic happens in production.

## Gotchas
- `.unwrap()` and `.expect()` on `Result` panic on `Err` — they're debug tools, not error-handling strategies
- `.expect()` IS better than `.unwrap()` when the message is descriptive — always describe WHAT failed and WHY
- `?` operator is the idiomatic alternative — it propagates `Err`/`None` to the caller
- Library code should NEVER panic (except in documented, unrecoverable scenarios) — always return `Result`
- Binary `main()` is the one place where `.expect()` is idiomatic — on startup failures the app can't continue
- `Mutex::lock()` returns `LockResult<MutexGuard>` — the `Err` variant means the mutex is POISONED (another thread panicked while holding the lock)
- `catch_unwind()` can catch panics, but it's not a substitute for proper error handling and has limitations (aborts, complex types)
- Slice indexing `[i]` panics on out-of-bounds — use `.get(i)` for safe access
- `unwrap_or_else()` avoids eager evaluation: `opt.unwrap_or_else(|| expensive_default())`
- `thiserror` for library error types, `anyhow` for binary error handling — both eliminate unwraps in normal flow
- `#[should_panic]` tests are for testing panic behavior — production codepaths should rarely need it
- `panic = "abort"` in Cargo.toml makes every unwrap an immediate process termination without any cleanup
- Clippy warns about `unwrap_used` and `expect_used` — enable these in production crates
- `.unwrap()` in test code is fine — tests should panic on failure; use `?` or `.unwrap()` as appropriate

## Related
- anti-patterns/rust-antipatterns.md
- rust/testing/mocking.md
