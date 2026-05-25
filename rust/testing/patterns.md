---
id: "rust-testing-patterns"
title: "Rust Testing Patterns"
language: "rust"
category: "testing"
subcategory: "unit-testing"
tags: ["rust", "testing", "test", "integration", "property", "mock", "assert"]
version: "1.75+"
retrieval_hint: "Rust testing #[test] integration property mock assert macro"
last_verified: "2026-05-24"
confidence: "high"
---

# Rust Testing Patterns

## When to Use
- Unit testing functions and methods
- Integration tests across modules
- Property-based testing with proptest
- Mocking dependencies for isolated tests

## Standard Pattern

```rust
// --- Unit tests (in same file) ---
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_addition() {
        assert_eq!(add(2, 3), 5);
    }

    #[test]
    fn test_error_case() {
        let result = divide(10, 0);
        assert!(result.is_err());
    }

    #[test]
    fn test_with_message() {
        let result = parse_number("42");
        assert!(result.is_ok(), "Expected Ok, got {:?}", result);
        assert_eq!(result.unwrap(), 42);
    }

    #[test]
    #[should_panic(expected = "divide by zero")]
    fn test_panic() {
        divide(1, 0).unwrap();
    }

    #[test]
    fn test_option() {
        let result = find_user(999);
        assert!(result.is_none());
    }
}

// --- Integration tests (tests/ directory) ---
// tests/api_test.rs
use mylib::UserService;

#[tokio::test]
async fn test_create_and_get_user() {
    let pool = create_test_pool().await;
    let service = UserService::new(pool);

    let user = service.create("Alice", "alice@test.com").await.unwrap();
    assert_eq!(user.name, "Alice");

    let found = service.get(user.id).await.unwrap().unwrap();
    assert_eq!(found.email, "alice@test.com");
}

// --- Test helpers ---
fn create_test_pool() -> PgPool {
    // Use testcontainers or in-memory DB
    PgPool::connect("sqlite::memory:").await.unwrap()
}

// --- Property-based testing with proptest ---
use proptest::prelude::*;

proptest! {
    #[test]
    fn test_reverse_twice_is_identity(s in ".*") {
        let reversed: String = s.chars().rev().collect();
        let double_reversed: String = reversed.chars().rev().collect();
        prop_assert_eq!(s, double_reversed);
    }

    #[test]
    fn test_parse_never_panics(n in 0i64..1000000) {
        let result = std::panic::catch_unwind(|| {
            format!("{}", n);
        });
        prop_assert!(result.is_ok());
    }
}

// --- Mock with mockall ---
use mockall::automock;

#[automock]
trait UserRepository {
    fn find_by_id(&self, id: i64) -> Result<Option<User>, Error>;
    fn create(&self, name: &str, email: &str) -> Result<User, Error>;
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_with_mock() {
        let mut mock = MockUserRepository::new();
        mock.expect_find_by_id()
            .with(eq(1))
            .returning(|_| Ok(Some(User { id: 1, name: "Alice".into() })));

        let result = mock.find_by_id(1).unwrap();
        assert!(result.is_some());
    }
}
```

## Common Mistakes

```rust
// WRONG: Test function not marked with #[test]
fn test_something() {  // Not discovered by cargo test!
    assert_eq!(1, 1);
}

// CORRECT: Always add #[test]
#[test]
fn test_something() {
    assert_eq!(1, 1);
}

// WRONG: Using assert_eq for floating point
assert_eq!(0.1 + 0.2, 0.3);  // Fails due to precision!

// CORRECT: Use approximate comparison
assert!((0.1 + 0.2 - 0.3).abs() < f64::EPSILON);

// WRONG: Test depends on execution order
#[test]
fn test_create() {
    let user = create("Alice");
    // user.id used in next test
}

// CORRECT: Each test is independent
#[test]
fn test_create_and_find() {
    let user = create("Alice");
    let found = find(user.id);
    assert_eq!(found.name, "Alice");
}
```

## Gotchas
- `cargo test` runs all tests in `src/` (unit) and `tests/` (integration)
- `#[test]` functions must be in `#[cfg(test)]` modules (in `src/`)
- Integration tests in `tests/` are separate crates — import your lib with `use mylib::...`
- `#[tokio::test]` for async tests (requires tokio feature)
- `assert_eq!` and `assert_ne!` print both values on failure
- `#[should_panic]` verifies that a panic occurs — use `expected` for specific messages
- `cargo test -- --nocapture` shows `println!` output during tests
- `proptest` generates random inputs — useful for edge case discovery

## Related
- rust/stdlib/error-crates.md
- rust/web/axum-deep.md
- rust/stdlib/result-option.md
