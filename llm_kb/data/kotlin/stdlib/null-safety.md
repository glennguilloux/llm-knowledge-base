---
id: "kotlin-stdlib-null-safety"
title: "Kotlin Null Safety: Safe Calls, Elvis, and Scope Functions"
language: "kotlin"
category: "stdlib"
tags: ["kotlin", "null-safety", "safe-call", "elvis", "let", "also", "run", "platform-types"]
version: "1.9+"
retrieval_hint: "kotlin nullable types safe calls elvis operator let also run not-null assertion platform types"
last_verified: "2026-05-24"
confidence: "high"
---

# Kotlin Null Safety: Safe Calls, Elvis, and Scope Functions

## When to Use
- Handling nullable values safely in Kotlin
- Avoiding NullPointerException (Kotlin's type system prevents most NPEs at compile time)
- Working with Java interop where nullability is unknown
- Using scope functions (`let`, `also`, `run`, `apply`, `with`) for null-safe operations

## Standard Pattern

```kotlin
// Nullable type — the ? makes it explicit
var name: String? = "Kotlin"
name = null  // OK — nullable type

// Safe call operator (?.) — returns null if receiver is null
val length: Int? = name?.length  // null if name is null

// Safe call chaining
val city: String? = user?.address?.city  // null if any part is null

// Elvis operator (?:) — provide default when null
val displayName = name ?: "Unknown"  // "Unknown" if name is null

// Elvis with throw
val required = name ?: throw IllegalArgumentException("Name is required")

// Elvis with return
fun process(name: String?) {
    val safe = name ?: return  // Return early if null
    println(safe.length)
}

// let — execute block only if non-null, returns block result
val result = name?.let { nonNullName ->
    nonNullName.length  // Returns Int?
}

// also — side effects, returns the receiver
val logged = name?.also { println("Name is: $it") }

// run — execute block on receiver, returns block result
val uppercased = name?.run { uppercase() }

// Not-null assertion (!!) — use sparingly, throws NPE if null
val forced: String = name!!  // Throws NullPointerException if name is null

// Smart cast — compiler tracks null checks
if (name != null) {
    // Inside this block, name is smart-cast to String (non-null)
    println(name.length)  // No ?. needed
}

// Safe cast (as?) — returns null if cast fails
val any: Any = "hello"
val str: String? = any as? String   // "hello"
val num: Int? = any as? Int         // null
```

## Common Mistakes

```kotlin
// WRONG: Overusing !! (not-null assertion)
fun getLength(text: String?): Int {
    return text!!.length  // Crashes if null — defeats Kotlin's null safety
}

// CORRECT: Use safe call with elvis
fun getLength(text: String?): Int {
    return text?.length ?: 0
}

// WRONG: Not using smart cast after null check
fun process(text: String?) {
    if (text != null) {
        val len = text.length  // Smart cast works — no ?. needed
    }
    // val len2 = text.length  // Error — text is nullable outside the if block
}

// CORRECT: Use smart cast within the null-checked scope
fun process(text: String?) {
    if (text != null) {
        println(text.length)  // Smart cast to String
        println(text.uppercase())
    }
}

// WRONG: let without safe call (doesn't help)
val result = name.let { it.length }  // it is still String? — can't call .length

// CORRECT: Use ?.let for null-safe transformation
val result = name?.let { it.length }  // Returns Int?

// WRONG: Confusing let vs also
val length = name?.also { it.length }  // also returns the receiver (String?), not length

// CORRECT: Use let for transformation, also for side effects
val length = name?.let { it.length }     // Returns Int?
val logged = name?.also { println(it) }  // Returns String?

// WRONG: Not handling platform types from Java
val javaResult = javaObject.getValue()  // Platform type — could be null!
val length = javaResult.length  // Potential NPE at runtime

// CORRECT: Explicitly handle platform types
val javaResult: String? = javaObject.getValue()
val length = javaResult?.length ?: 0
```

## Gotchas
- Kotlin's type system distinguishes `String` (non-null) from `String?` (nullable) at compile time. Most NPEs are prevented before runtime.
- `?.` (safe call) returns `null` if the receiver is null. The return type is always nullable.
- `?:` (elvis) is Kotlin's ternary replacement: `x ?: y` is like `x != null ? x : y`.
- `!!` (not-null assertion) converts nullable to non-null but throws NPE at runtime if the value IS null. Avoid it — it's an escape hatch.
- Smart cast: after `if (x != null)`, the compiler treats `x` as non-null within that scope. Works with `when`, `&&`, `||`, and early returns.
- `?.let { }` is the idiomatic pattern for "do something only if non-null". The lambda receives a non-null value.
- Platform types (`T!`) come from Java interop. The compiler doesn't know if they're null-safe. Handle them explicitly.
- `as?` (safe cast) returns null on failure instead of throwing `ClassCastException`.
- Scope functions: `let`/`run`/`with` return the lambda result. `also`/`apply` return the receiver object.

## Related
- kotlin/stdlib/basics.md
- kotlin/stdlib/functions-lambdas.md
- kotlin/stdlib/error-handling.md
- kotlin/stdlib/classes.md
