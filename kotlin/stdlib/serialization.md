---
id: "kotlin-stdlib-serialization"
title: "Kotlin Serialization: kotlinx.serialization with JSON"
language: "kotlin"
category: "stdlib"
tags: ["kotlin", "serialization", "json", "kotlinx-serialization", "polymorphic"]
version: "1.9+"
retrieval_hint: "kotlin kotlinx.serialization Serializable JSON encoding decoding custom serializers polymorphic"
last_verified: "2026-05-24"
confidence: "high"
---

# Kotlin Serialization: kotlinx.serialization with JSON

## When to Use
- Serializing Kotlin objects to/from JSON
- Working with REST APIs in Ktor or Spring Boot
- Type-safe serialization without reflection (compile-time code generation)
- Polymorphic serialization for sealed class hierarchies
- Replacing Gson/M Jackson with a Kotlin-native solution

## Standard Pattern

```kotlin
import kotlinx.serialization.*
import kotlinx.serialization.json.*
import kotlinx.serialization.encoding.*
import kotlinx.serialization.descriptors.*

// Basic serialization
@Serializable
data class User(
    val id: Int,
    val name: String,
    val email: String,
    val age: Int? = null  // Nullable field — omitted from JSON if null by default
)

// Encoding to JSON
fun main() {
    val json = Json {
        prettyPrint = true
        ignoreUnknownKeys = true  // Don't fail on unknown JSON keys
        encodeDefaults = true     // Include default values in output
        isLenient = true          // Allow unquoted keys, etc.
    }

    val user = User(1, "Alice", "alice@example.com", 30)
    val jsonString = json.encodeToString(user)
    // {"id":1,"name":"Alice","email":"alice@example.com","age":30}

    val decoded = json.decodeFromString<User>(jsonString)
    println(decoded.name)  // "Alice"
}

// Nested objects
@Serializable
data class Address(
    val street: String,
    val city: String,
    val country: String
)

@Serializable
data class UserWithAddress(
    val id: Int,
    val name: String,
    val address: Address,
    val tags: List<String> = emptyList()
)

// List serialization
fun serializeUsers(users: List<User>): String {
    return Json.encodeToString(users)
}

fun deserializeUsers(json: String): List<User> {
    return Json.decodeFromString<List<User>>(json)
}

// Custom field names with @SerialName
@Serializable
data class ApiResponse(
    @SerialName("user_id") val userId: Int,
    @SerialName("full_name") val fullName: String,
    @SerialName("created_at") val createdAt: String
)

// Custom serializer
@Serializable(with = ColorSerializer::class)
data class Color(val r: Int, val g: Int, val b: Int)

object ColorSerializer : KSerializer<Color> {
    override val descriptor: SerialDescriptor =
        PrimitiveDescriptor("Color", PrimitiveKind.STRING)

    override fun serialize(encoder: Encoder, value: Color) {
        encoder.encodeString("#${value.r.toString(16)}${value.g.toString(16)}${value.b.toString(16)}")
    }

    override fun deserialize(decoder: Decoder): Color {
        val hex = decoder.decodeString().removePrefix("#")
        return Color(
            r = hex.substring(0, 2).toInt(16),
            g = hex.substring(2, 4).toInt(16),
            b = hex.substring(4, 6).toInt(16)
        )
    }
}

// Polymorphic serialization with sealed classes
@Serializable
sealed class Shape {
    @Serializable
    @SerialName("circle")
    data class Circle(val radius: Double) : Shape()

    @Serializable
    @SerialName("rectangle")
    data class Rectangle(val width: Double, val height: Double) : Shape()
}
```

## Common Mistakes

```kotlin
// WRONG: Forgetting @Serializable annotation
data class User(val id: Int, val name: String)  // Not serializable!
// val json = Json.encodeToString(user)  // Compile error

// CORRECT: Add @Serializable
@Serializable
data class User(val id: Int, val name: String)

// WRONG: Using Java classes without @Serializable
// data class User(val id: Int, val created: java.time.LocalDateTime)  // No serializer!

// CORRECT: Provide custom serializer or use a serializable type
@Serializable
data class User(
    val id: Int,
    @Serializable(with = InstantSerializer::class)
    val created: java.time.Instant
)

// WRONG: Not handling unknown keys from API responses
val jsonStr = """{"id":1,"name":"Alice","extra_field":"value"}"""
// val user = Json.decodeFromString<User>(jsonStr)  // Fails on extra_field

// CORRECT: Configure Json to ignore unknown keys
val json = Json { ignoreUnknownKeys = true }
val user = json.decodeFromString<User>(jsonStr)  // OK

// WRONG: Not encoding defaults — missing fields in output
@Serializable
data class Config(val host: String = "localhost", val port: Int = 8080)
// Json.encodeToString(Config())  // {} — defaults not included!

// CORRECT: Enable encodeDefaults
val json = Json { encodeDefaults = true }
Json.encodeToString(Config())  // {"host":"localhost","port":8080}

// WRONG: Trying to serialize a non-sealed class polymorphically
// open class Animal(val name: String)  // Polymorphic requires sealed class

// CORRECT: Use sealed class for polymorphic serialization
@Serializable
sealed class Animal {
    abstract val name: String
}
```

## Gotchas
- `@Serializable` annotation is required on every class you want to serialize. The compiler plugin generates the serializer at compile time.
- `ignoreUnknownKeys = true` is essential for API responses — APIs often add new fields without notice.
- `encodeDefaults = false` by default — fields with default values are omitted from JSON output. Set to `true` if you need them.
- `kotlinx.serialization` works at compile time (no reflection). This means it's fast and works with Kotlin/Native and Kotlin/JS.
- For polymorphic serialization, the base type must be `sealed`. The `@SerialName` annotation on subclasses determines the type discriminator.
- Custom serializers implement `KSerializer<T>` with `serialize()` and `deserialize()` methods.
- `@Transient` annotation excludes a field from serialization (like `transient` in Java).
- `Json {}` configuration is immutable — create one instance and reuse it.
- Nullable fields with `null` value are omitted by default. Use `encodeDefaults = true` to include them.

## Related
- kotlin/stdlib/classes.md
- kotlin/stdlib/basics.md
- kotlin/web/ktor.md
- kotlin/web/spring-boot-kotlin.md
