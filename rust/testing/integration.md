---
id: "rust-integration-testing"
title: "Integration Testing: Test Modules, Mocking, Async Tests"
language: "rust"
category: "testing"
tags: ["rust", "testing", "integration", "async", "mocking", "test-utils"]
version: "n/a"
retrieval_hint: "rust integration testing test modules async tokio mock external services test organization"
last_verified: "2026-05-24"
confidence: "high"
---

# Integration Testing: Test Modules, Mocking, Async Tests

## When to Use
- Testing Rust applications end-to-end
- Verifying API endpoints and database interactions
- Mocking external services in integration tests
- Organizing test code across modules

## Standard Pattern

```rust
// === Test Organization ===

// tests/integration_test.rs (integration tests — separate binary)
// These test the library as an external consumer

use myapp::*;  // Tests only have access to public API

#[test]
fn test_add_user() {
    let result = add_user("alice@example.com", "Alice");
    assert!(result.is_ok());

    let user = result.unwrap();
    assert_eq!(user.email, "alice@example.com");
}

#[test]
fn test_duplicate_email() {
    add_user("alice@example.com", "Alice").unwrap();
    let result = add_user("alice@example.com", "Alice Again");
    assert!(result.is_err());
}


// === Async Tests ===

#[tokio::test]
async fn test_async_operation() {
    let result = async_add(1, 2).await;
    assert_eq!(result, 3);
}

// For tests requiring a Tokio runtime with specific config
#[tokio::test(flavor = "multi_thread")]
async fn test_concurrent_ops() {
    // Multi-threaded runtime for concurrency tests
}


// === Test Modules (in src/) ===

// src/lib.rs or src/module.rs
#[cfg(test)]
mod tests {
    use super::*;  // Import private items from parent module

    #[test]
    fn test_internal_logic() {
        // Can test private functions
        assert_eq!(internal_helper(5), 10);
    }
}

// Separate test module file
// src/tests/common/mod.rs — shared test utilities

#[cfg(test)]
pub(crate) mod common {
    use crate::models::User;

    // Factory functions for creating test data
    pub fn create_test_user() -> User {
        User {
            id: 1,
            email: "test@example.com".to_string(),
            name: "Test User".to_string(),
        }
    }

    pub fn create_test_users(count: usize) -> Vec<User> {
        (0..count)
            .map(|i| User {
                id: i as i64,
                email: format!("user{i}@example.com"),
                name: format!("User {i}"),
            })
            .collect()
    }
}


// === Test Fixtures ===

// tests/common/mod.rs
pub mod fixtures;

use std::sync::OnceLock;

// Shared test database (lazily initialized once)
static TEST_DB: OnceLock<TestDb> = OnceLock::new();

pub fn get_test_db() -> &'static TestDb {
    TEST_DB.get_or_init(|| {
        let db = TestDb::setup();
        // Register cleanup at process exit
        std::sync::OnceLock::new();
        db
    })
}

pub struct TestDb {
    connection_string: String,
}

impl TestDb {
    fn setup() -> Self {
        let conn_str = std::env::var("TEST_DATABASE_URL")
            .unwrap_or_else(|_| "postgres://localhost/test_db".to_string());
        // Run migrations
        // ...
        TestDb { connection_string: conn_str }
    }
}


// === Mocking Pattern ===

// Trait to mock
trait EmailService {
    async fn send_email(&self, to: &str, subject: &str, body: &str) -> Result<(), Error>;
}

// Real implementation
#[cfg(not(test))]
struct SmtpEmailService;

#[cfg(not(test))]
impl EmailService for SmtpEmailService { /* real SMTP */ }

// Mock implementation
#[cfg(test)]
struct MockEmailService {
    sent_emails: Arc<Mutex<Vec<(String, String, String)>>>,
}

#[cfg(test)]
impl EmailService for MockEmailService {
    async fn send_email(&self, to: &str, subject: &str, body: &str) -> Result<(), Error> {
        self.sent_emails.lock().unwrap()
            .push((to.to_string(), subject.to_string(), body.to_string()));
        Ok(())
    }
}


// === API Test Example ===

#[tokio::test]
async fn test_create_user_endpoint() {
    // Setup
    let app = test_app_builder().build().await;
    let client = app.get_client();

    // Execute
    let response = client
        .post("/api/users")
        .json(&serde_json::json!({
            "email": "new@example.com",
            "name": "New User"
        }))
        .send()
        .await;

    // Assert
    assert_eq!(response.status(), 201);
    let body: serde_json::Value = response.json().await;
    assert_eq!(body["email"], "new@example.com");
    assert!(body["id"].is_number());
}
```

## Common Mistakes

```rust
// WRONG: Integration tests as separate .rs files at root of tests/
// that don't use a common module (duplicate setup code)

// CORRECT: Use tests/common/mod.rs for shared utilities
// Then in each test file:
mod common;

#[test]
fn test_something() {
    let db = common::get_test_db();
    // ...
}


// WRONG: Ignoring #[cfg(test)] for test-only code
// Test utilities end up in release binary!

// CORRECT: Gate test-only code
#[cfg(test)]
pub mod test_utils { ... }


// WRONG: Async test without tokio runtime attribute
async fn test_async() {  // Compiler warning: unused async
    // ...
}

// CORRECT: Use #[tokio::test]
#[tokio::test]
async fn test_async() { ... }


// WRONG: Mutable global state between tests (tests affect each other)
static COUNTER: Mutex<i32> = Mutex::new(0);

#[test]
fn test_one() {
    *COUNTER.lock().unwrap() += 1;  // Affects subsequent tests!
}

// CORRECT: Use local state per test
#[test]
fn test_one() {
    let counter = Cell::new(0);
    // ...
}


// WRONG: Not cleaning up test resources (database rows, temp files)
#[tokio::test]
async fn test_create_user() {
    let user = create_user_in_db("test@example.com").await;
    // Test passes but user stays in database!
}

// CORRECT: Wrap in transaction or use setup/teardown
#[tokio::test]
async fn test_create_user() {
    let tx = db.begin().await;
    let user = create_user_in_db("test@example.com").await;
    // Assert...
    tx.rollback().await;  // Clean up
}
```

## Gotchas
- **Binary crates can't have integration tests**: Integration tests (`tests/`) only work for library crates. If your crate is a binary, extract the core logic into a `lib.rs` and make it a library+binary crate.
- **`#[cfg(test)]` vs test modules**: `#[cfg(test)]` on a module means it only compiles during `cargo test`. Test modules without `#[cfg(test)]` compile into release builds too (increasing binary size).
- **Parallel test execution**: `cargo test` runs tests in parallel by default. Tests that share resources (database, filesystem, ports) need `#[serial_test::serial]` or use unique suffixes (e.g., randomized database names).
- **`should_panic` tests**: Use `#[should_panic(expected = "...")]` for testing panic conditions. Prefer `Result<T, E>` return types from tests for better error messages — tests returning `Result` use `?` and auto-fail on `Err`.
- **Test output capture**: `cargo test` captures stdout by default. Use `cargo test -- --nocapture` to see debug output. In CI, use `-- --show-output` for a cleaner display.
- **Slow vs fast test separation**: Use `#[ignore]` for slow tests and run them explicitly: `cargo test -- --ignored`. Or use custom test categories with `#[cfg_attr(feature = "slow_tests", test)]` and feature flags.
- **Code coverage in Rust**: Use `cargo tarpaulin` or `cargo-llvm-cov` for code coverage. `cargo test` doesn't instrument for coverage — the binary must be compiled with `-Cinstrument-coverage` (nightly) or `--profile-coverage`.

## Related
- rust/web/axum-middleware.md
- rust/web/axum-auth.md
- rust/testing/mocking.md
