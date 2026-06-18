---
id: "kotlin-stdlib-basics"
title: "Kotlin Basics: val, var, Type Inference, Null Safety"
language: "kotlin"
category: "stdlib"
tags: ["kotlin", "basics", "val", "var", "type-inference", "null-safety", "string-template"]
version: "1.9+"
retrieval_hint: "kotlin val var type inference string template null safety basic syntax differences from Java"
last_verified: "2026-05-24"
confidence: "high"
---

# Kotlin Basics: val, var, Type Inference, Null Safety

## When to Use
- Writing any Kotlin code — these are the foundational concepts
- Migrating from Java to Kotlin and understanding key differences
- Declaring variables, properties, and functions for the first time in Kotlin
- Small LLMs frequently confuse Kotlin and Java syntax — this entry clarifies the differences

## Standard Pattern

```kotlin
// val = read-only (final in Java), var = mutable
val name: String = "Kotlin"  // Explicit type
val version = 1.9             // Type inferred
var counter = 0               // Mutable variable
counter++                     // OK — var can be reassigned

// String templates — no more String.format or concatenation
val greeting = "Hello, $name!"
val length = "Length: ${name.length}"  // Expressions in ${}

// Null safety at compile time
var nullable: String? = "value"  // ? makes it nullable
nullable = null                   // OK
val len = nullable?.length ?: 0   // Safe call + elvis operator

// Type inference works everywhere
val numbers = listOf(1, 2, 3)           // List<Int>
val map = mapOf("a" to 1, "b" to 2)     // Map<String, Int>
val filtered = numbers.filter { it > 1 }  // 'it' is the single lambda param

// Basic function with inferred return type
fun greet(name: String): String = "Hello, $name!"

// Function with block body and explicit return type
fun sum(a: Int, b: Int): Int {
    return a + b
}
```

## Common Mistakes

```kotlin
// WRONG: Using var when val should be used (Java habit)
var name = "Kotlin"
name = "Java"  // Works but defeats Kotlin's preference for immutability

// CORRECT: Use val unless you need mutability
val name = "Kotlin"

// WRONG: Not using type inference (Java-style redundant types)
val name: String = "Kotlin"
val number: Int = 42

// CORRECT: Let the compiler infer types when obvious
val name = "Kotlin"
val number = 42

// WRONG: Using !! (not-null assertion) instead of proper null handling
fun getLength(text: String?): Int {
    return text!!.length  // Crashes with NPE if text is null
}

// CORRECT: Use safe call with elvis operator
fun getLength(text: String?): Int {
    return text?.length ?: 0
}

// WRONG: Using new keyword (doesn't exist in Kotlin)
val list = new ArrayList<String>()

// CORRECT: Call the constructor directly — no 'new' keyword
val list = ArrayList<String>()

// WRONG: Using Java-style string concatenation
val message = "Hello, " + name + "! You have " + count + " items."

// CORRECT: Use string templates
val message = "Hello, $name! You have $count items."
```

## Gotchas
- `val` is NOT a constant — it's a read-only reference (like `final` in Java). For compile-time constants, use `const val`.
- `var` should be the exception, not the rule. Default to `val` and only use `var` when the value truly needs to change.
- The `?.` safe call operator returns `null` if the receiver is null — it short-circuits the entire chain.
- `?:` (elvis operator) provides a default value when the left side is null. It's Kotlin's replacement for `x != null ? x : y`.
- Kotlin does NOT have `new` — constructors are called like regular functions: `ArrayList<String>()`.
- `it` is the implicit name for a single lambda parameter. Use it for short lambdas; name the parameter explicitly for clarity in complex cases.
- Kotlin's `==` calls `.equals()` (structural equality). Use `===` for reference equality (like `==` in Java).

## Related
- kotlin/stdlib/null-safety.md
- kotlin/stdlib/collections.md
- kotlin/stdlib/functions-lambdas.md
