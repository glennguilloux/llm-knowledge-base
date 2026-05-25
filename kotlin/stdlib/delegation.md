---
id: "kotlin-stdlib-delegation"
title: "Kotlin Delegation: by lazy, Delegated Properties, Class Delegation"
language: "kotlin"
category: "stdlib"
tags: ["kotlin", "delegation", "delegated-properties", "lazy", "observable"]
version: "1.9+"
retrieval_hint: "kotlin delegation by lazy delegated properties observable vetoable class delegation"
last_verified: "2026-05-24"
confidence: "high"
---

# Kotlin Delegation: by lazy, Delegated Properties, Class Delegation

## When to Use
- Implementing lazy initialization with `by lazy`
- Observing property changes with `Delegates.observable`
- Validating property changes with `Delegates.vetoable`
- Implementing class composition via delegation (`by`)

## Standard Pattern

```kotlin
import kotlin.properties.Delegates
import kotlin.reflect.KProperty

// --- by lazy — Lazy Initialization ---
class HeavyDatabaseConnection {
    val config: DatabaseConfig by lazy {
        println("Loading database config...")  // Called once
        loadConfig()
    }

    val connection: Connection by lazy {
        println("Creating connection...")  // Only when first accessed
        DriverManager.getConnection(config.url)
    }
}

// --- Delegates.observable — Observe Property Changes ---
class UserViewModel {
    var name: String by Delegates.observable("") { _, old, new ->
        println("Name changed: $old → $new")
    }

    var isDirty: Boolean by Delegates.observable(false) { _, _, new ->
        if (new) {
            println("Form has unsaved changes")
        }
    }
}

// --- Delegates.vetoable — Validate Before Change ---
class PositiveNumber {
    var value: Int by Delegates.vetoable(0) { _, _, new ->
        if (new < 0) {
            println("Cannot set negative value: $new")
            false  // Reject the change
        } else {
            true   // Accept the change
        }
    }
}

// Usage:
// val num = PositiveNumber()
// num.value = 5   // OK
// num.value = -3  // Rejected, stays 5

// --- Custom Delegate ---
class StringDelegate(private var default: String = "") {
    private var formattedValue: String = default

    operator fun getValue(thisRef: Any?, property: KProperty<*>): String {
        return formattedValue
    }

    operator fun setValue(thisRef: Any?, property: KProperty<*>, value: String) {
        formattedValue = value.trim().replace(Regex("\\s+"), " ")
    }
}

class FormattedText {
    var text: String by StringDelegate()
}

// Usage:
// val ft = FormattedText()
// ft.text = "  Hello    World  "
// println(ft.text)  // "Hello World"

// --- Class Delegation (Composition) ---
interface Repository {
    fun getById(id: Int): String
    fun save(item: String): Boolean
}

class SqlRepository : Repository {
    override fun getById(id: Int): String = "SQL item $id"
    override fun save(item: String): Boolean {
        println("Saving $item to SQL")
        return true
    }
}

// CachingRepository wraps Repository by delegating all methods
class CachingRepository(
    private val inner: Repository
) : Repository by inner {  // Delegate all interface methods
    private val cache = mutableMapOf<Int, String>()

    override fun getById(id: Int): String {
        return cache.getOrPut(id) {
            inner.getById(id).also { println("Cache miss for $id") }
        }
    }
    // save() is not overridden — delegates to inner.save()
}

// Usage:
// val repo = CachingRepository(SqlRepository())
// repo.getById(1)  // Cache miss, fetches from SQL
// repo.getById(1)  // Cache hit

// --- Map Delegation ---
class AppConfig(map: Map<String, Any>) {
    val host: String by map
    val port: Int by map
    val debug: Boolean by map
}

// Usage:
// val config = AppConfig(mapOf(
//     "host" to "localhost",
//     "port" to 8080,
//     "debug" to true
// ))
// println(config.host)  // "localhost"

// --- Delegates.notNull (lateinit for primitives) ---
class Settings {
    var timeout: Long by Delegates.notNull()
    // Like lateinit but for primitives/non-nullable types

    fun init() {
        timeout = 5000L  // Must be set before use
    }
}

// --- Property Delegate for Validation ---
class ValidatedString(
    private val validator: (String) -> Boolean = { it.isNotBlank() }
) {
    private var value: String = ""

    operator fun getValue(thisRef: Any?, property: KProperty<*>): String = value

    operator fun setValue(thisRef: Any?, property: KProperty<*>, newValue: String) {
        require(validator(newValue)) {
            "Invalid value for ${property.name}: '$newValue'"
        }
        value = newValue
    }
}

class Person {
    var name: String by ValidatedString { it.length in 2..50 }
}
```

## Common Mistakes

```kotlin
// WRONG: Lazy under thread contention (creates multiple instances)
val instance by lazy {
    HeavyObject()  // Called twice if two threads check isEmpty simultaneously
}

// CORRECT: Lazy is thread-safe by default
val instance by lazy(LazyThreadSafetyMode.SYNCHRONIZED) {
    HeavyObject()  // Only one thread creates, others wait
}

// For single-threaded: lazy(LazyThreadSafetyMode.NONE)


// WRONG: Using mutable collection with delegation that expects immutable
class Config {
    val items: List<String> by lazy {
        mutableListOf("a", "b")  // Never mutated — use listOf
    }
}

// CORRECT: Use immutable
val items: List<String> by lazy { listOf("a", "b") }


// WRONG: Not initializing Delegates.notNull before use
class Timer {
    var duration: Long by Delegates.notNull()
}

// val t = Timer()
// println(t.duration)  // IllegalStateException: Property should be initialized


// WRONG: Class delegation with override confusion
interface Printer {
    fun print()
    fun printTwice()
}

class ConsolePrinter : Printer {
    override fun print() = println("Printing")
    override fun printTwice() { print(); print() }
}

class LoggingPrinter(p: Printer) : Printer by p {
    override fun print() {
        println("Log before")
        println("Log after")
    }
    // printTwice() still delegates to ConsolePrinter.printTwice()
    // which calls ConsolePrinter.print(), NOT LoggingPrinter.print()!
}
```

## Gotchas
- **`lazy` thread safety modes**: `SYNCHRONIZED` (default) — thread-safe, one initialization. `PUBLICATION` — can initialize multiple times but uses first result. `NONE` — not thread-safe (single-threaded only).
- **Map delegation type safety**: `by map` relies on unchecked casts. If the map has the wrong type for a key, you get a `ClassCastException` at runtime. Use with caution.
- **Delegation vs inheritance**: Use delegation over inheritance when you want to compose behavior. `by` delegation gives you all interface methods without boilerplate, and you can selectively override.
- **`observable` old value**: The `old` parameter in `observable` is the value before change. For initial set, `old` is the initial value passed to the constructor.
- **`vetoable` and validation**: The validation lambda should be pure (no side effects). If it throws, the property retains its old value but the exception propagates.
- **Property delegation restrictions**: Delegated properties cannot be used in `init` blocks of the same class for `by lazy`. The lazy delegate accesses the property after class initialization.
- **`lateinit` vs `Delegates.notNull`**: `lateinit` works only for `var` class properties (not primitives, not local vars). `Delegates.notNull` works for primitives and local vars.

## Related
- kotlin/stdlib/basics.md
- kotlin/stdlib/scope-functions.md
