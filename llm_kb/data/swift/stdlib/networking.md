---
id: "swift-stdlib-networking"
title: "Networking with URLSession: Async HTTP Requests"
language: "swift"
category: "stdlib"
tags: ["swift", "networking", "urlsession", "http", "async", "download"]
version: "5.9+"
retrieval_hint: "swift URLSession networking async await HTTP requests download upload"
last_verified: "2026-05-24"
confidence: "high"
---

# Networking with URLSession: Async HTTP Requests

## When to Use
- Making HTTP requests from Swift apps
- Fetching JSON data from REST APIs
- Downloading files and tracking progress
- Uploading data with multipart support

## Standard Pattern

```swift
import Foundation

// --- API Client with async/await ---
final class APIClient {
    private let session: URLSession
    private let baseURL: URL
    private let decoder: JSONDecoder

    init(
        baseURL: URL,
        session: URLSession = .shared,
        decoder: JSONDecoder = JSONDecoder()
    ) {
        self.baseURL = baseURL
        self.session = session
        self.decoder = decoder
        self.decoder.keyDecodingStrategy = .convertFromSnakeCase
        self.decoder.dateDecodingStrategy = .iso8601
    }

    // --- Generic GET Request ---
    func get<T: Decodable>(
        _ path: String,
        queryItems: [URLQueryItem]? = nil
    ) async throws -> T {
        var components = URLComponents(url: baseURL.appendingPathComponent(path), resolvingAgainstBaseURL: true)!
        if let queryItems {
            components.queryItems = queryItems
        }

        guard let url = components.url else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Accept")

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        guard (200...299).contains(httpResponse.statusCode) else {
            throw APIError.httpError(statusCode: httpResponse.statusCode, data: data)
        }

        return try decoder.decode(T.self, from: data)
    }

    // --- Generic POST Request ---
    func post<T: Decodable, B: Encodable>(
        _ path: String,
        body: B
    ) async throws -> T {
        let url = baseURL.appendingPathComponent(path)
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        guard (200...299).contains(httpResponse.statusCode) else {
            throw APIError.httpError(statusCode: httpResponse.statusCode, data: data)
        }

        return try decoder.decode(T.self, from: data)
    }

    // --- File Download with Progress ---
    func download(url: URL) async throws -> URL {
        let (localURL, response) = try await session.download(from: url)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw APIError.downloadFailed
        }

        return localURL
    }

    // --- Bearer Token Auth ---
    func setAuthToken(_ token: String) {
        // Store for use in requests
        // In a full implementation, use URLProtocol or URLSessionDelegate
    }
}

// --- Error Handling ---
enum APIError: Error, LocalizedError {
    case invalidURL
    case invalidResponse
    case httpError(statusCode: Int, data: Data)
    case decodingFailed(Error)
    case downloadFailed
    case noConnection

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .invalidResponse:
            return "Invalid server response"
        case .httpError(let code, _):
            return "HTTP error: \(code)"
        case .decodingFailed(let error):
            return "Decoding error: \(error.localizedDescription)"
        case .downloadFailed:
            return "Download failed"
        case .noConnection:
            return "No internet connection"
        }
    }
}

// --- Models ---
struct UserResponse: Decodable {
    let id: Int
    let name: String
    let email: String
}

struct CreateUserRequest: Encodable {
    let name: String
    let email: String
}

// --- Usage ---
func exampleUsage() async {
    let client = APIClient(baseURL: URL(string: "https://api.example.com")!)

    do {
        // GET
        let users: [UserResponse] = try await client.get("/users")

        // POST
        let newUser = CreateUserRequest(name: "Alice", email: "alice@example.com")
        let created: UserResponse = try await client.post("/users", body: newUser)

        print("Created user: \(created.name)")
    } catch APIError.noConnection {
        print("Please check your internet connection")
    } catch APIError.httpError(let code, let data) {
        let body = String(data: data, encoding: .utf8) ?? ""
        print("Server error \(code): \(body)")
    } catch {
        print("Unexpected error: \(error)")
    }
}
```

## Common Mistakes

```swift
// WRONG: Creating a new URLSession per request (wastes resources)
func fetchUser(id: Int) async throws -> User {
    let session = URLSession(configuration: .default)  // New session every time!
    let (data, _) = try await session.data(from: url)
    session.invalidateAndCancel()
    return try JSONDecoder().decode(User.self, from: data)
}

// CORRECT: Reuse URLSession
let session = URLSession.shared  // Singleton, configurable

func fetchUser(id: Int) async throws -> User {
    let (data, _) = try await session.data(from: url)
    return try JSONDecoder().decode(User.self, from: data)
}


// WRONG: Not checking HTTP status code (data can be error HTML)
func getData() async throws -> Data {
    let (data, response) = try await session.data(from: url)
    // data may contain "404 Not Found" HTML page
    return data  // No status code check!
}

// CORRECT: Always validate HTTP response
func getData() async throws -> Data {
    let (data, response) = try await session.data(from: url)
    guard let httpResponse = response as? HTTPURLResponse,
          (200...299).contains(httpResponse.statusCode) else {
        throw APIError.invalidResponse
    }
    return data
}


// WRONG: Missing URL encoding for query parameters
let query = "swift programming"
let url = URL(string: "https://api.example.com/search?q=\(query)")!
// URL is invalid — space not encoded

// CORRECT: Use URLQueryItem
var components = URLComponents(string: "https://api.example.com/search")!
components.queryItems = [URLQueryItem(name: "q", value: "swift programming")]
let url = components.url!  // Properly encoded
```

## Gotchas
- **Background vs foreground sessions**: `URLSession.shared` is foreground-only. For background downloads that continue after the app is suspended, use `URLSessionConfiguration.background(withIdentifier:)`.
- **Main thread awareness**: `URLSession` async methods return on a background delegate queue by default. Use `@MainActor` or `Task { @MainActor in ... }` to update UI.
- **Certificate pinning**: Implement `URLSessionDelegate.urlSession(_:didReceive:completionHandler:)` for certificate pinning. The shared session does not support custom delegates.
- **HTTP/2 and multiplexing**: `URLSession` supports HTTP/2 natively. Multiple requests to the same host are multiplexed automatically — no special configuration needed.
- **Cache policy**: Default cache policy is `.useProtocolCachePolicy`. For fresh data, use `.reloadIgnoringLocalCacheData`. For offline support, implement a custom `URLCache`.
- **Cookie storage**: `URLSession` automatically handles cookies based on `HTTPCookieStorage.shared`. Disable with `httpShouldHandleCookies = false` in the configuration.
- **Timeout configuration**: Set `timeoutIntervalForRequest` (per-request) and `timeoutIntervalForResource` (entire upload/download) in `URLSessionConfiguration`.

## Related
- swift/stdlib/json-codable.md
- swift/stdlib/concurrency.md
