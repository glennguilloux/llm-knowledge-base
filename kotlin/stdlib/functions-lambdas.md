---
id: "kotlin-stdlib-functions-lambdas"
title: "Kotlin Functions, Lambdas, and Extension Functions"
language: "kotlin"
category: "stdlib"
tags: ["kotlin", "functions", "lambdas", "extension-functions", "higher-order", "inline"]
version: "1.9+"
retrieval_hint: "kotlin extension functions lambda syntax it keyword inline functions higher-order functions"
last_verified: "2026-05-24"
confidence: "high"
---

# Kotlin Functions, Lambdas, and Extension Functions

## When to Use
- Writing functions in Kotlin — understanding default args, named args, and expression bodies
- Using lambdas for callbacks, collection operations, and functional patterns
- Creating extension functions to add behavior to existing types
- Writing higher-order functions that accept or return other functions

## Standard Pattern

```kotlin
// Basic function with default and named arguments
fun greet(name: String, greeting: String = "Hello"): String {
    return "$greeting, $name!"
}
greet("Alice")                          // "Hello, Alice!"
greet("Bob", greeting = "Hi")           // "Hi, Bob!"

// Expression body (single expression — no braces needed)
fun double(x: Int): Int = x * 2

// Lambda syntax
val sum: (Int, Int) -> Int = { a, b -> a + b }
val greet: (String) -> String = { name -> "Hello, $name!" }

// 'it' — implicit single parameter name
val square: (Int) -> Int = { it * it }

// Lambda as last parameter — trailing lambda syntax
fun processItems(items: List<Int>, action: (Int) -> Unit) {
    items.forEach(action)
}
processItems(listOf(1, 2, 3)) { println(it) }

// Extension function — add method to existing type
fun String.addExclamation(): String = "$this!"
"Kotlin".addExclamation()  // "Kotlin!"

// Extension function with generics
fun <T> List<T>.secondOrNull(): T? = if (size > 1) this[1] else null
listOf(1, 2, 3).secondOrNull()  // 2

// Higher-order function — returns a function
fun multiplier(factor: Int): (Int) -> Int {
    return { value -> value * factor }
}
val triple = multiplier(3)
triple(5)  // 15

// Inline function — no lambda object allocation at runtime
inline fun measureTime(block: () -> Unit): Long {
    val start = System.nanoTime()
    block()
    return System.nanoTime() - start
}

// Function type with receiver — like extension function as a lambda
fun buildString(builder: StringBuilder.() -> Unit): String {
    val sb = StringBuilder()
    sb.builder()
    return sb.toString()
}
val result = buildString {
    append("Hello")
    append(" ")
    append("World")
}  // "Hello World"

// Scope functions — let, also, run, apply
val name: String? = "Kotlin"
val length = name?.let { it.length }       // let: transform, returns result
val logged = name?.also { println("Processing: $it") }  // also: side effects, returns receiver
val uppercased = name?.run { uppercase() }  // run: execute block, returns result
val list = mutableListOf<Int>().apply {     // apply: configure, returns receiver
    add(1)
    add(2)
    add(3)
}
```

## Common Mistakes

```kotlin
// WRONG: Not using trailing lambda syntax
processItems(listOf(1, 2, 3), { println(it) })

// CORRECT: Lambda outside parentheses (idiomatic Kotlin)
processItems(listOf(1, 2, 3)) { println(it) }

// WRONG: Using return inside lambda (returns from enclosing function)
fun process(items: List<Int>) {
    items.forEach {
        if (it == 0) return  // Returns from process(), not just the lambda!
    }
}

// CORRECT: Use labeled return
fun process(items: List<Int>) {
    items.forEach {
        if (it == 0) return@forEach  // Returns from lambda only
    }
}

// WRONG: Extension function resolved statically — not polymorphic
open class Animal
class Dog : Animal()
fun Animal.name() = "Animal"
fun Dog.name() = "Dog"
val animal: Animal = Dog()
// animal.name() returns "Animal" — not "Dog"!

// CORRECT: Understand that extension functions are resolved statically
// Use virtual dispatch (override) for polymorphic behavior

// WRONG: Not using inline for higher-order functions with lambdas
fun execute(block: () -> Unit) {
    block()  // Creates a Function object each call
}

// CORRECT: Use inline to avoid lambda allocation overhead
inline fun execute(block: () -> Unit) {
    block()  // Inlined at call site — no Function object
}

// WRONG: Confusing let vs also
val result = name?.also { it.length }  // also returns the receiver (String?), not length

// CORRECT: Use let for transformation, also for side effects
val result = name?.let { it.length }  // Returns Int?
```

## Gotchas
- Extension functions are resolved **statically** at compile time, not dynamically. They don't modify the class — they're syntactic sugar for static utility functions.
- `inline` functions with lambda parameters avoid creating `Function` objects at runtime — the lambda body is inlined at the call site.
- `crossinline` prevents non-local returns in an inlined lambda. `noinline` excludes a lambda parameter from inlining.
- Trailing lambda syntax: if the last parameter is a function, the lambda can go outside the parentheses. If it's the ONLY function parameter, you can omit the parentheses entirely.
- `return` inside a lambda returns from the **enclosing function**, not the lambda. Use `return@label` for local return.
- Scope functions (`let`, `also`, `run`, `apply`, `with`) differ in what `this`/`it` refers to and what they return. `let`/`run`/`with` return the lambda result; `also`/`apply` return the receiver.
- `it` is the implicit name for a single lambda parameter. For multiple parameters, name them explicitly: `{ a, b -> a + b }`.

## Related
- kotlin/stdlib/basics.md
- kotlin/stdlib/classes.md
- kotlin/stdlib/collections.md
- kotlin/stdlib/coroutines.md
