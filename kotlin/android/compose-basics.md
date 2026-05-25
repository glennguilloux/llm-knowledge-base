---
id: "kotlin-android-compose-basics"
title: "Jetpack Compose Basics: Composables, State, Modifiers, Layouts"
language: "kotlin"
category: "web"
tags: ["kotlin", "jetpack-compose", "composables", "ui", "modifiers", "layouts"]
version: "1.5+"
retrieval_hint: "kotlin jetpack compose composable function state modifier layout theming material3"
last_verified: "2026-05-24"
confidence: "high"
---

# Jetpack Compose Basics: Composables, State, Modifiers, Layouts

## When to Use
- Building Android UIs with Jetpack Compose
- Creating reusable composable components
- Managing state with `remember` and `mutableStateOf`
- Arranging UI with Row, Column, and Box layouts

## Standard Pattern

```kotlin
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

// --- Basic Composable ---
@Composable
fun Greeting(name: String) {
    Text(text = "Hello, $name!")
}

// --- Composable with State ---
@Composable
fun Counter() {
    var count by remember { mutableStateOf(0) }

    Column(
        modifier = Modifier.padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = "Count: $count",
            fontSize = 24.sp,
            fontWeight = FontWeight.Bold
        )

        Spacer(modifier = Modifier.height(8.dp))

        Button(onClick = { count++ }) {
            Text("Increment")
        }
    }
}

// --- Layouts: Row, Column, Box ---
@Composable
fun ProfileCard(name: String, email: String) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(8.dp),
        shape = RoundedCornerShape(12.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Row(
            modifier = Modifier
                .padding(16.dp)
                .fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Avatar placeholder
            Box(
                modifier = Modifier
                    .size(48.dp)
                    .padding(4.dp),
                contentAlignment = Alignment.Center
            ) {
                Surface(
                    shape = RoundedCornerShape(50),
                    color = MaterialTheme.colorScheme.primary
                ) {
                    Text(
                        text = name.first().toString(),
                        color = MaterialTheme.colorScheme.onPrimary,
                        modifier = Modifier.padding(8.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.width(12.dp))

            Column {
                Text(
                    text = name,
                    fontWeight = FontWeight.SemiBold,
                    fontSize = 16.sp
                )
                Text(
                    text = email,
                    fontSize = 14.sp,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}

// --- Theming with Material3 ---
@Composable
fun AppTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = lightColorScheme(
            primary = androidx.compose.ui.graphics.Color(0xFF1976D2),
            secondary = androidx.compose.ui.graphics.Color(0xFF26A69A),
            background = androidx.compose.ui.graphics.Color(0xFFF5F5F5)
        ),
        typography = Typography(
            headlineLarge = TextStyle(
                fontSize = 28.sp,
                fontWeight = FontWeight.Bold
            ),
            bodyLarge = TextStyle(
                fontSize = 16.sp,
                lineHeight = 24.sp
            )
        ),
        content = content
    )
}

// --- Preview ---
@Preview(showBackground = true, showSystemUi = true)
@Composable
fun ProfileCardPreview() {
    AppTheme {
        ProfileCard(
            name = "Alice Johnson",
            email = "alice@example.com"
        )
    }
}

// --- Advanced: Modifier Chaining ---
@Composable
fun StyledButton(onClick: () -> Unit) {
    Button(
        onClick = onClick,
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp)
            .height(48.dp),
        shape = RoundedCornerShape(8.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = MaterialTheme.colorScheme.primary,
            contentColor = MaterialTheme.colorScheme.onPrimary
        ),
        elevation = ButtonDefaults.buttonElevation(
            defaultElevation = 2.dp,
            pressedElevation = 6.dp
        )
    ) {
        Text("Submit")
    }
}
```

## Common Mistakes

```kotlin
// WRONG: Calling composable from non-composable context
class MyActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)  // No Compose!
    }
}

// CORRECT: Use setContent
class MyActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            AppTheme {
                Greeting("World")
            }
        }
    }
}


// WRONG: Modifier order matters (wrong)
Button(
    onClick = {},
    modifier = Modifier
        .clickable { }  // Click handling should be first
        .padding(16.dp)
        .fillMaxWidth()
)

// CORRECT: Size/clip modifiers first, then padding, then clickable
Button(
    onClick = {},
    modifier = Modifier
        .fillMaxWidth()
        .padding(16.dp)
)


// WRONG: State hoisting failure — state inside composable
@Composable
fun UserProfile(userId: Int) {
    var userData by remember { mutableStateOf<User?>(null) }
    // State is tied to this composition, can't be reused/tested
    LaunchedEffect(userId) { userData = fetchUser(userId) }
}

// CORRECT: Hoist state up
@Composable
fun UserProfile(userData: User?, onRefresh: () -> Unit) {
    // Pure UI, no data loading
}
```

## Gotchas
- **Recomposition scope**: `remember` keeps state across recompositions. Without `remember`, `mutableStateOf` resets every recomposition. Use `rememberSaveable` to survive configuration changes.
- **Modifier order**: The order of modifier chaining matters. `Modifier.fillMaxWidth().padding(16.dp)` is different from `Modifier.padding(16.dp).fillMaxWidth()`. Size modifiers should generally come first.
- **`key` parameter**: In `LazyColumn` or `LazyRow`, provide a stable `key` parameter. Without it, recomposition is inefficient and animations break.
- **Unstable classes**: Compose considers classes unstable if they have mutable properties. Use `data class`, `@Stable`, or immutable properties for better recomposition skipping.
- **Preview parameter defaults**: `@Preview` composables need parameter defaults or wrapper methods. You can't preview a composable that requires non-optional parameters without providing defaults.
- **`MutableState` vs `State`**: Use `MutableState` when the composable needs to update the value. Use `State` (read-only) when the value comes from outside. Prefer `by` delegation over `.value`.

## Related
- kotlin/android/compose-state.md
- kotlin/stdlib/basics.md
- kotlin/stdlib/functions-lambdas.md
