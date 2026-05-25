---
id: "kotlin-stdlib-coroutines"
title: "Kotlin Coroutines: suspend, launch, async, and Flow"
language: "kotlin"
category: "stdlib"
tags: ["kotlin", "coroutines", "suspend", "launch", "async", "flow", "structured-concurrency"]
version: "1.9+"
retrieval_hint: "kotlin coroutines suspend functions launch async Dispatchers coroutineScope Flow structured concurrency"
last_verified: "2026-05-24"
confidence: "high"
---

# Kotlin Coroutines: suspend, launch, async, and Flow

## When to Use
- Performing asynchronous operations without callbacks
- Concurrent execution of multiple tasks
- Streaming data with Flow
- Replacing RxJava or callback-based APIs with structured concurrency
- Background tasks in Android or server-side Kotlin

## Standard Pattern

```kotlin
import kotlinx.coroutines.*

// suspend function — can be suspended without blocking a thread
suspend fun fetchUser(id: Int): User {
    delay(1000)  // Simulates network call — doesn't block the thread
    return User(id, "User $id")
}

// launch — starts a coroutine, returns Job (fire-and-forget)
fun main() = runBlocking {
    val job: Job = launch {
        val user = fetchUser(1)
        println("Fetched: ${user.name}")
    }
    job.join()  // Wait for completion
}

// async — starts a coroutine that returns a value, returns Deferred<T>
suspend fun fetchMultiple(): List<User> = coroutineScope {
    val user1 = async { fetchUser(1) }
    val user2 = async { fetchUser(2) }
    val user3 = async { fetchUser(3) }
    // All three run concurrently
    listOf(user1.await(), user2.await(), user3.await())
}

// Dispatchers — control which thread pool runs the coroutine
suspend fun processData() = withContext(Dispatchers.IO) {
    val data = File("data.txt").readText()
    data.uppercase()
}

// coroutineScope — creates a scope that waits for all children
suspend fun loadDashboard(): Dashboard = coroutineScope {
    val user = async { fetchUser(1) }
    val orders = async { fetchOrders(1) }
    val notifications = async { fetchNotifications(1) }
    Dashboard(user.await(), orders.await(), notifications.await())
}

// Flow — cold stream of values
fun fetchNews(): Flow<News> = flow {
    while (true) {
        val news = api.getLatestNews()
        emit(news)  // Emit a value
        delay(60_000)  // Wait 1 minute
    }
}

// Collecting a flow
suspend fun observeNews() {
    fetchNews()
        .filter { it.category == "tech" }
        .map { it.title }
        .collect { title ->
            println("New article: $title")
        }
}

data class User(val id: Int, val name: String)
data class Dashboard(val user: User, val orders: List<Any>, val notifications: List<Any>)
data class News(val title: String, val category: String)
```

## Common Mistakes

```kotlin
// WRONG: Calling suspend function from non-suspend context
fun main() {
    val user = fetchUser(1)  // Compile error: suspend function from non-suspend context
}

// CORRECT: Use runBlocking or another suspend function
fun main() = runBlocking {
    val user = fetchUser(1)  // OK
}

// WRONG: Using GlobalScope (breaks structured concurrency)
fun loadData() {
    GlobalScope.launch {
        fetchUser(1)  // Not bound to any scope — can leak!
    }
}

// CORRECT: Use a coroutineScope tied to lifecycle
class MyViewModel : ViewModel() {
    fun loadData() {
        viewModelScope.launch {
            fetchUser(1)  // Cancelled when ViewModel is cleared
        }
    }
}

// WRONG: Blocking the thread instead of suspending
suspend fun fetchData(): String {
    Thread.sleep(1000)  // Blocks the thread!
    return "data"
}

// CORRECT: Use delay (suspends without blocking)
suspend fun fetchData(): String {
    delay(1000)  // Suspends — thread is free for other coroutines
    return "data"
}

// WRONG: Not handling cancellation
suspend fun longRunning() {
    for (i in 1..1000) {
        heavyComputation(i)  // Won't respond to cancellation
    }
}

// CORRECT: Check cancellation or use yield
suspend fun longRunning() {
    for (i in 1..1000) {
        ensureActive()  // Throws CancellationException if cancelled
        heavyComputation(i)
    }
}

// WRONG: Confusing async with launch
val result = launch { compute() }  // Returns Job, not the result

// CORRECT: Use async for results, launch for side effects
val result = async { compute() }  // Returns Deferred<T>
val value = result.await()        // Get the value
```

## Gotchas
- `suspend` functions can only be called from coroutines or other suspend functions. Use `runBlocking {}` to bridge suspend and non-suspend code.
- `launch` returns a `Job` (fire-and-forget). `async` returns a `Deferred<T>` (produces a value). Use `await()` on `Deferred` to get the result.
- `Dispatchers.IO` is for blocking I/O (file, network, DB). `Dispatchers.Default` is for CPU-intensive work. `Dispatchers.Main` is for UI updates (Android).
- `coroutineScope {}` suspends until ALL child coroutines complete. If one child fails, all siblings are cancelled (structured concurrency).
- `supervisorScope {}` — child failures don't cancel siblings. Use for independent tasks.
- `Flow` is cold — it doesn't produce values until collected. Each collector gets its own stream.
- `delay()` suspends without blocking. `Thread.sleep()` blocks the thread — never use it in coroutines.
- `GlobalScope` breaks structured concurrency. Always use a scope tied to a lifecycle.
- Coroutine cancellation is cooperative — the coroutine must check `ensureActive()`, `yield()`, or call other suspend functions to be cancellable.

## Related
- kotlin/stdlib/functions-lambdas.md
- kotlin/stdlib/error-handling.md
- kotlin/web/ktor.md
- kotlin/android/basics.md
