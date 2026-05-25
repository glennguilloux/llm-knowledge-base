---
id: "anti-patterns-rust"
title: "Rust Anti-Patterns"
language: "rust"
category: "anti-patterns"
subcategory: "rust"
tags: ["rust", "anti-pattern", "clone", "unwrap", "deref", "result"]
version: "1.75+"
retrieval_hint: "Rust anti-pattern unnecessary clone unwrap Deref inheritance ignore Result"
last_verified: "2026-05-24"
confidence: "high"
---

# Rust Anti-Patterns

## When to Use
- Code review: identifying common Rust mistakes
- Refactoring for idiomatic Rust
- Performance optimization (unnecessary allocations)
- Preventing panics in production

## Standard Pattern

See Common Mistakes below for WRONG/CORRECT code pairs.

## Common Mistakes

```rust
// WRONG: Unnecessary clones
fn process(user: &User) -> String {
    let name = user.name.clone();  // Unnecessary clone
    let email = user.email.clone();  // Unnecessary clone
    format!("{name} <{email}>")
}

// CORRECT: Borrow instead of clone
fn process(user: &User) -> String {
    format!("{} <{}>", user.name, user.email)
}

// WRONG: unwrap() in production code
fn parse_config(path: &str) -> Config {
    let content = std::fs::read_to_string(path).unwrap();  // Panics on error!
    serde_yaml::from_str(&content).unwrap()  // Panics on bad YAML!
}

// CORRECT: Propagate errors with ?
fn parse_config(path: &str) -> Result<Config, anyhow::Error> {
    let content = std::fs::read_to_string(path)?;
    Ok(serde_yaml::from_str(&content)?)
}

// WRONG: Using Deref for inheritance
struct Animal {
    name: String,
}

impl std::ops::Deref for Dog {
    type Target = Animal;
    fn deref(&self) -> &Animal {
        &self.base
    }
}
// Dog "inherits" Animal methods via Deref — confusing!

// CORRECT: Use composition with explicit methods
struct Dog {
    name: String,
    breed: String,
}

impl Dog {
    fn name(&self) -> &str { &self.name }
    fn breed(&self) -> &str { &self.breed }
}

// WRONG: Ignoring Result
let file = std::fs::File::open("data.txt");  // Result ignored!
// compiler warning: unused Result

// CORRECT: Handle or propagate
let file = std::fs::File::open("data.txt")?;
// Or: let file = match std::fs::File::open("data.txt") { ... };

// WRONG: Using String when &str suffices
fn greet(name: String) -> String {  // Takes ownership unnecessarily
    format!("Hello, {name}")
}
greet(name.to_string())  // Caller must allocate

// CORRECT: Borrow with &str
fn greet(name: &str) -> String {
    format!("Hello, {name}")
}
greet(&name)  // No allocation needed

// WRONG: Match exhaustiveness bypassed
match value {
    1 => do_something(),
    2 => do_other(),
    _ => {},  // Silently ignores all other cases
}

// CORRECT: Handle or log unexpected values
match value {
    1 => do_something(),
    2 => do_other(),
    other => eprintln!("Unexpected value: {other}"),
}
```

## Gotchas
- `.clone()` is often unnecessary — prefer borrowing (`&T`) when possible
- `unwrap()` panics on `None`/`Err` — use `?` or `expect()` with context
- `Deref` polymorphism is an anti-pattern — Rust favors composition over inheritance
- Ignoring `Result` with `let _ = ...` hides errors — use `?` or explicit handling
- `String` vs `&str`: prefer `&str` in function parameters (accepts both `String` and `&str`)
- `to_string()` allocates — use `format!()` or `String::from()` when clearer
- Match `_` arm silently catches all cases — be explicit about what you're ignoring
- `Box<dyn Error>` loses type information — use `anyhow` or custom error types

## Related
- rust/stdlib/error-crates.md
- rust/stdlib/ownership.md
- rust/stdlib/iterators-closures.md
