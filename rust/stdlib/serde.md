---
id: "rust-stdlib-serde"
title: "Serialization with Serde"
language: "rust"
category: "stdlib"
tags: ["serde", "serialization", "json", "deserialization", "derive"]
version: "1.75+"
retrieval_hint: "serde Serialize Deserialize json serialization derive custom"
last_verified: "2026-05-24"
confidence: "high"
---

# Serialization with Serde

## When to Use
- Reading/writing JSON, TOML, YAML, or other data formats
- Parsing API responses into typed structs
- Configuration file handling
- Database column mapping

## Standard Pattern

```rust
use serde::{Deserialize, Serialize, Deserializer, Serializer};
use serde::de::{self, Visitor};
use std::fmt;

// Basic derive usage
#[derive(Debug, Serialize, Deserialize)]
struct Config {
    name: String,
    port: u16,
    #[serde(default)]
    debug: bool,
    #[serde(rename = "maxConnections")]
    max_connections: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    secret: Option<String>,
    #[serde(default = "default_host")]
    host: String,
}

fn default_host() -> String {
    "localhost".to_string()
}

// Enum with serde — externally tagged by default
#[derive(Debug, Serialize, Deserialize)]
#[serde(tag = "type", content = "data")] // adjacently tagged
enum Message {
    #[serde(rename = "chat")]
    Chat { text: String, from: String },
    #[serde(rename = "ping")]
    Ping,
    #[serde(rename = "error")]
    Error(String),
}

// Flatten for partial updates
#[derive(Debug, Serialize, Deserialize)]
struct UserUpdate {
    #[serde(flatten)]
    pub base: UserBase,
    #[serde(default)]
    pub metadata: std::collections::HashMap<String, String>,
}

#[derive(Debug, Serialize, Deserialize)]
struct UserBase {
    name: String,
    email: String,
}

// Custom deserialization for flexible input
#[derive(Debug, Serialize, Deserialize)]
struct FlexibleInt(
    #[serde(deserialize_with = "deserialize_flexible_int")]
    u64,
);

fn deserialize_flexible_int<'de, D>(deserializer: D) -> Result<u64, D::Error>
where
    D: Deserializer<'de>,
{
    let s = String::deserialize(deserializer)?;
    s.parse::<u64>().map_err(de::Error::custom)
}

// Skip fields during deserialization
#[derive(Debug, Serialize, Deserialize)]
struct ApiResponse {
    data: Vec<Item>,
    #[serde(skip)]
    _cached_at: Option<std::time::Instant>,
}

#[derive(Debug, Serialize, Deserialize)]
struct Item {
    id: u64,
    name: String,
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // JSON
    let json = r#"{"name":"server","port":8080,"maxConnections":100}"#;
    let config: Config = serde_json::from_str(json)?;
    println!("{:?}", config);

    let output = serde_json::to_string_pretty(&config)?;
    println!("{}", output);

    // TOML
    // let config: Config = toml::from_str(&toml_string)?;

    // YAML
    // let config: Config = serde_yaml::from_str(&yaml_string)?;

    // Message enum
    let msg_json = r#"{"type":"chat","data":{"text":"hello","from":"alice"}}"#;
    let msg: Message = serde_json::from_str(msg_json)?;
    println!("{:?}", msg);

    Ok(())
}
```

## Common Mistakes

```rust
// WRONG: Forgetting #[serde(default)] for optional fields in configs
#[derive(Deserialize)]
struct Config {
    name: String,
    debug: bool, // ERROR if missing from input
}

// CORRECT: Use Option or default
#[derive(Deserialize)]
struct Config {
    name: String,
    #[serde(default)]
    debug: bool, // defaults to false if missing
}

// WRONG: Using serde_json::from_str without error context
let config: Config = serde_json::from_str(&input)?; // cryptic error on failure

// CORRECT: Add context
let config: Config = serde_json::from_str(&input)
    .map_err(|e| format!("Failed to parse config at line {}: {}", e.line(), e))?;

// WRONG: Serializing sensitive fields
#[derive(Serialize)]
struct User {
    name: String,
    password: String, // Leaked to JSON output!
}

// CORRECT: Skip sensitive fields
#[derive(Serialize)]
struct User {
    name: String,
    #[serde(skip_serializing)]
    password: String,
}

// WRONG: Not handling unknown fields (breaks forward compatibility)
#[derive(Deserialize)]
struct Response {
    id: u64,
    name: String,
}

// CORRECT: Deny unknown fields only when schema is strict
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct StrictResponse {
    id: u64,
    name: String,
}
// Otherwise, unknown fields are silently ignored by default
```

## Gotchas
- `#[serde(flatten)]` uses a HashMap internally — can cause conflicts with other attributes
- `#[serde(tag = "type")]` puts the variant name as a field; `content = "data"` puts the payload in a nested object
- String fields accept `null` as `Option<String>` — no error, just None
- `serde_json::Value` is for untyped JSON — avoid in production code
- `#[serde(rename_all = "camelCase")]` converts all field names at once
- `#[serde(with = "module")]` uses a module's serialize/deserialize functions
- Deserializing into `HashMap<String, Value>` loses type safety — define proper structs
- Use `serde_json::from_reader` for large inputs to avoid copying

## Related
- rust/stdlib/result-option.md
- rust/web/axum-basics.md
- rust/stdlib/traits.md
