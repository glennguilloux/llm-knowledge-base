---
id: "swift-web-vapor-fluent"
title: "Fluent ORM with Vapor: Models, Migrations, Queries"
language: "swift"
category: "web"
tags: ["swift", "vapor", "fluent", "orm", "database", "migrations"]
version: "4.x+"
retrieval_hint: "swift vapor Fluent ORM models migrations queries relationships"
last_verified: "2026-05-24"
confidence: "high"
---

# Fluent ORM with Vapor: Models, Migrations, Queries

## When to Use
- Database operations in Vapor applications
- Defining models and relationships with Fluent ORM
- Managing schema changes with migrations
- Building type-safe database queries

## Standard Pattern

```swift
import Vapor
import Fluent

// --- Model Definition ---
final class User: Model, Content {
    static let schema = "users"

    @ID(key: .id)
    var id: UUID?

    @Field(key: "name")
    var name: String

    @Field(key: "email")
    var email: String

    @Field(key: "age")
    var age: Int?

    @Timestamp(key: "created_at", on: .create)
    var createdAt: Date?

    @Timestamp(key: "updated_at", on: .update)
    var updatedAt: Date?

    // Relationships
    @Children(for: \.$user)
    var posts: [Post]

    init() { }

    init(id: UUID? = nil, name: String, email: String, age: Int? = nil) {
        self.id = id
        self.name = name
        self.email = email
        self.age = age
    }
}

// --- Related Model ---
final class Post: Model, Content {
    static let schema = "posts"

    @ID(key: .id)
    var id: UUID?

    @Field(key: "title")
    var title: String

    @Field(key: "content")
    var content: String

    @Parent(key: "user_id")
    var user: User

    init() { }
}

// --- Migration ---
struct CreateUser: AsyncMigration {
    func prepare(on database: Database) async throws {
        try await database.schema("users")
            .id()
            .field("name", .string, .required)
            .field("email", .string, .required)
            .field("age", .int)
            .field("created_at", .datetime)
            .field("updated_at", .datetime)
            .unique(on: "email")
            .create()
    }

    func revert(on database: Database) async throws {
        try await database.schema("users").delete()
    }
}

struct CreatePost: AsyncMigration {
    func prepare(on database: Database) async throws {
        try await database.schema("posts")
            .id()
            .field("title", .string, .required)
            .field("content", .string, .required)
            .field("user_id", .uuid, .required, .references("users", "id", onDelete: .cascade))
            .create()
    }

    func revert(on database: Database) async throws {
        try await database.schema("posts").delete()
    }
}

// --- Register Migrations ---
// In configure.swift:
// app.migrations.add(CreateUser())
// app.migrations.add(CreatePost())
// try await app.autoMigrate()

// --- Query Patterns ---
struct UserRepository {
    let db: Database

    // Find by ID
    func find(id: UUID) async throws -> User? {
        try await User.find(id, on: db)
    }

    // Filter with multiple conditions
    func search(name: String?, minAge: Int?) async throws -> [User] {
        var query = User.query(on: db)
        if let name {
            query = query.filter(\.$name ~~ name)  // Contains (case-insensitive on some DBs)
        }
        if let minAge {
            query = query.filter(\.$age >= minAge)
        }
        return try await query.all()
    }

    // Eager loading (avoid N+1)
    func usersWithPosts() async throws -> [User] {
        try await User.query(on: db)
            .with(\.$posts)
            .all()
    }

    // Pagination
    func paginated(page: Int, perPage: Int = 20) async throws -> Page<User> {
        try await User.query(on: db)
            .sort(\.$createdAt, .descending)
            .paginate(PageRequest(page: page, per: perPage))
    }

    // Aggregation
    func count() async throws -> Int {
        try await User.query(on: db).count()
    }

    // Raw SQL (when Fluent isn't enough)
    func rawQuery() async throws -> [User] {
        try await db.raw("SELECT * FROM users WHERE age > $1")
            .bind(18)
            .all(decoding: User.self)
    }
}
```

## Common Mistakes

```swift
// WRONG: N+1 query — loading relationships in a loop
let users = try await User.query(on: req.db).all()
for user in users {
    let posts = try await user.$posts.query(on: req.db).all()  // N queries!
}

// CORRECT: Eager load with .with()
let users = try await User.query(on: req.db)
    .with(\.$posts)
    .all()
for user in users {
    print(user.posts.count)  // Already loaded
}


// WRONG: Wrong field key name (mismatch between migration and model)
// Migration:
.field("full_name", .string, .required)
// Model:
@Field(key: "name")  // Wrong key!
var name: String

// CORRECT: Match exactly
.field("name", .string, .required)
@Field(key: "name")
var name: String


// WRONG: Forgetting to run migrations
// Model defined but table doesn't exist — runtime crash
func index(req: Request) async throws -> [User] {
    try await User.query(on: req.db).all()  // Fatal error: table not found
}

// CORRECT: Auto-migrate on startup
// In configure.swift:
try await app.autoMigrate()
```

## Gotchas
- **Migration idempotency**: Migrations should be idempotent — running them multiple times should be safe. `create()` fails if the table already exists. Use `.ignoreExisting()` or check with `databaseExists()`.
- **Foreign key constraints**: When using `.references()`, the referenced model must exist and be migrated first. Migration order matters.
- **Model vs DTO**: Never expose your Fluent `Model` directly to API responses if it contains sensitive fields (like password hashes). Create separate DTO structs.
- **Field key naming**: Fluent uses the `@Field(key:)` string — changing it breaks existing data unless you write a migration. Use `snake_case` for database columns.
- **`@Timestamp` quirks**: `.on(.create)` sets the field only on first save. `.on(.update)` updates on every save. `.on(.none)` never auto-sets.
- **Database provider**: SQLite in development vs PostgreSQL in production can have subtle differences (case sensitivity, type casting). Test with both.
- **Page return type**: Fluent's `paginate()` returns a `Page` struct with `items`, `metadata.page`, `metadata.per`, and `metadata.total`. It always runs a count query.

## Related
- swift/web/vapor-basics.md
- swift/web/vapor-auth.md
