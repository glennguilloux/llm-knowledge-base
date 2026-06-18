---
id: "rust-concurrency-async-traits"
title: "Async Traits in Rust — Patterns and Limitations"
language: "rust"
category: "concurrency"
subcategory: "async"
tags: ["rust", "async", "traits", "async-trait", "rprit", "impl-trait", "dyn"]
version: "1.75+"
retrieval_hint: "Rust async traits async-trait crate RPITIT dyn compatibility Send bounds"
last_verified: "2026-05-25"
confidence: "high"
---

# Async Traits in Rust — Patterns and Limitations

## When to Use
- Defining async behavior in shared interfaces (repositories, services, handlers)
- Building trait-based abstractions over async I/O operations
- Writing middleware or plugin systems that need async dispatch
- API boundaries where you want to abstract over different async implementations

## Standard Pattern

```rust
use std::future::Future;

// --- Approach 1: #[async_trait] crate (stable, works everywhere) ---
use async_trait::async_trait;

#[async_trait]
pub trait Repository {
    /// Find a user by ID. #[async_trait] desugars this into
    /// fn find_by_id(&self, id: u64) -> Pin<Box<dyn Future<Output = Result<User, Error>> + Send>>;
    async fn find_by_id(&self, id: u64) -> Result<User, Error>;

    /// Returns all users. The returned future must be Send (for spawn).
    async fn find_all(&self) -> Result<Vec<User>, Error>;
}

pub struct PostgresRepository {
    pool: sqlx::PgPool,
}

#[async_trait]
impl Repository for PostgresRepository {
    async fn find_by_id(&self, id: u64) -> Result<User, Error> {
        sqlx::query_as("SELECT * FROM users WHERE id = $1")
            .bind(id as i64)
            .fetch_one(&self.pool)
            .await
            .map_err(Error::from)
    }

    async fn find_all(&self) -> Result<Vec<User>, Error> {
        sqlx::query_as("SELECT * FROM users")
            .fetch_all(&self.pool)
            .await
            .map_err(Error::from)
    }
}

// --- Approach 2: Native async fn in trait (Rust 1.75+ / nightly) ---
// Requires: #![feature(async_fn_in_trait)] on nightly, or 1.75+ with limitations

pub trait AsyncProcessor {
    async fn process(&self, input: &str) -> Result<String, Error>;
}

// With RPITIT (Return Position Impl Trait In Traits), stable since 1.75:
pub trait AsyncIterator {
    type Item;

    /// Returns a future that resolves to the next item.
    /// The -> impl Future syntax is the stable way (1.75+)
    fn next(&mut self) -> impl Future<Output = Option<Self::Item>> + Send;
}

// --- Practical: Polymorphic async dispatch ---

// Using #[async_trait] for trait objects (dynamic dispatch)
#[async_trait]
pub trait Notifier: Send + Sync {
    async fn notify(&self, message: &str) -> Result<(), Error>;
}

pub struct EmailNotifier { /* ... */ }
pub struct SmsNotifier { /* ... */ }

#[async_trait]
impl Notifier for EmailNotifier {
    async fn notify(&self, message: &str) -> Result<(), Error> {
        println!("Email: {}", message);
        Ok(())
    }
}

#[async_trait]
impl Notifier for SmsNotifier {
    async fn notify(&self, message: &str) -> Result<(), Error> {
        println!("SMS: {}", message);
        Ok(())
    }
}

// Vec<Box<dyn Notifier>> — works with #[async_trait], NOT with native async fn in trait
async fn notify_all(notifiers: &[Box<dyn Notifier>], message: &str) -> Result<(), Error> {
    for notifier in notifiers {
        notifier.notify(message).await?;
    }
    Ok(())
}
```

## Common Mistakes

```rust
// WRONG: #[async_trait] without Send bound — can't be used with tokio::spawn
#[async_trait]
pub trait MyTrait {
    async fn do_stuff(&self);  // Future is NOT Send by default
}

// CORRECT: Add Send bound explicitly when needed with tokio::spawn
#[async_trait]
pub trait MyTrait: Send {
    async fn do_stuff(&self); // Now the future is Send
}

// Alternatively, use Send bound on the method:
#[async_trait]
pub trait MyTrait {
    async fn do_stuff(&self) where Self: Sync;
}

// WRONG: Mixing native async fn with dyn dispatch (doesn't work)
pub trait NativeAsync {
    async fn process(&self);  // Native async fn in trait
}

// This compiles... but you CANNOT use it as a trait object:
// fn use_dyn(x: &dyn NativeAsync) { ... }  // ERROR: doesn't work

// CORRECT: Use #[async_trait] when you need dyn dispatch
#[async_trait]
pub trait AsyncDyn: Send {
    async fn process(&self);
}

fn use_dyn(x: &dyn AsyncDyn) { /* works */ }

// WRONG: Forgetting the Send bound — future can't be spawned
#[async_trait]
pub trait Worker {
    async fn work(&self) -> Result<(), Error>;
}

async fn run_worker(worker: impl Worker) {
    tokio::spawn(async move {
        worker.work().await // ERROR: future is not Send!
    });
}

// CORRECT: Add Send bound
#[async_trait]
pub trait Worker: Send {
    async fn work(&self) -> Result<(), Error>;
}
```

## Gotchas
- **`#[async_trait]` boxes the future:** The macro desugars `async fn` into `Pin<Box<dyn Future + Send>>`. This means a heap allocation per call. For hot paths, consider using native async fn in trait (when stable) or manual desugaring.
- **Send bounds are NOT automatic:** `#[async_trait]` without explicit `Send` on the trait produces non-Send futures. For tokio (which requires Send), always add `: Send` to your trait or `+ Send` at the method level.
- **Native async fn in trait (1.75+) cannot be used as trait objects:** Traits with native async methods cannot produce `dyn Trait` objects. Use `#[async_trait]` or the `async-trait` crate if you need dynamic dispatch.
- **RPITIT (1.75+) has lifetime capturing complexity:** When returning `-> impl Future<'_>`, the lifetime of the returned future is tied to `&self`. This is correct but can cause confusing borrow-checker errors. Use `async-trait` if you hit lifetime issues.
- **Tooling support varies:** `rust-analyzer` handles `#[async_trait]` well but may struggle with native async fn in trait in some IDE operations (rename, go-to-definition).

## Related
- rust/concurrency/async-tokio.md
- rust/stdlib/traits.md
