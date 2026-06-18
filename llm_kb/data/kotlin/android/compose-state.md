---
id: "kotlin-android-compose-state"
title: "Jetpack Compose State Management: remember, StateFlow, ViewModel"
language: "kotlin"
category: "web"
tags: ["kotlin", "jetpack-compose", "state", "viewmodel", "stateflow", "side-effects"]
version: "1.5+"
retrieval_hint: "kotlin jetpack compose state remember mutableStateOf StateFlow ViewModel side effects LaunchedEffect"
last_verified: "2026-05-24"
confidence: "high"
---

# Jetpack Compose State Management: remember, StateFlow, ViewModel

## When to Use
- Managing UI state in Jetpack Compose
- Connecting ViewModel to Compose UI
- Handling side effects with LaunchedEffect and DisposableEffect
- Collecting flows from ViewModel

## Standard Pattern

```kotlin
import androidx.compose.runtime.*
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.compose.viewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

// --- ViewModel with StateFlow ---
data class UiState(
    val isLoading: Boolean = false,
    val data: String? = null,
    val error: String? = null
)

class MyViewModel : ViewModel() {
    private val _uiState = MutableStateFlow(UiState())
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()

    fun loadData() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            try {
                val result = fetchFromApi()  // Suspend function
                _uiState.value = UiState(data = result)
            } catch (e: Exception) {
                _uiState.value = UiState(error = e.message)
            }
        }
    }
}

// --- Composable Collecting State ---
@Composable
fun DataScreen(
    viewModel: MyViewModel = viewModel()
) {
    val uiState by viewModel.uiState.collectAsState()

    // Trigger data load on first composition
    LaunchedEffect(Unit) {
        viewModel.loadData()
    }

    when {
        uiState.isLoading -> LoadingIndicator()
        uiState.error != null -> ErrorMessage(uiState.error!!)
        uiState.data != null -> DataContent(uiState.data!!)
    }
}

// --- Local State (remember) ---
@Composable
fun SearchBar(
    onSearch: (String) -> Unit
) {
    var query by remember { mutableStateOf("") }
    var isExpanded by remember { mutableStateOf(false) }

    OutlinedTextField(
        value = query,
        onValueChange = {
            query = it
            isExpanded = it.isNotEmpty()
        },
        modifier = Modifier.fillMaxWidth(),
        trailingIcon = {
            if (query.isNotEmpty()) {
                IconButton(onClick = {
                    query = ""
                    isExpanded = false
                }) {
                    // Close icon
                }
            }
        }
    )
}

// --- rememberSaveable (survives configuration change) ---
@Composable
fun FormWithRotationSafeState() {
    var name by rememberSaveable { mutableStateOf("") }
    // Survives screen rotation unlike plain remember

    TextField(value = name, onValueChange = { name = it })
}

// --- Side Effects ---
@Composable
fun SideEffectExamples() {
    // LaunchedEffect — runs once when key enters composition
    LaunchedEffect(Unit) {
        val data = fetchInitialData()
        // Update state with result
    }

    // LaunchedEffect with key — re-runs when key changes
    var userId by remember { mutableStateOf(1) }
    LaunchedEffect(userId) {
        val user = fetchUser(userId)
        // Re-fetches when userId changes
    }

    // DisposableEffect — cleanup on removal
    DisposableEffect(Unit) {
        val observer = registerLifecycleObserver()
        onDispose {
            observer.unregister()  // Cleanup
        }
    }

    // rememberUpdatedState — avoid stale lambda captures
    val onEvent by rememberUpdatedState { /* latest handler */ }
    LaunchedEffect(Unit) {
        // Always calls the latest onEvent
        onEvent()
    }
}

// --- Derived State ---
@Composable
fun DerivedStateExample(items: List<String>, query: String) {
    val filteredItems by remember {
        derivedStateOf {
            items.filter { it.contains(query, ignoreCase = true) }
        }
    }
    // filteredItems only recomputes when items or query changes
}

// --- SnapshotFlow (convert Compose state to Flow) ---
@Composable
fun SnapshotFlowExample() {
    var searchQuery by remember { mutableStateOf("") }

    LaunchedEffect(Unit) {
        snapshotFlow { searchQuery }
            .debounce(300)
            .collect { query ->
                performSearch(query)
            }
    }
}
```

## Common Mistakes

```kotlin
// WRONG: Mutable state outside composition scope
@Composable
fun BadCounter() {
    var count = 0  // Regular var, not state!
    Button(onClick = { count++ }) {
        Text("Count: $count")  // Never updates!
    }
}

// CORRECT: Use mutableStateOf with remember
@Composable
fun GoodCounter() {
    var count by remember { mutableStateOf(0) }
    Button(onClick = { count++ }) {
        Text("Count: $count")  // Updates on recomposition
    }
}


// WRONG: Side effects directly in composable (called on every recomposition)
@Composable
fun UserProfile(userId: Int) {
    val user = fetchUser(userId)  // Called every recomposition!
    Text(user.name)
}

// CORRECT: Side effects in LaunchedEffect
@Composable
fun UserProfile(userId: Int) {
    var user by remember { mutableStateOf<User?>(null) }
    LaunchedEffect(userId) {
        user = fetchUser(userId)  // Only when userId changes
    }
    user?.let { Text(it.name) }
}


// WRONG: Collecting flow from wrong scope
@Composable
fun BadFlowCollection() {
    val viewModel: MyViewModel = viewModel()
    val state = viewModel.uiState // Not collected!

    // StateFlow won't emit without collectAsState()
}

// CORRECT: Use collectAsState
@Composable
fun GoodFlowCollection() {
    val viewModel: MyViewModel = viewModel()
    val state by viewModel.uiState.collectAsState()
}
```

## Gotchas
- **LaunchedEffect cancellation**: When the key changes, the previous `LaunchedEffect` coroutine is cancelled. For cleanup that shouldn't be cancelled, use a separate `DisposableEffect`.
- **Snapshot state thread safety**: Compose snapshot state is thread-safe within recomposition. Modifying state from a background thread updates the snapshot correctly and triggers recomposition.
- **Recomposition count**: Excessive recompositions degrade performance. Use `derivedStateOf` for computed state, stable keys in lists, and `remember` for expensive computations.
- **remember vs rememberSaveable**: `remember` survives recomposition but not configuration changes (rotation, dark mode). Use `rememberSaveable` for UI state that must survive config changes.
- **State hoisting**: Lift state out of composables that don't own it. The owner should be the lowest common ancestor that needs the state. This makes composables reusable and testable.
- **Stable lambdas**: Passing lambdas into composables causes recomposition of the child if the lambda changes. Use `remember` to stabilize lambdas or extract them to module-level functions.
- **SnapshotFlow debouncing**: `snapshotFlow` emits every time the snapshot state changes. Combine with `debounce` or `filter` operators to avoid rapid-fire emissions.

## Related
- kotlin/android/compose-basics.md
- kotlin/coroutines/flow.md
- kotlin/stdlib/coroutines.md
