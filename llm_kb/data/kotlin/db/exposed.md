---
id: "kotlin-db-exposed"
title: "JetBrains Exposed ORM: Tables, Queries, and Transactions"
language: "kotlin"
category: "db"
tags: ["kotlin", "exposed", "orm", "database", "sql", "transactions"]
version: "1.9+"
retrieval_hint: "kotlin JetBrains Exposed ORM tables queries transactions joins SQL library"
last_verified: "2026-05-24"
confidence: "high"
---

# JetBrains Exposed ORM: Tables, Queries, and Transactions

## When to Use
- Working with SQL databases in Kotlin using a Kotlin-native ORM
- Building type-safe SQL queries with Exposed DSL
- Managing database schemas with Exposed DDL
- When you want a lightweight ORM without JPA/Hibernate overhead

## Standard Pattern

```kotlin
import org.jetbrains.exposed.sql.*
import org.jetbrains.exposed.sql.transactions.transaction
import org.jetbrains.exposed.sql.SchemaUtils.create
import org.jetbrains.exposed.sql.SchemaUtils.drop

// Define tables
object Users : Table("users") {
    val id = integer("id").autoIncrement()
    val name = varchar("name", 255)
    val email = varchar("email", 255).uniqueIndex()
    val age = integer("age").nullable()
    override val primaryKey = PrimaryKey(id)
}

object Orders : Table("orders") {
    val id = integer("id").autoIncrement()
    val userId = integer("user_id").references(Users.id)
    val product = varchar("product", 255)
    val amount = decimal("amount", 10, 2)
    val createdAt = datetime("created_at").defaultExpression(CurrentDateTime)
    override val primaryKey = PrimaryKey(id)
}

// Connect to database
fun connect() {
    Database.connect(
        url = "jdbc:postgresql://localhost:5432/mydb",
        driver = "org.postgresql.Driver",
        user = "user",
        password = "password"
    )
}

// Create tables
fun createSchema() {
    transaction {
        create(Users, Orders)
    }
}

// Insert data
fun createUser(name: String, email: String, age: Int? = null): Int {
    return transaction {
        Users.insertAndGetId {
            it[Users.name] = name
            it[Users.email] = email
            it[Users.age] = age
        }.value
    }
}

// Query data
fun findAllUsers(): List<UserRow> {
    return transaction {
        Users.selectAll().map { it.toUser() }
    }
}

fun findUserById(id: Int): UserRow? {
    return transaction {
        Users.select { Users.id eq id }
            .map { it.toUser() }
            .singleOrNull()
    }
}

fun findUsersByName(pattern: String): List<UserRow> {
    return transaction {
        Users.select { Users.name like "%$pattern%" }
            .map { it.toUser() }
    }
}

// Update data
fun updateUserEmail(id: Int, newEmail: String): Boolean {
    return transaction {
        Users.update({ Users.id eq id }) {
            it[email] = newEmail
        } > 0
    }
}

// Delete data
fun deleteUser(id: Int): Boolean {
    return transaction {
        Users.deleteWhere { Users.id eq id } > 0
    }
}

// Join query
fun getUserOrders(userId: Int): List<UserOrder> {
    return transaction {
        (Users innerJoin Orders)
            .slice(Users.name, Users.email, Orders.product, Orders.amount)
            .select { Users.id eq userId }
            .map {
                UserOrder(
                    userName = it[Users.name],
                    email = it[Users.email],
                    product = it[Orders.product],
                    amount = it[Orders.amount]
                )
            }
    }
}

// Aggregation
fun getUserOrderStats(): List<UserStats> {
    return transaction {
        (Users leftJoin Orders)
            .slice(Users.name, Orders.id.count(), Orders.amount.sum())
            .selectAll()
            .groupBy(Users.name)
            .map {
                UserStats(
                    name = it[Users.name],
                    orderCount = it[Orders.id.count()],
                    totalAmount = it[Orders.amount.sum()] ?: BigDecimal.ZERO
                )
            }
    }
}

// Extension function to map ResultRow to data class
fun ResultRow.toUser() = UserRow(
    id = this[Users.id],
    name = this[Users.name],
    email = this[Users.email],
    age = this[Users.age]
)

data class UserRow(val id: Int, val name: String, val email: String, val age: Int?)
data class UserOrder(val userName: String, val email: String, val product: String, val amount: BigDecimal)
data class UserStats(val name: String, val orderCount: Long, val totalAmount: BigDecimal)
```

## Common Mistakes

```kotlin
// WRONG: Not wrapping database operations in transaction
fun createUser(name: String): Int {
    return Users.insertAndGetId {  // Fails — must be inside a transaction!
        it[Users.name] = name
    }.value
}

// CORRECT: Always use transaction block
fun createUser(name: String): Int {
    return transaction {
        Users.insertAndGetId {
            it[Users.name] = name
        }.value
    }
}

// WRONG: Using string interpolation in queries (SQL injection risk)
fun searchUsers(name: String): List<UserRow> {
    return transaction {
        Users.select { Users.name like "%$name%" }  // Safe in Exposed (parameterized)
        // But raw SQL would be dangerous: "SELECT * FROM users WHERE name = '$name'"
    }.map { it.toUser() }
}

// CORRECT: Exposed DSL is safe — it uses parameterized queries
fun searchUsers(name: String): List<UserRow> {
    return transaction {
        Users.select { Users.name like "%$name%" }
            .map { it.toUser() }
    }
}

// WRONG: Not handling nullable columns properly
val age = row[Users.age]  // Returns Int? — could be null

// CORRECT: Handle nullable columns
val age: Int? = row[Users.age]
val ageOrDefault: Int = row[Users.age] ?: 0

// WRONG: N+1 query problem
fun getUsersWithOrders(): List<Pair<UserRow, List<UserOrder>>> {
    return transaction {
        Users.selectAll().map { userRow ->
            val user = userRow.toUser()
            val orders = Orders.select { Orders.userId eq user.id }
                .map { /* ... */ }
            user to orders  // One query per user — N+1!
        }
    }
}

// CORRECT: Use joins to fetch in one query
fun getUsersWithOrders(): List<Pair<UserRow, List<UserOrder>>> {
    return transaction {
        (Users leftJoin Orders)
            .selectAll()
            .groupBy { it[Users.id] }
            .map { (_, rows) ->
                val user = rows.first().toUser()
                val orders = rows.filter { it.getOrNull(Orders.id) != null }
                    .map { /* ... */ }
                user to orders
            }
    }
}
```

## Gotchas
- ALL database operations in Exposed MUST be inside a `transaction { }` block. This is the most common mistake.
- Exposed DSL uses `eq` for equality, `neq` for not-equal, `like` for pattern matching, `isNull`/`isNotNull` for null checks.
- `insertAndGetId` returns the auto-generated ID. `insert` returns the number of affected rows.
- `update { }.where { }` is written as `update({ condition }) { set }` in Exposed.
- `leftJoin` includes all rows from the left table even without matches. `innerJoin` only includes matching rows.
- `groupBy` + aggregation functions (`count()`, `sum()`, `avg()`) for reporting queries.
- Nullable columns in Exposed are defined with `.nullable()` and return nullable types.
- Exposed supports PostgreSQL, MySQL, SQLite, H2, Oracle, and SQL Server.
- Use `SchemaUtils.create()` and `SchemaUtils.drop()` for schema management.

## Related
- kotlin/stdlib/basics.md
- kotlin/stdlib/error-handling.md
- kotlin/web/ktor.md
- kotlin/web/spring-boot-kotlin.md
