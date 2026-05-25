---
id: "kotlin-stdlib-scope-functions"
title: "Kotlin Scope Functions: let, run, with, apply, also"
language: "kotlin"
category: "stdlib"
tags: ["kotlin", "scope-functions", "let", "run", "apply", "also", "with"]
version: "1.9+"
retrieval_hint: "kotlin scope functions let run with apply also context object lambda receiver"
last_verified: "2026-05-24"
confidence: "high"
---

# Kotlin Scope Functions: let, run, with, apply, also

## When to Use
- Performing operations on nullable objects safely
- Configuring objects after construction
- Computing values with temporary scope
- Adding side effects to expression chains

## Standard Pattern

```kotlin
data class Person(
    var name: String = "",
    var age: Int = 0,
    var email: String = ""
)

data class Order(
    val id: Int,
    val items: List<String>,
    val total: Double
)

// --- let — Transform nullable, return result ---
// Context: it (implicit parameter)
// Return: lambda result

fun findEmailLength(person: Person?): Int? {
    return person?.let {
        // Safe access on non-null person
        val email = it.email
        if (email.isNotEmpty()) email.length else null
    }
}

// --- run — Compute a value, context as receiver ---
// Context: this (receiver)
// Return: lambda result

fun formatOrder(order: Order): String {
    return order.run {
        // "this" refers to order
        "Order #$id: ${items.size} items, total $$total"
    }
}

// --- with — Group operations on an object, return result ---
// Context: this (receiver)
// Return: lambda result

fun displayOrder(order: Order): String {
    return with(order) {
        // "this" is order
        val summary = "Order $id"
        val itemList = items.joinToString(", ")
        "$summary\nItems: $itemList\nTotal: $$total"
    }
}

// --- apply — Configure object, return the object ---
// Context: this (receiver)
// Return: the context object

fun createAdminUser(): Person {
    return Person().apply {
        name = "Admin"
        age = 30
        email = "admin@example.com"
    }
    // Returns the Person with all fields set
}

// --- also — Perform side effects, return the object ---
// Context: it (implicit parameter)
// Return: the context object

fun createAndLogPerson(): Person {
    return Person(
        name = "Alice",
        age = 25,
        email = "alice@example.com"
    ).also {
        println("Created person: ${it.name}")
        logCreation(it)
    }
    // Returns the Person (unchanged)
}

// --- Comparison Table ---
// Function | Context | Return Value  | Use Case
// ---------|---------|---------------|---------
// let      | it      | lambda result | Nullable transformation
// run      | this    | lambda result | Compute with receiver
// with     | this    | lambda result | Group receiver calls
// apply    | this    | context obj   | Object configuration
// also     | it      | context obj   | Side effects

// --- Practical Examples ---

// Chaining nullable transformations
fun processOrder(order: Order?): String? {
    return order
        ?.takeIf { it.items.isNotEmpty() }
        ?.let { formatOrder(it) }
}

// Builder-style configuration
fun buildPerson(name: String, age: Int): Person {
    return Person().apply {
        this.name = name
        this.age = age
        email = "$name@example.com"
    }
}

// Nested scope functions (use with care)
fun complexValidation(person: Person): Boolean {
    return with(person) {
        name.isNotBlank() && age > 0 && email.contains("@")
    }
}

// Debugging/tracing
fun debugProcess(items: List<String>): List<String> {
    return items
        .filter { it.isNotBlank() }
        .also { println("After filter: $it") }
        .map { it.trim() }
        .also { println("After trim: $it") }
}

// --- Multiple return type decisions ---

// Use 'let' when you need to transform a value
val length: Int? = name?.let { it.length }

// Use 'run' when you need to compute something with the object
val isReady: Boolean = connection.run { isConnected && isAuthenticated }

// Use 'apply' when you need to configure the object
val config = ServerConfig().apply {
    host = "localhost"
    port = 8080
}

// Use 'also' for logging/side effects without changing the value
val user = fetchUser().also { log("Fetched user: ${it.id}") }

// Use 'with' when you need multiple calls on the same object
val info = with(person) { "$name ($age): $email" }
```

## Common Mistakes

```kotlin
// WRONG: Using apply instead of let for nullable transformation
val name: String? = getName()
name.apply {
    // "this" is String?, so length requires !! or ?.
    this?.length  // Must use safe call anyway
}

// CORRECT: Use let for nullable transformations
name?.let {
    it.length  // "it" is non-null String
}

// Or use run:
name?.run {
    length  // "this" is non-null String
}


// WRONG: Chaining scope functions excessively (readability suffers)
fun process(input: String?) {
    input?.let {
        it.uppercase()
    }?.let {
        it.reversed()
    }?.let {
        println(it)
    }
}

// CORRECT: Use direct calls for simple chains
fun process(input: String?) {
    input?.uppercase()?.reversed()?.let { println(it) }
}


// WRONG: Using apply when you need the return value
val result = person.apply {
    name.length  // Returns Person, not Int!
}

// CORRECT: Use run or let for transform
val result = person.run {
    name.length  // Returns Int
}

val result = person.let {
    it.name.length  // Returns Int
}


// WRONG: Not understanding 'this' vs 'it' in nested scope
class Outer {
    val items = listOf(1, 2, 3)

    fun process() {
        items.run {
            this.first()  // Refers to items (the receiver)
            // To access Outer: this@Outer
            println(this@Outer.items.size)  // Access outer
        }
    }
}

// CORRECT: Use labeled 'this' for nested scopes
this@Outer.items  // Access outer from inner scope
```

## Gotchas
- **Nested scope functions create context confusion**: When nesting `apply` inside `run`, `this` refers to the innermost receiver. Use labeled `this@label` to access outer receivers.
- **`apply` vs `also` semantic difference**: `apply` uses `this` (receiver) — ideal for configuring the object's properties. `also` uses `it` — ideal for side effects that don't need property access.
- **`run` vs `with` distinctions**: `run` is an extension function (called on the object). `with` is a normal function (object passed as argument). Both use `this` as context and return lambda result.
- **Return value confusion**: `apply` and `also` return the context object. `let`, `run`, and `with` return the lambda result. Mixing them up produces wrong types.
- **`let` for null checks**: `x?.let { }` is idiomatic for executing code only when `x` is non-null. Combine with `?:` for the else case: `x?.let { handle(it) } ?: handleNull()`.
- **Performance**: Scope functions are inlined by the compiler, so there's no runtime overhead. Use them freely for readability, but avoid deeply nested chains.
- **`takeIf` and `takeUnless` pair well**: `x.takeIf { condition }?.let { }` is the Kotlin idiom for "do something if condition is true."

## Related
- kotlin/stdlib/basics.md
- kotlin/stdlib/delegation.md
