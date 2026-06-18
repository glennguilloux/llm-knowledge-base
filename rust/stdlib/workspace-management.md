---
id: "rust-stdlib-workspace-management"
title: "Rust Cargo Workspaces — Multi-Crate Project Management"
language: "rust"
category: "stdlib"
subcategory: "cargo"
tags: ["rust", "cargo", "workspace", "monorepo", "dependencies", "crates"]
version: "1.75+"
retrieval_hint: "Rust cargo workspace monorepo multi-crate dependency inheritance publish"
last_verified: "2026-05-25"
confidence: "high"
---

# Rust Cargo Workspaces — Multi-Crate Project Management

## When to Use
- Projects with multiple interdependent crates (library + binary + shared types)
- Separating public API from internal implementation crates
- Monorepos where you want shared dependency resolution
- Releasing multiple related crates that share a version cycle

## Standard Pattern

```toml
# Root Cargo.toml (workspace definition)
[workspace]
resolver = "2"  # Always use v2 resolver for workspaces

members = [
    "crates/core",       # Core library
    "crates/api",        # API layer (depends on core)
    "crates/cli",        # CLI binary (depends on core, api)
    "crates/derive",     # Proc-macro crate (separate compilation unit)
]

# Workspace-level metadata (inherited by member crates)
[workspace.package]
version = "0.1.0"
edition = "2021"
authors = ["Your Name <email@example.com>"]
license = "MIT"

[workspace.dependencies]
serde = { version = "1", features = ["derive"] }
tokio = { version = "1", features = ["full"] }
thiserror = "1"
anyhow = "1"
reqwest = { version = "0.12", features = ["json"] }
tracing = "0.1"
tracing-subscriber = "0.3"
```

```toml
# crates/core/Cargo.toml — uses workspace inheritance
[package]
name = "myapp-core"
version.workspace = true
edition.workspace = true
authors.workspace = true
license.workspace = true

[dependencies]
serde.workspace = true
thiserror.workspace = true
tracing.workspace = true
```

```toml
# crates/api/Cargo.toml — depends on core
[package]
name = "myapp-api"
version.workspace = true
edition.workspace = true

[dependencies]
myapp-core = { path = "../core" }
serde.workspace = true
tokio.workspace = true
reqwest.workspace = true
tracing.workspace = true
thiserror.workspace = true
```

```rust
// crates/core/src/lib.rs — shared core logic
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct User {
    pub id: u64,
    pub name: String,
    pub email: String,
}

#[derive(Debug, thiserror::Error)]
pub enum CoreError {
    #[error("validation error: {0}")]
    Validation(String),
    #[error("not found: {0}")]
    NotFound(String),
}
```

```rust
// crates/cli/src/main.rs — binary
use myapp_core::{CoreError, User};

fn main() -> Result<(), anyhow::Error> {
    println!("Hello from myapp!");
    Ok(())
}
```

## Common Mistakes

```rust
// WRONG: Cyclic dependency between workspace crates
// crate_a depends on crate_b
// crate_b depends on crate_a
// cargo will error: circular dependency detected

// WRONG: Forgetting "resolver = "2"" in workspace
// Without resolver = "2", cargo uses the v1 resolver which can
// unify features incorrectly across workspace members
// Always set: resolver = "2"

// WRONG: Publishing crates in wrong order
// If crate-b depends on crate-a, you MUST publish crate-a FIRST.
// Otherwise, when crate-b's publish resolves, it can't find crate-a on crates.io.

// CORRECT: Establish a publish order
// 1. myapp-core (no deps on other workspace crates)
// 2. myapp-derive (no deps)
// 3. myapp-api (depends on core)
// 4. myapp-cli (depends on core, api)

// WRONG: Workspace dependency unification creates unexpected version resolution
[workspace.dependencies]
tokio = { version = "1", features = ["full"] }

# If crate-a also adds tokio with "full" features, that's fine (they unify).
# But if crate-a adds tokio = "0.2" directly, cargo will build BOTH 1.x and 0.2!

// CORRECT: Use workspace dependencies for shared deps
// Let all crates get their tokio from the workspace to ensure a single version.

// WRONG: Using path = "..." in published workspace crates
myapp-core = { path = "../core" }  // Works locally but NOT on crates.io!

// CORRECT: Use workspace dependency + publish = false for internal crates
[workspace]
members = [
    "crates/core",
    "crates/cli",
]
# core is not published individually

// OR use conditional path/version:
myapp-core = { path = "../core", version = "0.1.0" }
// Local: uses path. Published: uses version.
```

## Gotchas
- **Proc-macro crates must be separate members:** Procedural macros require their own crate (they compile to a different compilation unit). Even in a workspace, a proc-macro crate cannot be a subdirectory of another crate. Always put them in `crates/derive/` as a separate member.
- **Feature unification is workspace-wide:** When crate A enables `tokio/full` and crate B enables `tokio/sync`, the workspace result is `tokio` with BOTH `full` AND `sync` features. This is correct for compilation but can lead to unexpected dependency bloat. Use `default-features = false` on workspace deps to control this.
- **`cargo publish` requires workspace coordination:** Publishing one crate from a workspace publishes ONLY that crate. If it depends on other workspace crates that aren't on crates.io yet, publish will fail. Use a script or `cargo release` to publish in order.
- **`cargo test` runs ALL workspace crates:** By default, `cargo test --workspace` tests everything. Use `cargo test -p myapp-core` to test a single crate. This is often needed for focused development.
- **Lockfile is at workspace root:** Only the root `Cargo.lock` matters. Individual crate `Cargo.lock` files inside the workspace are ignored. Run `cargo generate-lockfile` at the workspace root to update.

## Related
- rust/stdlib/modules-visibility.md
- rust/concurrency/async-tokio.md
