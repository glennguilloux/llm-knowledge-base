---
id: "swift-web-vapor-basics"
title: "Vapor Framework Basics: Routes, Controllers, Middleware"
language: "swift"
category: "web"
tags: ["swift", "vapor", "routes", "controllers", "middleware", "server"]
version: "4.x+"
retrieval_hint: "swift vapor routes controllers middleware async HTTP server"
last_verified: "2026-05-24"
confidence: "high"
---

# Vapor Framework Basics: Routes, Controllers, Middleware

## When to Use
- Building server-side Swift applications
- Creating REST APIs with Vapor
- Implementing middleware for request/response processing
- Structuring routes with controllers

## Standard Pattern

```swift
import Vapor

// --- Entry Point ---
// Sources/App/entrypoint.swift
@main
enum Entrypoint {
    static func main() async throws {
        let app = try await Application.make(.detect())
        defer { app.shutdown() }
        try await configure(app)
        try await app.execute()
    }
}

// --- Configuration ---
// Sources/App/configure.swift
func configure(_ app: Application) async throws {
    // Middleware (order matters!)
    app.middleware.use(CORSMiddleware())
    app.middleware.use(ErrorMiddleware.default(environment: app.environment))
    app.middleware.use(FileMiddleware(publicDirectory: app.directory.publicDirectory))

    // Register routes
    try app.register(collection: UserController())
    try app.register(collection: PostController())

    // Configure database
    app.databases.use(.sqlite(.file("db.sqlite")), as: .sqlite)
}

// --- Controller ---
// Sources/App/Controllers/UserController.swift
import Vapor

struct UserController: RouteCollection {
    func boot(routes: RoutesBuilder) throws {
        let users = routes.grouped("api", "users")
        users.get(use: index)
        users.post(use: create)
        users.group(":userID") { user in
            user.get(use: show)
            user.put(use: update)
            user.delete(use: delete)
        }
    }

    // GET /api/users
    @Sendable
    func index(req: Request) async throws -> [UserDTO] {
        let users = try await User.query(on: req.db).all()
        return users.map { $0.toDTO() }
    }

    // POST /api/users
    @Sendable
    func create(req: Request) async throws -> UserDTO {
        let createDTO = try req.content.decode(CreateUserDTO.self)
        let user = User(name: createDTO.name, email: createDTO.email)
        try await user.save(on: req.db)
        return user.toDTO()
    }

    // GET /api/users/:userID — uses route parameter
    @Sendable
    func show(req: Request) async throws -> UserDTO {
        guard let user = try await User.find(req.parameters.get("userID"), on: req.db) else {
            throw Abort(.notFound)
        }
        return user.toDTO()
    }

    // PUT /api/users/:userID
    @Sendable
    func update(req: Request) async throws -> UserDTO {
        guard let user = try await User.find(req.parameters.get("userID"), on: req.db) else {
            throw Abort(.notFound)
        }
        let updateDTO = try req.content.decode(UpdateUserDTO.self)
        user.name = updateDTO.name ?? user.name
        user.email = updateDTO.email ?? user.email
        try await user.save(on: req.db)
        return user.toDTO()
    }

    // DELETE /api/users/:userID
    @Sendable
    func delete(req: Request) async throws -> HTTPStatus {
        guard let user = try await User.find(req.parameters.get("userID"), on: req.db) else {
            throw Abort(.notFound)
        }
        try await user.delete(on: req.db)
        return .noContent
    }
}

// --- DTOs (Data Transfer Objects) ---
import Vapor

struct UserDTO: Content {
    let id: UUID?
    let name: String
    let email: String
}

struct CreateUserDTO: Content {
    let name: String
    let email: String
}

struct UpdateUserDTO: Content {
    let name: String?
    let email: String?
}

// --- Custom Middleware ---
struct TimingMiddleware: AsyncMiddleware {
    func respond(to request: Request, chainingTo next: any AsyncResponder) async throws -> Response {
        let start = Date()
        let response = try await next.respond(to: request)
        let duration = Date().timeIntervalSince(start)
        response.headers.replaceOrAdd(name: "X-Response-Time", value: "\(duration * 1000)ms")
        return response
    }
}

// Register: app.middleware.use(TimingMiddleware())
```

## Common Mistakes

```swift
// WRONG: Blocking the event loop with synchronous calls
func index(req: Request) -> [UserDTO] {
    let data = try! Data(contentsOf: url)  // Blocking!
    return try! JSONDecoder().decode([UserDTO].self, from: data)
}

// CORRECT: Use async/await throughout
func index(req: Request) async throws -> [UserDTO] {
    let (data, _) = try await URLSession.shared.data(from: url)
    return try JSONDecoder().decode([UserDTO].self, from: data)
}


// WRONG: Missing await on async database operations
func show(req: Request) async throws -> UserDTO {
    let user = User.find(req.parameters.get("userID"), on: req.db)
    // `user` is an EventLoopFuture, not a User!
    return user.toDTO()  // Compiler error or wrong type
}

// CORRECT: Await the result
func show(req: Request) async throws -> UserDTO {
    guard let user = try await User.find(req.parameters.get("userID"), on: req.db) else {
        throw Abort(.notFound)
    }
    return user.toDTO()
}


// WRONG: Wrong Content-Type in request decoding
func create(req: Request) async throws -> UserDTO {
    let user = try req.content.decode(CreateUserDTO.self)
    // Fails if Content-Type is not application/json
}

// CORRECT: Explicit content type configuration
func create(req: Request) async throws -> UserDTO {
    guard req.headers.contentType == .json else {
        throw Abort(.unsupportedMediaType)
    }
    let user = try req.content.decode(CreateUserDTO.self)
}
```

## Gotchas
- **Event loop blocking**: Vapor runs on SwiftNIO event loops. Never call synchronous blocking APIs (like `Data(contentsOf:)`) on the event loop. Use `req.client` or async APIs instead.
- **Middleware ordering**: Middleware runs in the order it's added. Error middleware must be added early to catch errors from subsequent middleware. CORS middleware should be early.
- **Route collision**: Route parameters (`:userID`) can collide with static path segments. Specific routes (`users/me`) must be registered before parameterized routes (`users/:userID`).
- **Content type**: `req.content.decode()` requires the `Content-Type` header. JSON clients must send `Content-Type: application/json`.
- **Controller registration**: Controllers conform to `RouteCollection` and must be registered with `try app.register(collection:)`. Forgetting this step silently does nothing.
- **Application lifecycle**: Always `app.shutdown()` in a defer block. Use `try await Application.make(.detect())` for production.

## Related
- swift/web/vapor-auth.md
- swift/web/vapor-fluent.md
