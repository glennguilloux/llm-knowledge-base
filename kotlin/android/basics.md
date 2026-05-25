---
id: "kotlin-android-basics"
title: "Kotlin Android Basics: Activity, ViewModel, Compose, and Permissions"
language: "kotlin"
category: "stdlib"
tags: ["kotlin", "android", "activity", "viewmodel", "compose", "permissions"]
version: "1.9+"
retrieval_hint: "kotlin android Activity lifecycle ViewModel Compose basics permissions Intents"
last_verified: "2026-05-24"
confidence: "high"
---

# Kotlin Android Basics: Activity, ViewModel, Compose, and Permissions

## When to Use
- Building Android applications with Kotlin
- Understanding the Activity lifecycle and state management
- Using ViewModel to survive configuration changes
- Building UIs with Jetpack Compose
- Handling runtime permissions

## Standard Pattern

```kotlin
// Activity lifecycle
class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // Initialize UI, restore saved state from savedInstanceState
    }

    override fun onStart() {
        super.onStart()
        // Activity becomes visible
    }

    override fun onResume() {
        super.onResume()
        // Activity is in foreground and interactive
    }

    override fun onPause() {
        super.onPause()
        // Activity is partially visible — save lightweight state
    }

    override fun onStop() {
        super.onStop()
        // Activity is no longer visible
    }

    override fun onDestroy() {
        super.onDestroy()
        // Clean up resources
    }
}

// ViewModel — survives configuration changes
class UserViewModel : ViewModel() {
    private val _users = MutableLiveData<List<User>>()
    val users: LiveData<List<List<User>>> = _users

    private val _loading = MutableLiveData<Boolean>()
    val loading: LiveData<Boolean> = _loading

    fun loadUsers() {
        viewModelScope.launch {
            _loading.value = true
            try {
                _users.value = repository.getUsers()
            } catch (e: Exception) {
                // Handle error
            } finally {
                _loading.value = false
            }
        }
    }
}

// Jetpack Compose basics
@Composable
fun UserList(viewModel: UserViewModel = viewModel()) {
    val users by viewModel.users.observeAsState(emptyList())
    val isLoading by viewModel.loading.observeAsState(false)

    if (isLoading) {
        CircularProgressIndicator()
    } else {
        LazyColumn {
            items(users) { user ->
                UserCard(user = user)
            }
        }
    }
}

@Composable
fun UserCard(user: User) {
    var expanded by remember { mutableStateOf(false) }

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(8.dp)
            .clickable { expanded = !expanded }
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(text = user.name, style = MaterialTheme.typography.h6)
            if (expanded) {
                Text(text = user.email)
            }
        }
    }
}

// Requesting permissions
class CameraActivity : AppCompatActivity() {
    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        if (isGranted) openCamera() else showPermissionDenied()
    }

    fun requestCameraPermission() {
        when {
            ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA)
                == PackageManager.PERMISSION_GRANTED -> openCamera()
            shouldShowRequestPermissionRationale(Manifest.permission.CAMERA) ->
                showRationaleDialog()
            else -> requestPermissionLauncher.launch(Manifest.permission.CAMERA)
        }
    }
}
```

## Common Mistakes

```kotlin
// WRONG: Doing heavy work on the main thread
override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    val data = database.loadAllData()  // Blocks UI thread!
    updateUI(data)
}

// CORRECT: Use coroutines for background work
override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    lifecycleScope.launch(Dispatchers.IO) {
        val data = database.loadAllData()
        withContext(Dispatchers.Main) {
            updateUI(data)
        }
    }
}

// WRONG: Not handling configuration changes
class MyActivity : AppCompatActivity() {
    private var userList: List<User>? = null  // Lost on rotation!

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        userList = fetchUsers()  // Re-fetched on every rotation
    }
}

// CORRECT: Use ViewModel to survive configuration changes
class MyViewModel : ViewModel() {
    val users: LiveData<List<User>> = liveData {
        emit(repository.fetchUsers())  // Survives rotation
    }
}

// WRONG: Not using remember in Compose (recomposition resets state)
@Composable
fun Counter() {
    var count = 0  // Reset to 0 on every recomposition!
    Button(onClick = { count++ }) {
        Text("Count: $count")
    }
}

// CORRECT: Use remember to persist state across recompositions
@Composable
fun Counter() {
    var count by remember { mutableStateOf(0) }
    Button(onClick = { count++ }) {
        Text("Count: $count")
    }
}

// WRONG: Leaking Activity context in ViewModel
class MyViewModel(private val activity: Activity) : ViewModel() {
    // Activity reference leaks if ViewModel outlives Activity!
}

// CORRECT: Use Application context via AndroidViewModel
class MyViewModel(application: Application) : AndroidViewModel(application) {
    val appContext: Context = getApplication<Application>().applicationContext
}
```

## Gotchas
- Activity is destroyed and recreated on configuration changes (rotation, locale). Use `ViewModel` + `SavedStateHandle` to survive.
- `LiveData` is lifecycle-aware — it only updates observers that are in `STARTED` or `RESUMED` state.
- Compose `remember` persists state across recompositions but NOT across configuration changes. Use `rememberSaveable` for that.
- `viewModelScope.launch` automatically cancels coroutines when the ViewModel is cleared.
- Runtime permissions (Android 6.0+) must be requested at runtime, not just declared in manifest.
- `Dispatchers.Main` is the UI thread. Never perform blocking operations on it.
- Compose `LazyColumn` is the equivalent of `RecyclerView` — it only renders visible items.

## Related
- kotlin/stdlib/coroutines.md
- kotlin/stdlib/basics.md
- kotlin/stdlib/null-safety.md
