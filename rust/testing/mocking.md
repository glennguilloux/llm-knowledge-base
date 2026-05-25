---
id: "rust-testing-mocking"
title: "Rust Mocking with Mockall: Trait-Based Mock Objects"
language: "rust"
category: "testing"
subcategory: "unit-testing"
tags: ["rust", "mocking", "mockall", "trait", "unit-testing", "dependency-injection"]
version: "latest"
retrieval_hint: "Rust mocking Mockall trait automock expectation predicate dependency injection unit test"
last_verified: "2026-05-24"
confidence: "high"
---

# Rust Mocking with Mockall: Trait-Based Mock Objects

## When to Use
- Unit testing code that depends on external services (database, HTTP, filesystem)
- Isolating business logic from infrastructure concerns
- Testing error paths that are hard to trigger with real implementations
- Verifying specific method calls and argument patterns

## Standard Pattern

### Basic Mock with `#[automock]`

```rust
// --- src/db.rs ---
use mockall::automock;

#[automock]
pub trait UserRepository {
    fn find_by_id(&self, id: u64) -> Result<User, DbError>;
    fn save(&self, user: &User) -> Result<u64, DbError>;
    fn delete(&self, id: u64) -> Result<(), DbError>;
}

#[derive(Debug, Clone, PartialEq)]
pub struct User {
    pub id: u64,
    pub name: String,
    pub email: String,
}

#[derive(Debug)]
pub enum DbError {
    NotFound,
    ConnectionFailed,
    ConstraintViolation,
}

// --- src/service.rs ---
use crate::db::{User, UserRepository, DbError};

pub struct UserService<R: UserRepository> {
    repo: R,
}

impl<R: UserRepository> UserService<R> {
    pub fn new(repo: R) -> Self {
        Self { repo }
    }

    pub fn get_user_display(&self, id: u64) -> Result<String, DbError> {
        let user = self.repo.find_by_id(id)?;
        Ok(format!("{} <{}>", user.name, user.email))
    }

    pub fn register_user(&self, name: &str, email: &str) -> Result<u64, DbError> {
        if name.is_empty() || email.is_empty() {
            return Err(DbError::ConstraintViolation);
        }
        let user = User {
            id: 0,
            name: name.to_string(),
            email: email.to_string(),
        };
        self.repo.save(&user)
    }
}
```

### Writing Tests

```rust
// --- tests/service_tests.rs ---
use mockall::predicate::*;
use crate::db::{MockUserRepository, User, DbError};
use crate::service::UserService;

#[test]
fn test_get_user_display_success() {
    let mut mock_repo = MockUserRepository::new();
    mock_repo
        .expect_find_by_id()
        .with(eq(42))
        .times(1)
        .returning(|_| Ok(User {
            id: 42,
            name: "Alice".into(),
            email: "alice@example.com".into(),
        }));

    let service = UserService::new(mock_repo);
    let result = service.get_user_display(42);
    assert_eq!(result.unwrap(), "Alice <alice@example.com>");
}

#[test]
fn test_get_user_display_not_found() {
    let mut mock_repo = MockUserRepository::new();
    mock_repo
        .expect_find_by_id()
        .returning(|_| Err(DbError::NotFound));

    let service = UserService::new(mock_repo);
    assert!(matches!(service.get_user_display(99), Err(DbError::NotFound)));
}

#[test]
fn test_register_user_calls_save() {
    let mut mock_repo = MockUserRepository::new();
    mock_repo
        .expect_save()
        .with(function(|user: &User| {
            user.name == "Bob" && user.email == "bob@example.com"
        }))
        .times(1)
        .returning(|_| Ok(1));

    let service = UserService::new(mock_repo);
    let result = service.register_user("Bob", "bob@example.com");
    assert_eq!(result.unwrap(), 1);
}

#[test]
fn test_register_user_empty_name_returns_error() {
    let mock_repo = MockUserRepository::new();
    // No expectations set — save() should never be called
    let service = UserService::new(mock_repo);
    assert!(matches!(
        service.register_user("", "bob@example.com"),
        Err(DbError::ConstraintViolation)
    ));
}
```

### Mocking with Context

```rust
use mockall::automock;
use mockall::predicate::*;

#[automock]
pub trait EmailSender {
    fn send_email(&self, to: &str, subject: &str, body: &str) -> Result<(), String>;
}

#[test]
fn test_welcome_email_is_sent() {
    let mut mock_sender = MockEmailSender::new();
    mock_sender
        .expect_send_email()
        .with(
            eq("alice@example.com"),
            eq("Welcome!"),
            always(),  // Don't care about body content
        )
        .times(1)
        .returning(|_, _, _| Ok(()));

    // Use mock_sender in service
}
```

## Common Mistakes

```rust
// WRONG: Trying to mock a concrete struct instead of a trait
struct Database { /* fields */ }
impl Database {
    fn query(&self, sql: &str) -> Vec<Row> { /* ... */ }
}
// Cannot derive a mock for Database — Mockall needs traits

// CORRECT: Define a trait, implement it for the struct
#[automock]
pub trait DatabaseOps {
    fn query(&self, sql: &str) -> Vec<Row>;
}

impl DatabaseOps for Database {
    fn query(&self, sql: &str) -> Vec<Row> {
        // real implementation
    }
}
// Now MockDatabaseOps is available for tests
```

```rust
// WRONG: Using .returning() with a closure that borrows local data
let name = String::from("Alice");
mock_repo
    .expect_find_by_id()
    .returning(|_| Ok(User {
        id: 1,
        name: name.clone(),  // ERROR: cannot borrow `name` in closure
        email: "".into(),
    }));

// CORRECT: Use return_once or move the data
mock_repo
    .expect_find_by_id()
    .return_once(|_| Ok(User {
        id: 1,
        name: "Alice".into(),
        email: "alice@example.com".into(),
    }));
// OR use return_const for repeated calls

// WRONG: Forgetting .returning() on an expectation
let mut mock_repo = MockUserRepository::new();
mock_repo
    .expect_find_by_id()
    .with(eq(42));
    // Missing .returning() — panics at runtime with "expected ... but got no return value set"

// CORRECT: Always set a return value
let mut mock_repo = MockUserRepository::new();
mock_repo
    .expect_find_by_id()
    .with(eq(42))
    .returning(|_| Ok(User {
        id: 42,
        name: "Alice".into(),
        email: "alice@example.com".into(),
    }));
```

## Gotchas
- `#[automock]` generates a `Mock<TraitName>` struct automatically — no manual mock implementation needed, but the trait must have `'static` lifetime bounds for owned types
- Mock expectations are checked on drop — if you forget to verify, the test passes silently; use `.times(n)` to enforce call counts
- `predicate::function` closures can't be serialized in error messages — prefer `eq()` and `ne()` for readable failure output
- Each mock method gets its own expectation chain — calling `.expect_method()` twice overwrites the first; use `.times()` for multiple calls
- `Mockall` generates mocks at compile time — large traits with many methods significantly increase compile time
- `return_once` panics if called more than once — use `returning` for methods expected to be called multiple times
- The mock's `Drop` impl verifies expectations — if you need to inspect failures, call `checkpoint()` before the mock goes out of scope
- Generic traits require specifying concrete types in tests: `MockGenericTrait::<ConcreteType>::new()`

## Related
- rust/testing/patterns.md
- go/testing/mocking.md
