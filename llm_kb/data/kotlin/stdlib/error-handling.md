---
id: "kotlin-stdlib-error-handling"
title: "Kotlin Error Handling: Result, Sealed Classes, and runCatching"
language: "kotlin"
category: "stdlib"
tags: ["kotlin", "error-handling", "result", "sealed-class", "runCatching", "exceptions"]
version: "1.9+"
retrieval_hint: "kotlin Result type custom exceptions sealed class errors runCatching Either pattern Arrow"
last_verified: "2026-05-24"
confidence: "high"
---

# Kotlin Error Handling: Result, Sealed Classes, and runCatching

## When to Use
- Handling errors in a functional style with `Result<T>`
- Modeling domain errors with sealed classes
- Wrapping exception-throwing code with `runCatching`
- Using Arrow's Either for advanced error handling
- Avoiding try/catch boilerplate in business logic

## Standard Pattern

```kotlin
// Result type — built into Kotlin stdlib
fun divide(a: Int, b: Int): Result<Int> {
    return if (b == 0) {
        Result.failure(ArithmeticException("Division by zero"))
    } else {
        Result.success(a / b)
    }
}

// Using Result
fun calculate(): Result<Int> {
    return runCatching {
        val a = readInt()
        val b = readInt()
        divide(a, b).getOrThrow()
    }
}

// Result chaining with map and recover
fun processValue(input: String): Result<Int> {
    return input.toIntOrNull()
        ?.let { Result.success(it) }
        ?: Result.failure(NumberFormatException("Invalid: $input"))
}

// runCatching — wraps exception-throwing code
fun parseJson(json: String): Result<User> = runCatching {
    Json.decodeFromString<User>(json)
}

// Sealed class for domain errors — the most Kotlin-idiomatic approach
sealed class AppError {
    data class NetworkError(val code: Int, val message: String) : AppError()
    data class ValidationError(val field: String, val reason: String) : AppError()
    data class NotFoundError(val resource: String, val id: Any) : AppError()
    data class UnauthorizedError(val reason: String) : AppError()
    object UnknownError : AppError()
}

// Using sealed class errors
fun fetchUser(id: Int): Result<User, AppError> {
    if (id <= 0) return Result.failure(AppError.ValidationError("id", "Must be positive"))
    return try {
        val user = api.getUser(id)
        Result.success(user)
    } catch (e: HttpException) {
        when (e.code()) {
            404 -> Result.failure(AppError.NotFoundError("User", id))
            401 -> Result.failure(AppError.UnauthorizedError("Invalid token"))
            else -> Result.failure(AppError.NetworkError(e.code(), e.message()))
        }
    } catch (e: Exception) {
        Result.failure(AppError.UnknownError)
    }
}

// Exhaustive when for error handling
fun handleError(error: AppError): String = when (error) {
    is AppError.NetworkError -> "Network error ${error.code}: ${error.message}"
    is AppError.ValidationError -> "Invalid ${error.field}: ${error.reason}"
    is AppError.NotFoundError -> "${error.resource} #${error.id} not found"
    is AppError.UnauthorizedError -> "Unauthorized: ${error.reason}"
    AppError.UnknownError -> "An unknown error occurred"
}

// Custom exceptions for exceptional cases
class InsufficientFundsException(
    val accountId: String,
    val balance: BigDecimal,
    val requested: BigDecimal
) : IllegalStateException(
    "Account $accountId has insufficient funds: balance=$balance, requested=$requested"
)

// Using custom exceptions
class BankService {
    fun transfer(from: String, to: String, amount: BigDecimal) {
        val balance = getBalance(from)
        if (balance < amount) {
            throw InsufficientFundsException(from, balance, amount)
        }
        // Perform transfer...
    }
    fun getBalance(accountId: String): BigDecimal = BigDecimal("100.00")
}

// Arrow Either pattern (requires Arrow library)
// Either<Error, Success> — Right is success, Left is error
/*
import arrow.core.Either
import arrow.core.left
import arrow.core.right

fun fetchUser(id: Int): Either<AppError, User> {
    if (id <= 0) return AppError.ValidationError("id", "Must be positive").left()
    return try {
        api.getUser(id).right()
    } catch (e: Exception) {
        AppError.UnknownError.left()
    }
}

// Chaining Either operations
fun processUser(id: Int): Either<AppError, ProcessedUser> {
    return fetchUser(id)
        .map { it.toProcessed() }
        .map { enrichWithPermissions(it) }
}
*/
```

## Common Mistakes

```kotlin
// WRONG: Using Result.getOrThrow() without checking first
val result = parseJson(json)
val user = result.getOrThrow()  // Crashes if parsing failed!

// CORRECT: Check result before using value
val result = parseJson(json)
result.onSuccess { user -> println(user.name) }
result.onFailure { error -> println("Parse failed: ${error.message}") }

// Or use getOrNull()
val user = result.getOrNull() ?: return

// WRONG: Catching all exceptions with generic catch
try {
    riskyOperation()
} catch (e: Exception) {  // Too broad — catches everything including CancellationException
    println("Error: $e")
}

// CORRECT: Catch specific exceptions
try {
    riskyOperation()
} catch (e: IOException) {
    println("IO error: ${e.message}")
} catch (e: IllegalArgumentException) {
    println("Invalid argument: ${e.message}")
}

// WRONG: Not using sealed class for errors (using strings or codes)
fun fetchUser(id: Int): Pair<User?, String?> {
    // String errors are not type-safe — compiler can't help
    return Pair(null, "User not found")
}

// CORRECT: Use sealed class for type-safe error handling
fun fetchUser(id: Int): Result<User, AppError> {
    // Compiler ensures all error cases are handled
    return Result.failure(AppError.NotFoundError("User", id))
}

// WRONG: Using runCatching and ignoring the failure
runCatching {
    riskyOperation()
}  // Failure is silently ignored!

// CORRECT: Handle both success and failure
runCatching {
    riskyOperation()
}.onFailure { error ->
    logger.error("Operation failed", error)
}.getOrNull()?.let { result ->
    process(result)
}

// WRONG: Throwing generic Exception
throw Exception("Something went wrong")  // No context, no type safety

// CORRECT: Throw specific exceptions with context
throw InsufficientFundsException(accountId, balance, requested)
```

## Gotchas
- `Result<T>` is built into Kotlin stdlib. Use `Result.success()` and `Result.failure()` to create, `getOrThrow()`, `getOrNull()`, `getOrDefault()` to extract.
- `runCatching { }` catches ALL exceptions including `CancellationException`. Use `runCatching` carefully in coroutines.
- Sealed class errors + exhaustive `when` is the most Kotlin-idiomatic error handling pattern. The compiler ensures all cases are handled.
- `Result` cannot be used directly as a return type in suspend functions in some contexts. Use `sealed class` or `Either` instead.
- Arrow's `Either<Left, Right>` is a more powerful alternative to `Result` — it supports chaining with `map`, `flatMap`, `fold`.
- Custom exceptions should carry context (field names, IDs, values) to make debugging easier.
- Never catch `CancellationException` in coroutines — it's used by the coroutine framework for structured cancellation.
- `onSuccess` and `onFailure` on `Result` are side-effect handlers — they return the same `Result` (not the transformed value).

## Related
- kotlin/stdlib/classes.md
- kotlin/stdlib/coroutines.md
- kotlin/stdlib/basics.md
- kotlin/stdlib/null-safety.md
