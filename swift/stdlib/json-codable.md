---
id: "swift-stdlib-json-codable"
title: "JSON with Codable: Encoding, Decoding, and Custom Keys"
language: "swift"
category: "stdlib"
tags: ["swift", "codable", "json", "encoding", "decoding", "serialization"]
version: "5.9+"
retrieval_hint: "swift JSON Codable encoding decoding JSONEncoder JSONDecoder custom keys"
last_verified: "2026-05-24"
confidence: "high"
---

# JSON with Codable: Encoding, Decoding, and Custom Keys

## When to Use
- Serializing Swift structs/classes to JSON
- Parsing JSON from APIs into Swift models
- Customizing JSON key mapping (snake_case, custom keys)
- Handling date formats and special values

## Standard Pattern

```swift
import Foundation

// --- Basic Codable Model ---
struct User: Codable {
    let id: Int
    let name: String
    let email: String
}

// Encode to JSON
let user = User(id: 1, name: "Alice", email: "alice@example.com")
let encoder = JSONEncoder()
encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
let jsonData = try encoder.encode(user)
let jsonString = String(data: jsonData, encoding: .utf8)!
// {"email":"alice@example.com","id":1,"name":"Alice"}

// Decode from JSON
let json = """
{"id": 1, "name": "Alice", "email": "alice@example.com"}
""".data(using: .utf8)!
let decoder = JSONDecoder()
let decoded = try decoder.decode(User.self, from: json)

// --- Custom Coding Keys (snake_case API) ---
struct APIUser: Codable {
    let id: Int
    let displayName: String
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id
        case displayName = "display_name"
        case createdAt = "created_at"
    }
}

// --- Snake Case Auto-Conversion (JSONEncoder + JSONDecoder) ---
let snakeDecoder = JSONDecoder()
snakeDecoder.keyDecodingStrategy = .convertFromSnakeCase

let snakeEncoder = JSONEncoder()
snakeEncoder.keyEncodingStrategy = .convertToSnakeCase

// This auto-converts: "display_name" → displayName, "created_at" → createdAt
// Works for simple cases; use CodingKeys for complex mappings

// --- Date Handling ---
let dateDecoder = JSONDecoder()
dateDecoder.dateDecodingStrategy = .iso8601

// Custom date format
let formatter = DateFormatter()
formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ssZ"
formatter.locale = Locale(identifier: "en_US_POSIX")
dateDecoder.dateDecodingStrategy = .formatted(formatter)

// Custom date decoding (e.g., Unix timestamps)
dateDecoder.dateDecodingStrategy = .custom { decoder in
    let container = try decoder.singleValueContainer()
    let timestamp = try container.decode(TimeInterval.self)
    return Date(timeIntervalSince1970: timestamp)
}

// --- Optional and Default Values ---
struct Product: Codable {
    let id: Int
    let name: String
    let price: Double
    let description: String?  // Optional — missing key becomes nil
    let currency: String      // Must exist or decoding fails
}

// --- Nested JSON ---
struct Order: Codable {
    let id: Int
    let customer: Customer
    let items: [OrderItem]
}

struct Customer: Codable {
    let name: String
    let email: String
}

struct OrderItem: Codable {
    let productId: Int
    let quantity: Int
    let price: Double
}

// JSON:
// {
//   "id": 1001,
//   "customer": {"name": "Alice", "email": "alice@example.com"},
//   "items": [{"product_id": 42, "quantity": 2, "price": 19.99}]
// }
```

## Common Mistakes

```swift
// WRONG: Assuming all properties are required when some could be missing
struct Config: Codable {
    let host: String
    let port: Int
    let timeout: Int   // Fails if "timeout" key is missing from JSON
}

// CORRECT: Use optional for potentially missing values
struct Config: Codable {
    let host: String
    let port: Int
    let timeout: Int?  // nil if key is missing
}

// Or use default values with custom init:
struct Config: Codable {
    let host: String
    let port: Int
    let timeout: Int

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        host = try container.decode(String.self, forKey: .host)
        port = try container.decode(Int.self, forKey: .port)
        timeout = try container.decodeIfPresent(Int.self, forKey: .timeout) ?? 30
    }
}


// WRONG: Forgetting CodingKeys for renamed properties
// JSON has "display_name" but Swift uses "displayName"
struct User: Codable {
    let displayName: String  // Fails — no "displayName" key in JSON
}

// CORRECT: Map with CodingKeys
struct User: Codable {
    let displayName: String
    enum CodingKeys: String, CodingKey {
        case displayName = "display_name"
    }
}


// WRONG: Wrong date format strategy — dates fail silently
let json = """
{"name": "event", "date": "2024-01-15T10:30:00Z"}
""".data(using: .utf8)!

let decoder = JSONDecoder()
// Default date strategy expects TimeInterval since 2001
let event = try decoder.decode(Event.self, from: json)  // Fails!

// CORRECT: Match the date format
decoder.dateDecodingStrategy = .iso8601


// WRONG: Encoding floats with unnecessary precision
struct Price: Codable {
    let amount: Double
}
let price = Price(amount: 19.99)
let data = try JSONEncoder().encode(price)
String(data: data, encoding: .utf8)!  // "19.990000000000002"

// CORRECT: Use Decimal for currency
struct Price: Codable {
    let amount: Decimal  // "19.99"
}
```

## Gotchas
- **Key decoding strategy scope**: `keyDecodingStrategy = .convertFromSnakeCase` applies globally. Individual properties that don't follow snake_case need explicit `CodingKeys`.
- **Fractional seconds**: ISO8601 dates with fractional seconds (e.g., `2024-01-15T10:30:00.123Z`) require iOS 12+ / macOS 10.14+ for `.iso8601` with `includingFractionalSeconds`. Older OS versions will fail.
- **CodingKeys are exhaustive**: If you provide a `CodingKeys` enum, you must list ALL properties, not just the custom ones. Missing keys will cause compiler errors.
- **Encoding order**: JSONEncoder encodes properties in the order they appear in the struct definition, matching `CodingKeys` order. This is not guaranteed by the JSON spec but is consistent in practice.
- **Floating point precision**: `Double` and `Float` can introduce precision errors. Use `Decimal` for currency or other precision-sensitive values.
- **Property wrappers and Codable**: `@Published`, `@State`, and custom property wrappers can interfere with Codable synthesis. You may need custom encode/decode implementations for wrapped properties.
- **JSONEncoder vs PropertyListEncoder**: Both conform to the same pattern. `PropertyListEncoder` uses XML format by default. Use `JSONEncoder` for API communication.

## Related
- swift/stdlib/file-io.md
- swift/stdlib/networking.md
