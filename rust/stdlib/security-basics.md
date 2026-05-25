---
id: "rust-stdlib-security-basics"
title: "Rust Security Basics: Input Validation, SQL Injection, Hashing, Random Generation, Unsafe"
language: "rust"
category: "stdlib"
tags: ["security", "input-validation", "sql-injection", "argon2", "rand", "unsafe", "crypto"]
version: "1.75+"
retrieval_hint: "Rust security input validation SQL injection argon2 password hashing unsafe block rand"
last_verified: "2026-05-24"
confidence: "high"
---

# Rust Security Basics

## When to Use
- Building web services that accept user input
- Storing passwords or API keys securely
- Connecting to databases with dynamic queries
- Generating secure random tokens (session IDs, CSRF tokens)
- Writing or reviewing `unsafe` code blocks

## Standard Pattern

```rust
use argon2::{
    password_hash::{rand_core::OsRng, PasswordHash, PasswordHasher, PasswordVerifier, SaltString},
    Argon2,
};
use rand::RngCore;
use regex::Regex;
use sqlx::{PgPool, Row};
use std::fmt;
use thiserror::Error;

// --- Input Validation ---

#[derive(Debug, Error)]
pub enum ValidationError {
    #[error("Field '{field}': {message}")]
    Invalid { field: String, message: String },
}

fn validate_email(email: &str) -> Result<String, ValidationError> {
    let email = email.trim();
    if email.is_empty() {
        return Err(ValidationError::Invalid {
            field: "email".into(),
            message: "cannot be empty".into(),
        });
    }
    if email.len() > 254 {
        return Err(ValidationError::Invalid {
            field: "email".into(),
            message: "exceeds maximum length of 254".into(),
        });
    }
    // Simple but effective email regex
    let re = Regex::new(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$").unwrap();
    if !re.is_match(email) {
        return Err(ValidationError::Invalid {
            field: "email".into(),
            message: "invalid format".into(),
        });
    }
    Ok(email.to_lowercase())
}

fn validate_username(username: &str) -> Result<String, ValidationError> {
    let username = username.trim();
    if username.len() < 3 || username.len() > 32 {
        return Err(ValidationError::Invalid {
            field: "username".into(),
            message: "must be 3-32 characters".into(),
        });
    }
    let re = Regex::new(r"^[a-zA-Z0-9_]+$").unwrap();
    if !re.is_match(username) {
        return Err(ValidationError::Invalid {
            field: "username".into(),
            message: "only alphanumeric and underscore allowed".into(),
        });
    }
    Ok(username.to_string())
}

// --- SQL Injection Prevention with SQLx ---

#[derive(Debug, Error)]
pub enum UserError {
    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),
    #[error("Validation error: {0}")]
    Validation(#[from] ValidationError),
    #[error("Not found")]
    NotFound,
}

pub struct UserStore {
    pool: PgPool,
}

impl UserStore {
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }

    // SQLx uses compile-time checked queries with parameter binding
    pub async fn find_by_email(&self, email: &str) -> Result<Option<User>, UserError> {
        let user = sqlx::query_as::<_, User>(
            "SELECT id, email, username FROM users WHERE email = $1",
        )
        .bind(email)  // Parameterized — safe from SQL injection
        .fetch_optional(&self.pool)
        .await?;

        Ok(user)
    }

    pub async fn create(&self, email: &str, username: &str) -> Result<i64, UserError> {
        let row = sqlx::query(
            "INSERT INTO users (email, username) VALUES ($1, $2) RETURNING id",
        )
        .bind(email)
        .bind(username)
        .fetch_one(&self.pool)
        .await?;

        let id: i64 = row.get("id");
        Ok(id)
    }
}

#[derive(Debug, sqlx::FromRow)]
pub struct User {
    pub id: i64,
    pub email: String,
    pub username: String,
}

// --- Password Hashing with Argon2 ---

#[derive(Debug, Error)]
pub enum PasswordError {
    #[error("Hashing failed: {0}")]
    Hash(String),
    #[error("Verification failed: {0}")]
    Verify(String),
}

pub fn hash_password(password: &str) -> Result<String, PasswordError> {
    let salt = SaltString::generate(&mut OsRng);
    let argon2 = Argon2::default();

    let password_hash = argon2
        .hash_password(password.as_bytes(), &salt)
        .map_err(|e| PasswordError::Hash(e.to_string()))?;

    Ok(password_hash.to_string())
}

pub fn verify_password(password: &str, hash: &str) -> Result<bool, PasswordError> {
    let parsed_hash = PasswordHash::new(hash)
        .map_err(|e| PasswordError::Verify(e.to_string()))?;

    let argon2 = Argon2::default();
    match argon2.verify_password(password.as_bytes(), &parsed_hash) {
        Ok(()) => Ok(true),
        Err(argon2::password_hash::Error::Password) => Ok(false),
        Err(e) => Err(PasswordError::Verify(e.to_string())),
    }
}

// --- Secure Random Generation ---

pub fn generate_session_token() -> String {
    let mut bytes = [0u8; 32];
    OsRng.fill_bytes(&mut bytes);
    base64::encode(&bytes)
}

pub fn generate_csrf_token() -> String {
    let mut bytes = [0u8; 16];
    OsRng.fill_bytes(&mut bytes);
    hex::encode(&bytes)
}

// --- Unsafe Block Guidelines ---

// Safe wrapper around unsafe operation
pub fn safe_slice_copy(src: &[u8], dst: &mut [u8]) -> Result<(), &'static str> {
    if src.len() != dst.len() {
        return Err("src and dst must have equal length");
    }

    // SAFETY: We've verified lengths match, and both slices are valid
    unsafe {
        std::ptr::copy_nonoverlapping(src.as_ptr(), dst.as_mut_ptr(), src.len());
    }

    Ok(())
}

// Documenting unsafe invariants
/// # Safety
/// - `ptr` must be valid for reads of `count` bytes
/// - `ptr` must be properly aligned
pub unsafe fn read_bytes(ptr: *const u8, count: usize) -> Vec<u8> {
    std::slice::from_raw_parts(ptr, count).to_vec()
}

// Minimal unsafe — isolate it in a small function
pub fn parse_u32_be(bytes: &[u8]) -> Option<u32> {
    if bytes.len() < 4 {
        return None;
    }
    // SAFETY: We checked length >= 4, and bytes is a valid slice
    let val = unsafe { u32::from_be_bytes(*(bytes.as_ptr() as *const [u8; 4])) };
    Some(val)
}

// Base64 encoding helper (simplified — use base64 crate in production)
mod base64 {
    const ALPHABET: &[u8] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

    pub fn encode(input: &[u8]) -> String {
        let mut result = String::with_capacity((input.len() + 2) / 3 * 4);
        for chunk in input.chunks(3) {
            let b = match chunk.len() {
                1 => [chunk[0], 0, 0],
                2 => [chunk[0], chunk[1], 0],
                3 => [chunk[0], chunk[1], chunk[2]],
                _ => unreachable!(),
            };
            result.push(ALPHABET[(b[0] >> 2) as usize] as char);
            result.push(ALPHABET[(((b[0] & 0x3) << 4) | (b[1] >> 4)) as usize] as char);
            result.push(if chunk.len() > 1 { ALPHABET[(((b[1] & 0xf) << 2) | (b[2] >> 6)) as usize] } else { b'=' } as char);
            result.push(if chunk.len() > 2 { ALPHABET[(b[2] & 0x3f) as usize] } else { b'=' } as char);
        }
        result
    }
}

mod hex {
    pub fn encode(bytes: &[u8]) -> String {
        bytes.iter().map(|b| format!("{:02x}", b)).collect()
    }
}
```

## Common Mistakes

```rust
// WRONG: String formatting in SQL queries
let query = format!("SELECT * FROM users WHERE email = '{}'", email);
// Attacker: email = "'; DROP TABLE users; --"

// CORRECT: Parameterized queries with SQLx
let user = sqlx::query_as::<_, User>("SELECT * FROM users WHERE email = $1")
    .bind(email)
    .fetch_optional(&pool)
    .await?;

// WRONG: Using rand::thread_rng() for security tokens
use rand::Rng;
let token: String = rand::thread_rng()
    .sample_iter(&rand::distributions::Alphanumeric)
    .take(32)
    .map(char::from)
    .collect();
// thread_rng is NOT cryptographically secure for session tokens

// CORRECT: Use OsRng for security-sensitive random data
use rand::RngCore;
let mut bytes = [0u8; 32];
OsRng.fill_bytes(&mut bytes);
let token = base64::encode(&bytes);

// WRONG: Using unsafe without documenting invariants
pub fn get_element(ptr: *const i32, index: usize) -> i32 {
    unsafe { *ptr.offset(index as isize) }  // No safety docs, no checks
}

// CORRECT: Document safety requirements and minimize unsafe surface
/// # Safety
/// `ptr` must point to an array of at least `index + 1` valid i32 values
pub unsafe fn get_element(ptr: *const i32, index: usize) -> i32 {
    *ptr.add(index)
}

// WRONG: Storing passwords with a fast hash (SHA-256, MD5)
use sha2::{Sha256, Digest};
let mut hasher = Sha256::new();
hasher.update(password);
let hash = format!("{:x}", hasher.finalize());
// Fast hashes are designed to be fast — bad for password storage

// CORRECT: Use Argon2 (memory-hard, designed for password hashing)
let hash = hash_password(password)?;

// WRONG: Using blacklist for input validation
if !email.contains("<script>") {  // Bypassed easily
    // "safe"
}

// CORRECT: Use whitelist validation
let re = Regex::new(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$").unwrap();
if !re.is_match(email) {
    return Err(ValidationError::Invalid { field: "email".into(), message: "invalid".into() });
}
```

## Gotchas
- `OsRng` is the only cryptographically secure RNG in the Rust ecosystem — `thread_rng()` is NOT suitable for passwords, tokens, or secrets
- Argon2id is the recommended variant (used by `Argon2::default()`) — it resists both GPU and side-channel attacks
- SQLx `$1, $2` syntax is for PostgreSQL; MySQL/SQLite use `?` placeholders — the driver handles escaping
- `unsafe` doesn't disable the borrow checker — it only allows raw pointer dereferencing, calling unsafe functions, and accessing mutable statics
- Every `unsafe` block should have a `/// # Safety` comment documenting the invariants the caller must uphold
- Isolate `unsafe` in the smallest possible function — never spread it across a large function
- `PasswordHash::new()` parses the encoded hash string (includes algorithm, version, salt, hash) — don't try to manually split it
- Input validation regexes should be compiled once (lazy_static or once_cell), not per-request
- The `sqlx::query!` macro checks SQL at compile time against a live database — use it for maximum safety

## Related
- rust/stdlib/error-handling.md
- rust/stdlib/result-option.md
- patterns/input-validation.md
- patterns/rate-limiting.md
