---
id: "swift-stdlib-basics"
title: "Swift Basics: let, var, Optionals, and Type Inference"
language: "swift"
category: "stdlib"
tags: ["swift", "basics", "let", "var", "optionals", "guard", "switch", "type-inference"]
version: "5.9+"
retrieval_hint: "swift let var optionals guard let if let switch exhaustiveness string interpolation type inference"
last_verified: "2026-05-24"
confidence: "high"
---

# Swift Basics: let, var, Optionals, and Type Inference

## When to Use
- Writing any Swift code — these are the foundational concepts
- Understanding Swift's type safety and optionals system
- Migrating from Objective-C to Swift
- Small LLMs often generate Objective-C-style Swift — this entry clarifies modern Swift

## Standard Pattern

```swift
// let = immutable (constant), var = mutable (variable)
let name: String = "Swift"  // Immutable — cannot be changed
var counter = 0              // Mutable — can be changed
counter += 1                 // OK

// Type inference — compiler infers types
let version = 5.9            // Inferred as Double
let language = "Swift"       // Inferred as String
let items = [1, 2, 3]        // Inferred as [Int]

// Optionals — the core of Swift's type safety
var optionalName: String? = nil  // Can be nil
optionalName = "Alice"           // Or a value

// Unwrapping optionals safely
if let unwrapped = optionalName {
    print("Hello, \(unwrapped)")  // Only executes if optionalName is not nil
}

// guard let — early return if nil
func greet(_ name: String?) {
    guard let name = name else {
        print("No name provided")
        return
    }
    // name is non-nil String in the rest of the function
    print("Hello, \(name)!")
}

// Nil coalescing operator (??) — provide default value
let displayName = optionalName ?? "Anonymous"

// Optional chaining
struct Address { var city: String = "" }
struct User { var address: Address? }
let user: User? = User(address: Address(city: "Paris"))
let city = user?.address?.city  // Optional<String> — nil if any part is nil

// Switch — exhaustive and powerful
let statusCode = 200
switch statusCode {
case 200:
    print("OK")
case 201:
    print("Created")
case 400..<500:
    print("Client Error")
case 500..<600:
    print("Server Error")
default:
    print("Unknown")
}

// String interpolation
let score = 95
let message = "Your score is \(score) points"
let detail = "Double: \(score * 2)"  // Expressions work too

// Guard for preconditions
func process(age: Int?) {
    guard let age = age, age >= 0 else {
        print("Invalid age")
        return
    }
    print("Age: \(age)")
}

// Tuple
let httpStatus = (code: 200, message: "OK")
print(httpStatus.code)    // 200
print(httpStatus.message) // "OK"

// Type safety — no implicit conversions
let intValue = 42
// let doubleValue: Double = intValue  // Compile error!
let doubleValue = Double(intValue)    // Explicit conversion required
```

## Common Mistakes

```swift
// WRONG: Force unwrapping without checking (crashes if nil)
let name: String? = nil
let length = name!.count  // Runtime crash: Unexpectedly found nil

// CORRECT: Use optional binding or nil coalescing
if let name = name {
    let length = name.count
}
// Or:
let length = name?.count ?? 0

// WRONG: Using var when let should be used
var name = "Swift"  // name never changes — should be let

// CORRECT: Use let by default
let name = "Swift"

// WRONG: Not using guard for early returns (pyramid of doom)
func processUser(_ user: String?) {
    if let user = user {
        if !user.isEmpty {
            if user.count > 2 {
                print("Processing \(user)")
            }
        }
    }
}

// CORRECT: Use guard for clean early returns
func processUser(_ user: String?) {
    guard let user = user, !user.isEmpty, user.count > 2 else { return }
    print("Processing \(user)")
}

// WRONG: Using if let when guard let is more appropriate
func sendEmail(to address: String?) {
    if let address = address {
        // All code nested inside if block
        print("Sending to \(address)")
        // ... 50 more lines of nested code
    }
}

// CORRECT: Use guard let to keep the happy path at top level
func sendEmail(to address: String?) {
    guard let address = address else { return }
    // All code at top level — address is non-nil String
    print("Sending to \(address)")
}

// WRONG: Not handling all cases in switch (non-exhaustible)
enum Direction { case north, south, east, west }
let dir = Direction.north
switch dir {
case .north:
    print("Going north")
case .south:
    print("Going south")
    // Compiler error: switch must be exhaustive!
}

// CORRECT: Handle all cases or add default
switch dir {
case .north: print("Going north")
case .south: print("Going south")
case .east:  print("Going east")
case .west:  print("Going west")
}
```

## Gotchas
- `let` is the default. Use `var` only when the value truly needs to change.
- Optionals (`Type?`) are the most important Swift concept. A `String?` is NOT a `String` — you must unwrap it.
- `guard let` unwraps the optional for the REST of the scope. `if let` unwraps only within the `if` block.
- `guard` MUST transfer control (`return`, `throw`, `break`, `continue`, or `fatalError()`) in its `else` clause.
- Swift's `switch` is exhaustive for enums. The compiler will tell you if you missed a case.
- String interpolation: `"Value: \(expression)"`. Works with any type that conforms to `CustomStringConvertible`.
- Swift does NOT do implicit type conversions. `Double(42)` not `42 as Double`.
- `??` (nil coalescing) provides a default value when the optional is nil.
- `?.` (optional chaining) returns nil if any part of the chain is nil.

## Related
- swift/stdlib/optionals.md
- swift/stdlib/collections.md
- swift/stdlib/closures.md
- swift/stdlib/error-handling.md
