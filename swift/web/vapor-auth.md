---
id: "swift-web-vapor-auth"
title: "Authentication in Vapor: Session, Token, JWT"
language: "swift"
category: "web"
tags: ["swift", "vapor", "auth", "jwt", "session", "token"]
version: "4.x+"
retrieval_hint: "swift vapor authentication JWT token session middleware"
last_verified: "2026-05-24"
confidence: "high"
---

# Authentication in Vapor: Session, Token, JWT

## When to Use
- Adding authentication to Vapor applications
- Implementing JWT-based stateless auth
- Protecting routes with Authenticatable middleware
- Handling user sessions in Vapor

## Standard Pattern

```swift
import Vapor
import Fluent

// --- User Model with Authenticatable ---
final class User: Model, Content, Authenticatable {
    static let schema = "users"

    @ID(key: .id)
    var id: UUID?

    @Field(key: "name")
    var name: String

    @Field(key: "email")
    var email: String

    @Field(key: "password_hash")
    var passwordHash: String

    init() {}

    init(id: UUID? = nil, name: String, email: String, passwordHash: String) {
        self.id = id
        self.name = name
        self.email = email
        self.passwordHash = passwordHash
    }
}

// --- Session Authenticatable (for web apps) ---
extension User: ModelSessionAuthenticatable {}
// Adds createSessionID(sessionID:) and authenticate(sessionID:)

// --- Credentials Authenticatable (for login endpoint) ---
struct UserLogin: Content {
    let email: String
    let password: String
}

extension User: ModelCredentialsAuthenticatable {
    static let usernameKey = \User.$email
    static let passwordHashKey = \User.$passwordHash

    func verify(password: String) throws -> Bool {
        try Bcrypt.verify(password, created: self.passwordHash)
    }
}

// --- JWT Configuration ---
// Requires: JWT package — in Package.swift:
// .package(url: "https://github.com/vapor/jwt.git", from: "4.0.0")

struct UserJWTPayload: JWTPayload, Authenticatable {
    var subject: SubjectClaim
    var email: String
    var expiration: ExpirationClaim

    func verify(using signer: JWTSigner) throws {
        try expiration.verifyNotExpired()
    }
}

// --- Configure Auth ---
// In configure.swift:
func configureAuth(_ app: Application) {
    // Session auth
    app.middleware.use(app.sessions.middleware)
    app.middleware.use(User.sessionAuthenticator())

    // Credential auth (login endpoint)
    User.credentialsAuthenticator()

    // JWT
    app.jwt.signers.use(.hs256(key: "your-secret-key-here"))
}

// --- Auth Routes ---
struct AuthController: RouteCollection {
    func boot(routes: RoutesBuilder) throws {
        // Public routes
        routes.post("login", use: login)
        routes.post("register", use: register)

        // Protected — requires valid JWT
        let protected = routes.grouped(UserJWTPayload.authenticator())
        protected.get("profile", use: profile)
    }

    // POST /login
    @Sendable
    func login(req: Request) async throws -> TokenResponse {
        let login = try req.content.decode(UserLogin.self)

        guard let user = try await User.query(on: req.db)
            .filter(\.$email == login.email)
            .first()
        else {
            throw Abort(.unauthorized, reason: "Invalid credentials")
        }

        guard try user.verify(password: login.password) else {
            throw Abort(.unauthorized, reason: "Invalid credentials")
        }

        // Create JWT
        let payload = UserJWTPayload(
            subject: .init(value: user.id!.uuidString),
            email: user.email,
            expiration: .init(value: Date().addingTimeInterval(3600))  // 1 hour
        )
        let token = try await req.jwt.sign(payload)

        return TokenResponse(token: token, user: UserDTO(from: user))
    }

    // POST /register
    @Sendable
    func register(req: Request) async throws -> UserDTO {
        let create = try req.content.decode(CreateUserDTO.self)
        let user = User(
            name: create.name,
            email: create.email,
            passwordHash: try Bcrypt.hash(create.password)
        )
        try await user.save(on: req.db)
        return UserDTO(from: user)
    }

    // GET /profile (protected)
    @Sendable
    func profile(req: Request) async throws -> UserDTO {
        let payload = try req.auth.require(UserJWTPayload.self)
        guard let user = try await User.find(UUID(payload.subject.value), on: req.db) else {
            throw Abort(.notFound)
        }
        return UserDTO(from: user)
    }
}
```

## Common Mistakes

```swift
// WRONG: Not using Authenticatable middleware — manual token check in every handler
func profile(req: Request) async throws -> UserDTO {
    guard let authHeader = req.headers.first(name: "Authorization") else {
        throw Abort(.unauthorized)
    }
    // Manual parsing...
}

// CORRECT: Use Authenticatable middleware
let protected = routes.grouped(UserJWTPayload.authenticator())
protected.get("profile", use: profile)


// WRONG: Storing JWT secret in source code
app.jwt.signers.use(.hs256(key: "hardcoded-secret"))

// CORRECT: Use environment variable
app.jwt.signers.use(.hs256(key: Environment.get("JWT_SECRET") ?? "dev-secret"))


// WRONG: Not checking token expiry
struct MyPayload: JWTPayload {
    var subject: SubjectClaim
    // Missing ExpirationClaim!
    func verify(using signer: JWTSigner) throws {}  // No expiry check
}

// CORRECT: Always include and verify expiration
struct MyPayload: JWTPayload {
    var subject: SubjectClaim
    var expiration: ExpirationClaim  // Required

    func verify(using signer: JWTSigner) throws {
        try expiration.verifyNotExpired()
    }
}


// WRONG: Not configuring session middleware before session authenticator
app.middleware.use(User.sessionAuthenticator())
// Sessions won't work — session middleware not added first!

// CORRECT: Session middleware first, then authenticator
app.middleware.use(app.sessions.middleware)
app.middleware.use(User.sessionAuthenticator())
```

## Gotchas
- **JWT secret rotation**: When you change the JWT secret, all existing tokens become invalid. Plan for token refresh with a refresh token or grace period.
- **Token revocation**: JWTs are stateless — you cannot revoke individual tokens without a blocklist. For immediate revocation, use session-based auth or maintain a token blocklist in Redis.
- **Middleware order**: Session middleware must be registered before session authenticator middleware. Auth middleware must be applied to the route group, not globally, unless all routes need auth.
- **Bcrypt cost**: Vapor's Bcrypt defaults to cost 12. This is secure but slow (200-400ms per hash). Consider async hashing for registration endpoints.
- **Authenticatable conformance**: Make sure your model conforms to the correct Authenticatable protocol. `ModelSessionAuthenticatable` is for sessions, `ModelCredentialsAuthenticatable` is for login.
- **JWT signer type**: HMAC with `hs256` uses symmetric keys — anyone with the key can sign tokens. Use `es256` (ECDSA) for asymmetric signing in production.

## Related
- swift/web/vapor-basics.md
- swift/web/vapor-fluent.md
- swift/stdlib/json-codable.md
