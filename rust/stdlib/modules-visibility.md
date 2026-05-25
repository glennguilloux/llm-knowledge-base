---
id: "rust-stdlib-modules-visibility"
title: "Rust Modules, Visibility, and Crate Structure"
language: "rust"
category: "stdlib"
subcategory: "modules"
tags: ["rust", "module", "visibility", "pub", "use", "crate", "super", "re-export"]
version: "1.75+"
retrieval_hint: "Rust mod pub use super crate module visibility re-export file hierarchy"
last_verified: "2026-05-24"
confidence: "high"
---

# Rust Modules, Visibility, and Crate Structure

## When to Use

- `mod`: Declare a module (inline or from a file)
- `pub`: Make an item visible outside its module
- `use`: Bring items into scope (shorten long paths)
- `super`: Access the parent module (relative path)
- `crate`: Access the root of the current crate (absolute path)
- `pub use`: Re-export an item under a different path (API reshaping)
- Module file conventions: `mod.rs` (old style) or `module_name.rs` + `module_name/` directory (Rust 2018+)

## Standard Pattern

Assume this file tree:
```text
src/
  main.rs
  lib.rs
  models/
    mod.rs          (or: models.rs + models/ directory)
    user.rs
    order.rs
  services/
    mod.rs
    auth.rs
```

```rust
// --- src/main.rs ---
// Declare the `models` module (compiler looks for src/models/mod.rs or src/models.rs)
mod models;
mod services;

// Bring specific items into scope
use crate::models::user::User;
use crate::services::auth::AuthService;

fn main() {
    let user = User::new("Alice");
    let auth = AuthService::new();
    println!("{:?}", user);
}


// --- src/models/mod.rs (or src/models.rs, which declares submodule directory) ---
// Declare submodules
pub mod user;
pub mod order;

// Re-export user::User so callers can use `models::User` instead of `models::user::User`
pub use user::User;


// --- src/models/user.rs ---
#[derive(Debug)]
pub struct User {
    name: String,
    // Private field — not accessible outside this module
    created_at: u64,
}

impl User {
    pub fn new(name: &str) -> Self {
        User {
            name: name.to_string(),
            created_at: 0,
        }
    }
}


// --- src/models/order.rs ---
#[derive(Debug)]
pub struct Order {
    pub id: u64,
    pub user_name: String,
    pub amount: f64,
}


// --- src/services/mod.rs ---
pub mod auth;

// Re-export at a higher level
pub use auth::AuthService;


// --- src/services/auth.rs ---
// Private helper function
fn hash_password(pw: &str) -> String {
    format!("hashed_{}", pw)
}

pub struct AuthService {
    secret: String, // private
}

impl AuthService {
    pub fn new() -> Self {
        AuthService { secret: "key".to_string() }
    }

    pub fn authenticate(&self, _user: &str, _password: &str) -> bool {
        let _hashed = hash_password(_password);
        true
    }
}


// --- Visibility reference ---
mod demo {
    // Private: only visible within `demo`
    fn private_fn() {}

    // Public: visible to parent module (and beyond, if parent re-exports)
    pub fn public_fn() {}

    // Visible to parent module only (pub(super))
    pub(super) fn parent_visible() {}

    // Visible within the current crate only (pub(crate))
    pub(crate) fn crate_wide() {}

    // Visible to a specific ancestor module
    pub(in crate::models) fn models_only() {}

    pub struct Example {
        pub name: String,         // public field
        pub(crate) count: u32,    // crate-visible field
        internal: bool,           // private field
    }

    impl Example {
        pub fn new(name: &str) -> Self {
            Example {
                name: name.to_string(),
                count: 0,
                internal: true,
            }
        }
    }
}
```

## Common Mistakes

```rust
// WRONG: Using a private item from outside its module
// In models/user.rs:
fn internal_helper() -> bool { true }

// In main.rs:
// let result = models::user::internal_helper(); // ERROR: function is private

// CORRECT: Mark the item as pub if it should be accessible
// In models/user.rs:
pub fn internal_helper() -> bool { true }


// WRONG: Using super:: to go up too many levels
// In src/models/order.rs:
// let data = super::super::config::SETTINGS; // Fragile and unclear

// CORRECT: Use crate:: for clear absolute paths
// In src/models/order.rs:
// let data = crate::config::SETTINGS;


// WRONG: Forgetting that re-export (pub use) is needed to shorten paths
// src/models/mod.rs
pub mod user;
// Caller must use: crate::models::user::User  (long path)

// CORRECT: Re-export to provide a cleaner API
// src/models/mod.rs
pub use user::User;
// Caller can now use: crate::models::User


// WRONG: Declaring mod twice (once via mod.rs and once explicitly)
// src/models/mod.rs
pub mod user;       // OK: declares that user.rs is a submodule

// src/main.rs
mod models;
mod user; // ERROR: conflicting module declarations

// CORRECT: Only declare each module once in the tree
// src/lib.rs or src/main.rs: mod models;
// src/models/mod.rs: pub mod user;


// WRONG: Assuming pub makes a struct's fields public
pub struct Config {
    pub host: String,  // public
    port: u16,          // private! Not accessible outside module
}

// Caller:
// let mut c = services::Config { host: "localhost".into(), port: 8080 };
// ERROR: field `port` is private

// CORRECT: Mark all fields that should be public, or provide setters
pub struct Config {
    pub host: String,
    pub port: u16, // Now this is public too
}


// WRONG: Confusing file paths with module paths
// Thinking `src/models/user.rs` means the module path is `models::user`
// But if declared as `pub mod user;` inside `models/mod.rs`, the path IS `crate::models::user`
// If `main.rs` has `mod models`, the compiler looks for:
//   - src/models.rs (and submodules in src/models/)
//   - src/models/mod.rs

// CORRECT: Follow Rust's module-file mapping:
// mod foo;  -> looks for foo.rs or foo/mod.rs in the same directory
```

## Gotchas
- By default, everything in Rust is **private** — `pub` is the only way to expose it; there is no "protected" or "internal" keyword in the object-oriented sense
- `pub(crate)` is often overlooked — it makes an item available anywhere within the crate without exposing it in the public API
- `pub(super)` restricts visibility to the immediate parent — useful for internal helpers shared between sibling submodules
- Struct fields have independent visibility from the struct itself: `pub struct Foo { priv_field: i32 }` means outside code can construct the struct via `pub fn new()` but cannot directly access `priv_field`
- `use` is purely a scope convenience — it does not re-export; `pub use` re-exports, making the item accessible through a different path
- Module declaration (`mod foo;`) and import (`use foo::Bar;`) are fundamentally different statements — `mod` tells the compiler to include a file, `use` just brings a name into scope
- Inline modules (`mod foo { ... }`) and file-based modules (`mod foo;` pointing to `foo.rs`) are semantically equivalent — the compiler treats `mod foo;` as if you wrote `#[path = "foo.rs"] mod foo { /* contents of foo.rs */ }`
- In Cargo workspaces, each crate has its own module tree — `crate::` in crate A refers to a different root than `crate::` in crate B

## Related
- rust/stdlib/lifetimes.md
- rust/stdlib/error-handling.md
