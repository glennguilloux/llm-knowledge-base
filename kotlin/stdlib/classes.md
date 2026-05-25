---
id: "kotlin-stdlib-classes"
title: "Kotlin Classes: data, sealed, object, enum, and Delegation"
language: "kotlin"
category: "stdlib"
tags: ["kotlin", "data-class", "sealed-class", "object", "companion", "enum", "delegation"]
version: "1.9+"
retrieval_hint: "kotlin data class sealed class object singleton companion object enum class delegation"
last_verified: "2026-05-24"
confidence: "high"
---

# Kotlin Classes: data, sealed, object, enum, and Delegation

## When to Use
- Modeling data with classes in Kotlin
- Using data classes for DTOs, value objects, and configuration
- Using sealed classes for restricted hierarchies (state machines, result types)
- Creating singletons with `object` instead of Java's verbose singleton pattern
- Using delegation to compose behavior instead of inheritance

## Standard Pattern

```kotlin
// Data class — auto-generates equals, hashCode, toString, copy, componentN
data class User(
    val id: Int,
    val name: String,
    val email: String
)
val user = User(1, "Alice", "alice@example.com")
val copy = user.copy(name = "Bob")  // Copy with modification
val (id, name, email) = user        // Destructuring

// Sealed class — restricted hierarchy, all subclasses known at compile time
sealed class Result<out T> {
    data class Success<T>(val data: T) : Result<T>()
    data class Error(val message: String, val code: Int) : Result<Nothing>()
    object Loading : Result<Nothing>()
}

// Exhaustive when — compiler ensures all cases handled
fun handle(result: Result<String>): String = when (result) {
    is Result.Success -> result.data
    is Result.Error -> "Error ${result.code}: ${result.message}"
    Result.Loading -> "Loading..."
    // No else needed — compiler knows all cases
}

// Object — singleton (replaces Java's static singleton pattern)
object DatabaseConnection {
    private var connection: String? = null
    fun connect(url: String) {
        connection = url
        println("Connected to $url")
    }
    fun query(sql: String): List<String> = listOf("result1", "result2")
}

// Companion object — like Java static members
class MyClass {
    companion object {
        const val MAX_SIZE = 100
        fun create(): MyClass = MyClass()
    }
}

// Enum class
enum class Direction { NORTH, SOUTH, EAST, WEST }

enum class HttpStatus(val code: Int) {
    OK(200), NOT_FOUND(404), INTERNAL_ERROR(500);
    fun isError(): Boolean = code >= 400
}

// Class delegation — compose behavior without inheritance
interface Logger {
    fun log(message: String)
}

class ConsoleLogger : Logger {
    override fun log(message: String) = println("[LOG] $message")
}

// by keyword — delegates Logger implementation to ConsoleLogger
class Service(logger: Logger) : Logger by logger {
    fun execute() {
        log("Service executing")
    }
}
```

## Common Mistakes

```kotlin
// WRONG: Using regular class when data class is appropriate
class User(val id: Int, val name: String, val email: String)
val u1 = User(1, "Alice", "a@b.com")
val u2 = User(1, "Alice", "a@b.com")
// u1 == u2 is false! (reference equality)

// CORRECT: Use data class for value semantics
data class User(val id: Int, val name: String, val email: String)
val u1 = User(1, "Alice", "a@b.com")
val u2 = User(1, "Alice", "a@b.com")
// u1 == u2 is true (structural equality)

// WRONG: Using object when you need multiple instances
object Config {
    var timeout = 30  // Only one instance exists
}

// CORRECT: Use class if you need multiple instances
class Config(var timeout: Int = 30)

// WRONG: Not using companion object for factory methods
class User private constructor(val name: String) {
    // How to create instances?
}

// CORRECT: Use companion object for factory
class User private constructor(val name: String) {
    companion object {
        fun create(name: String): User? {
            return if (name.isNotBlank()) User(name) else null
        }
    }
}

// WRONG: Inheritance when delegation would be better
class ServiceWithInheritance : Logger, DatabaseConnection() { }

// CORRECT: Use delegation for composition
class Service(logger: Logger, db: DatabaseConnection) : Logger by logger {
    fun execute() { log("executing") }
}
```

## Gotchas
- `data class` automatically generates `equals()`, `hashCode()`, `toString()`, `copy()`, and `componentN()` functions. All properties must be in the primary constructor.
- `sealed class` restricts the hierarchy — all direct subclasses must be declared in the same compilation unit. The `when` expression becomes exhaustive (no `else` needed).
- `object` creates a thread-safe singleton. Initialization is lazy (on first access).
- `companion object` is NOT the same as Java `static` — it's a real singleton object. For true static members, use `@JvmStatic` annotation.
- `const val` can only be used in `companion object` or at top level. It's a compile-time constant (inlined at call sites).
- Class delegation (`by`) forwards calls to the delegate. You can override specific methods to customize behavior.
- `value class` (inline class) has zero runtime overhead for single-property wrappers. It's erased to the underlying type at runtime.
- `data class` cannot be `open`, `abstract`, `sealed`, or `inner`.

## Related
- kotlin/stdlib/basics.md
- kotlin/stdlib/functions-lambdas.md
- kotlin/stdlib/error-handling.md
- kotlin/stdlib/null-safety.md
