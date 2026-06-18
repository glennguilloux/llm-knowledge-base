---
id: "kotlin-coroutines-flow"
title: "Kotlin Flow: Cold/Hot Flows, Operators, StateFlow vs SharedFlow"
language: "kotlin"
category: "concurrency"
tags: ["kotlin", "coroutines", "flow", "stateflow", "sharedflow", "cold-flow"]
version: "1.7+"
retrieval_hint: "kotlin flow cold hot StateFlow SharedFlow operators collect testing"
last_verified: "2026-05-24"
confidence: "high"
---

# Kotlin Flow: Cold/Hot Flows, Operators, StateFlow vs SharedFlow

## When to Use
- Representing asynchronous sequences of values
- Reactively processing data streams
- Sharing state between ViewModel and UI
- Broadcasting events to multiple collectors

## Standard Pattern

```kotlin
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlin.system.measureTimeMillis

// --- Cold Flow (Flow builder) ---
// Cold: starts fresh for each collector, no data shared
fun fetchUsers(): Flow<User> = flow {
    emit(Loading)
    try {
        val users = api.getUsers()  // Suspend call
        emit(Success(users))
    } catch (e: Exception) {
        emit(Error(e.message ?: "Unknown"))
    }
}.flowOn(Dispatchers.IO)  // Run upstream on IO thread

// --- Flow Operators ---
data class User(val id: Int, val name: String, val age: Int)

val userFlow: Flow<User> = (1..10).asFlow().map { id ->
    User(id, "User$id", (20..60).random())
}

suspend fun flowOperators() {
    // Filter
    userFlow
        .filter { it.age >= 30 }
        .collect { println("Adult: ${it.name}") }

    // Map + transform
    userFlow
        .map { it.name.uppercase() }
        .collect { println(it) }

    // FlatMapConcat (sequential)
    userFlow
        .flatMapConcat { user -> fetchDetails(user.id) }
        .collect { /* sequential, one at a time */ }

    // FlatMapMerge (concurrent, order not guaranteed)
    userFlow
        .flatMapMerge(concurrency = 3) { user -> fetchDetails(user.id) }
        .collect { /* up to 3 concurrent requests */ }

    // Catch errors
    userFlow
        .map { check(it.age > 0); it }
        .catch { e -> println("Error: $e") }
        .collect { /* safe from upstream errors */ }

    // Debounce (for search inputs)
    val searchFlow = MutableStateFlow("")
    searchFlow
        .debounce(300)
        .collect { query -> performSearch(query) }
}

// --- StateFlow (hot, state holder) ---
// Holds a single value, emits updates to collectors
class UserRepository {
    private val _users = MutableStateFlow<List<User>>(emptyList())
    val users: StateFlow<List<User>> = _users.asStateFlow()

    fun updateUsers(newUsers: List<User>) {
        _users.value = newUsers
    }
}

// --- SharedFlow (hot, event bus) ---
// Emits events to all collectors, no initial value
class EventBus {
    private val _events = MutableSharedFlow<UiEvent>(
        replay = 0,          // No replay for new subscribers
        extraBufferCapacity = 64  // Buffer for backpressure
    )
    val events: SharedFlow<UiEvent> = _events.asSharedFlow()

    suspend fun emit(event: UiEvent) {
        _events.emit(event)
    }
}

sealed interface UiEvent {
    data class ShowSnackbar(val message: String) : UiEvent
    data class NavigateTo(val route: String) : UiEvent
}

// --- StateFlow vs SharedFlow Decision ---
// StateFlow: State (single value, has initial, always has value)
// SharedFlow: Events (no initial value, replay configurable, one-shot)

// --- Flow Collection Strategies ---
suspend fun collectionStrategies() {
    val flow = (1..5).asFlow()

    // collect — process each value
    flow.collect { println(it) }

    // collectLatest — cancel previous if new value arrives
    flow
        .map { delay(100); it }
        .collectLatest { value ->
            delay(50)  // Cancelled by next value
            println("Processed: $value")
        }

    // conflate — skip intermediate values if collector is slow
    flow
        .conflate()
        .collect { value ->
            delay(100)  // Skips values if slow
            println("Got: $value")
        }

    // Single — expects exactly one value
    val singleValue: Int = flow.single()

    // toList / toSet — collect all to collection
    val list: List<Int> = flow.toList()
}

// --- Flow Testing ---
// In test (uses kotlinx-coroutines-test):
// @Test
// fun `test flow emissions`() = runTest {
//     val flow = flowOf(1, 2, 3)
//     val result = flow.toList()
//     assertEquals(listOf(1, 2, 3), result)
// }
```

## Common Mistakes

```kotlin
// WRONG: Blocking in flow builder
val badFlow = flow {
    Thread.sleep(1000)  // Blocks the coroutine!
    emit(compute())
}.flowOn(Dispatchers.IO)  // Still blocks, wastes thread

// CORRECT: Use suspend functions
val goodFlow = flow {
    delay(1000)  // Suspends, doesn't block
    emit(compute())
}


// WRONG: Missing catch operator (downstream crash)
userFlow
    .map { it.let { dangerousOperation() } }
    .collect { /* upstream exception crashes here */ }

// CORRECT: Catch upstream errors
userFlow
    .map { dangerousOperation() }
    .catch { e -> println("Error: $e") }
    .collect { /* safe */ }


// WRONG: StateFlow without initial value
val state = MutableStateFlow(/* No initial value! */)
// StateFlow requires an initial value

// CORRECT: Provide initial value
val state = MutableStateFlow(UiState())


// WRONG: Collecting from wrong scope (leaks)
class MyActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        viewModel.someFlow
            .onEach { updateUI(it) }
            .launchIn(GlobalScope)  // Leaks!
    }
}

// CORRECT: Use lifecycle-aware scope
// In Activity: lifecycleScope
// In ViewModel: viewModelScope
// viewModel.someFlow.onEach { }.launchIn(lifecycleScope)
```

## Gotchas
- **`flowOn` context preservation**: `flowOn` affects only upstream operators (before `flowOn`). Downstream operators run in the default context. Multiple `flowOn` calls create context switches.
- **Cancellation in `collect`**: If the collector function in `collect` takes too long, the coroutine can be cancelled. Use `conflate` or `collectLatest` to handle backpressure.
- **`SharedFlow` replay vs `StateFlow`**: `StateFlow` replays the latest value (always has one). `SharedFlow` with `replay = 0` never replays. Use `StateFlow` for state, `SharedFlow` for one-shot events.
- **Cold flow vs hot flow**: Cold flows (created with `flow {}`) run the producer for each collector. Hot flows (`StateFlow`, `SharedFlow`) share data between collectors. MutableStateFlow is hot.
- **`catch` operator position**: `catch` only catches upstream exceptions (operators above it). Place `catch` after `map`/`filter` but before `collect` to catch all upstream errors.
- **Flow completion**: `onCompletion { }` runs when the flow completes or is cancelled. Use it for cleanup, not for error handling (use `catch` for that).
- **`asFlow()` on collections**: `.asFlow()` on a `List` emits all items immediately. For infinite sequences, use `flow { }` builder with a loop.

## Related
- kotlin/stdlib/coroutines.md
- kotlin/testing/mocking.md
- kotlin/android/compose-state.md
