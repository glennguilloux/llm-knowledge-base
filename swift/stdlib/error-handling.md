---
id: "swift-stdlib-error-handling"
title: "Swift Error Handling: throws, try, catch, Result, and async throws"
language: "swift"
category: "stdlib"
tags: ["swift", "error-handling", "throws", "try", "catch", "Result", "async-throws"]
version: "5.9+"
retrieval_hint: "swift throws try catch Result type custom Error enum rethrows async throws error propagation"
last_verified: "2026-05-24"
confidence: "high"
---

# Swift Error Handling: throws, try, catch, Result, and async throws

## When to Use
- Handling errors in Swift with the `throws`/`try`/`catch` pattern
- Using `Result` type for async error handling
- Defining custom error types with enums
- Propagating errors with `rethrows`
- Handling errors in async/await code

## Standard Pattern

```swift
// Define custom error enum
enum NetworkError: Error {
    case invalidURL
    case noData
    case decodingFailed(Error)
    case serverError(statusCode: Int, message: String)
    case unauthorized
}

// Throwing function
func fetchUser(id: Int) throws -> User {
    guard id > 0 else {
        throw NetworkError.invalidURL
    }
    
    let data = try performRequest("/users/\(id)")
    
    do {
        return try JSONDecoder().decode(User.self, from: data)
    } catch {
        throw NetworkError.decodingFailed(error)
    }
}

// Using try/catch
do {
    let user = try fetchUser(id: 1)
    print("User: \(user.name)")
} catch NetworkError.invalidURL {
    print("Invalid URL")
} catch NetworkError.decodingFailed(let underlyingError) {
    print("Decode error: \(underlyingError)")
} catch NetworkError.serverError(let code, let message) {
    print("Server error \(code): \(message)")
} catch {
    print("Unknown error: \(error)")
}

// try? — converts to optional (discards error)
let user = try? fetchUser(id: 1)  // User? — nil if error

// try! — force try (crashes if error)
let user = try! fetchUser(id: 1)  // User — crashes if error

// Result type — for storing success/failure
enum Result<Success, Failure: Error> {
    case success(Success)
    case failure(Failure)
}

func fetchUserResult(id: Int) -> Result<User, NetworkError> {
    do {
        let user = try fetchUser(id: id)
        return .success(user)
    } catch let error as NetworkError {
        return .failure(error)
    } catch {
        return .failure(.serverError(statusCode: 0, message: error.localizedDescription))
    }
}

// Using Result
switch fetchUserResult(id: 1) {
case .success(let user):
    print("User: \(user.name)")
case .failure(let error):
    print("Error: \(error)")
}

// Result with map and flatMap
let name = fetchUserResult(id: 1)
    .map { $0.name }
    .map { $0.uppercased() }

// rethrows — only throws if the closure parameter throws
func processItems<T>(_ items: [T], using processor: (T) throws -> Void) rethrows {
    for item in items {
        try processor(item)
    }
}

// If called with non-throwing closure, no need for try
processItems([1, 2, 3]) { print($0) }  // No try needed

// If called with throwing closure, try is required
try processItems([1, 2, 3]) { item in
    if item == 2 { throw NetworkError.noData }
}

// Async throws (Swift 5.5+)
func fetchUserAsync(id: Int) async throws -> User {
    let (data, response) = try await URLSession.shared.data(from: url)
    
    guard let httpResponse = response as? HTTPURLResponse else {
        throw NetworkError.noData
    }
    
    guard httpResponse.statusCode == 200 else {
        throw NetworkError.serverError(
            statusCode: httpResponse.statusCode,
            message: "Request failed"
        )
    }
    
    return try JSONDecoder().decode(User.self, from: data)
}

// Using async throws
Task {
    do {
        let user = try await fetchUserAsync(id: 1)
        print("User: \(user.name)")
    } catch {
        print("Error: \(error)")
    }
}

// Custom Error with context
struct AppError: Error {
    let code: Int
    let message: String
    let underlying: Error?
    
    init(code: Int, message: String, underlying: Error? = nil) {
        self.code = code
        self.message = message
        self.underlying = underlying
    }
}

// Error propagation
func processData() throws {
    let data = try loadData()      // Propagates error
    let parsed = try parse(data)   // Propagates error
    try save(parsed)               // Propagates error
}
```

## Common Mistakes

```swift
// WRONG: Using try! in production code
let user = try! fetchUser(id: 1)  // Crashes if error!

// CORRECT: Handle errors properly
do {
    let user = try fetchUser(id: 1)
    // Use user
} catch {
    // Handle error
}

// WRONG: Catching all errors without specificity
do {
    let user = try fetchUser(id: 1)
} catch {
    print("Error: \(error)")  // Too broad — no specific handling
}

// CORRECT: Catch specific error types
do {
    let user = try fetchUser(id: 1)
} catch NetworkError.invalidURL {
    // Handle invalid URL
} catch NetworkError.serverError(let code, _) where code == 401 {
    // Handle unauthorized
} catch {
    // Handle other errors
}

// WRONG: Not using Result for async callbacks
func fetchUser(completion: @escaping (User?, Error?) -> Void) {
    // Caller must check both user and error — easy to forget!
}

// CORRECT: Use Result for type-safe async callbacks
func fetchUser(completion: @escaping (Result<User, NetworkError>) -> Void) {
    // Caller must handle both cases — compiler enforces it
}

// WRONG: Not propagating errors
func processData() {
    let data = try? loadData()  // Error silently discarded!
    // data is nil if error occurred — but we don't know why
}

// CORRECT: Propagate errors with throws
func processData() throws {
    let data = try loadData()  // Error propagated
}

// WRONG: Using Error as a type directly
func handle(error: Error) { }  // Too generic

// CORRECT: Use specific error enum
func handle(error: NetworkError) { }  // Type-safe
```

## Gotchas
- Swift error handling is NOT exception handling. `throws` is part of the function signature and is checked at compile time.
- `try?` converts a throwing expression to an optional. Errors become `nil`.
- `try!` crashes on error. Only use when you're certain the call won't fail (e.g., loading a bundled file).
- `Result<Success, Failure>` is useful for storing success/failure for later handling.
- `rethrows` means the function only throws if its closure parameter throws.
- `async throws` combines error handling with async/await. Use `try await` to call.
- Custom errors should conform to `Error` protocol. Enums are the most common pattern.
- Pattern matching in `catch` blocks: `catch let error as SpecificError`, `catch where condition`.
- `Error.localizedDescription` provides a human-readable error message.
- Error propagation: if a function calls a `throws` function without `try`, it must also be marked `throws`.

## Related
- swift/stdlib/basics.md
- swift/stdlib/optionals.md
- swift/stdlib/closures.md
- swift/stdlib/concurrency.md
