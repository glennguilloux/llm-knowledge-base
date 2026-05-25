---
id: "kotlin-testing-mocking"
title: "MockK: Mocking, Verification, and Coroutine Testing"
language: "kotlin"
category: "testing"
tags: ["kotlin", "mocking", "mockk", "testing", "coroutines", "verification"]
version: "1.13+"
retrieval_hint: "kotlin mockk mocking verification relaxed mock coroutine testing"
last_verified: "2026-05-24"
confidence: "high"
---

# MockK: Mocking, Verification, and Coroutine Testing

## When to Use
- Unit testing Kotlin classes with dependencies
- Mocking interfaces and classes for isolated tests
- Verifying interactions with mocked dependencies
- Testing coroutine-based code with mockk

## Standard Pattern

```kotlin
import io.mockk.*
import kotlinx.coroutines.test.runTest
import kotlin.test.Test
import kotlin.test.assertEquals

// --- Service Under Test ---
interface UserRepository {
    suspend fun getUser(id: Int): User
    fun save(user: User): Boolean
    fun getUsersByRole(role: String): List<User>
}

data class User(val id: Int, val name: String, val role: String)

class UserService(private val repository: UserRepository) {
    suspend fun getUserDisplayName(id: Int): String {
        val user = repository.getUser(id)
        return "${user.name} (${user.role})"
    }

    fun promoteToAdmin(id: Int): Boolean {
        val users = repository.getUsersByRole("admin")
        if (users.any { it.id == id }) return true  // Already admin
        return repository.save(User(id, "", "admin"))
    }
}

// --- Basic MockK Tests ---
class UserServiceTest {

    private val repository = mockk<UserRepository>()
    private val service = UserService(repository)

    @Test
    fun `get user display name`() = runTest {
        // Given
        val user = User(1, "Alice", "user")
        coEvery { repository.getUser(1) } returns user

        // When
        val result = service.getUserDisplayName(1)

        // Then
        assertEquals("Alice (user)", result)
        coVerify { repository.getUser(1) }
    }

    @Test
    fun `promote user to admin`() {
        // Given
        every { repository.getUsersByRole("admin") } returns listOf(
            User(2, "Bob", "admin")
        )
        every { repository.save(any()) } returns true

        // When
        val result = service.promoteToAdmin(1)

        // Then
        assertEquals(true, result)
        verify { repository.getUsersByRole("admin") }
        verify { repository.save(any()) }
    }

    @Test
    fun `already admin does not save again`() {
        // Given
        every { repository.getUsersByRole("admin") } returns listOf(
            User(1, "Alice", "admin")  // Already includes user 1
        )

        // When
        val result = service.promoteToAdmin(1)

        // Then
        assertEquals(true, result)
        verify(exactly = 0) { repository.save(any()) }  // Never called
    }

    @Test
    fun `relaxed mock for unused methods`() {
        // Relaxed mock: returns default values for unstubbed methods
        val relaxedRepo = mockk<UserRepository>(relaxed = true)
        val service = UserService(relaxedRepo)

        // No need to stub getUsersByRole — relaxed returns empty list
        val result = service.promoteToAdmin(1)
        assertEquals(true, result)  // save returns true (default for Boolean)
    }
}

// --- Advanced MockK Features ---
class AdvancedMockKTest {

    @Test
    fun `argument capture`() {
        val repo = mockk<UserRepository>(relaxUnitFun = true)
        val slot = slot<User>()

        every { repo.save(capture(slot)) } returns true

        repo.save(User(1, "Alice", "user"))

        assertEquals(1, slot.captured.id)
        assertEquals("Alice", slot.captured.name)
    }

    @Test
    fun `verify order`() {
        val repo = mockk<UserRepository>(relaxed = true)

        repo.getUsersByRole("admin")
        repo.getUsersByRole("user")

        verifyOrder {
            repo.getUsersByRole("admin")
            repo.getUsersByRole("user")
        }
    }

    @Test
    fun `verify with timeouts`() {
        val repo = mockk<UserRepository>(relaxed = true)

        repo.getUsersByRole("admin")

        verify(timeout = 1000) {
            repo.getUsersByRole("admin")
        }
    }

    @Test
    fun `answer with lambda`() {
        val repo = mockk<UserRepository>()

        every { repo.getUsersByRole(any()) } answers {
            when (firstArg<String>()) {
                "admin" -> listOf(User(1, "Admin", "admin"))
                else -> emptyList()
            }
        }

        assertEquals(1, repo.getUsersByRole("admin").size)
        assertEquals(0, repo.getUsersByRole("user").size)
    }
}

// --- MockkStatic and MockkObject ---
@Test
fun `mock static utility`() {
    mockkStatic(String::class)
    every { any<String>().uppercase() } returns "MOCKED"

    assertEquals("MOCKED", "hello".uppercase())

    unmockkStatic(String::class)
}

@Test
fun `mock singleton object`() {
    object Analytics {
        fun track(event: String) { /* firebase */ }
    }

    mockkObject(Analytics)
    every { Analytics.track(any()) } just runs

    Analytics.track("login")
    verify { Analytics.track("login") }

    unmockkObject(Analytics)
}
```

## Common Mistakes

```kotlin
// WRONG: Using strict mock when relaxed needed (unexpected call fails)
val repo = mockk<UserRepository>()  // Strict by default
// service.promoteToAdmin calls getUsersByRole — not stubbed, throws exception!

// CORRECT: Use relaxed mock when you don't care about all calls
val repo = mockk<UserRepository>(relaxed = true)


// WRONG: Forgetting coEvery for suspend functions
every { repository.getUser(1) } returns user  // Fails! getUser is suspend
coEvery { repository.getUser(1) } returns user  // Correct for suspend

// Also: coVerify for verification of suspend functions
coVerify { repository.getUser(1) }


// WRONG: Verify with wrong order (default order is unspecified)
verify { repo.getUsersByRole("user") }
verify { repo.getUsersByRole("admin") }
// Even if admin was called first, this passes

// CORRECT: Use verifyOrder
verifyOrder {
    repo.getUsersByRole("admin")
    repo.getUsersByRole("user")
}


// WRONG: Not cleaning up mockkObject between tests
mockkObject(MySingleton)
// Test runs...
// Next test doesn't set up — leaks between tests

// CORRECT: Unmock after each test
@Test
fun myTest() {
    mockkObject(MySingleton)
    // ...
    unmockkObject(MySingleton)
}

// Or in @AfterTest: unmockkAll()
```

## Gotchas
- **`mockkObject` vs `mockkClass`**: `mockkObject` mocks a singleton (Kotlin `object`). `mockkClass` creates a mock of a regular class. Use `mockkObject` for objects, `mockk` for classes/interfaces.
- **Coroutine scope mocking**: When testing classes that use `viewModelScope` or custom scopes, mock the scope's behavior or use `runTest` from `kotlinx-coroutines-test`.
- **`unmockkAll()`**: Call `unmockkAll()` in `@AfterTest` or `@AfterClass` to reset all mocks. Failure to unmock can cause weird failures in subsequent tests.
- **Relaxed vs strict**: Relaxed mocks return default values (0, false, null, empty list). Strict mocks throw on unstubbed calls. Use strict for critical behavior, relaxed for convenience.
- **`slot` vs `capture`**: Use `slot<T>` for single capture, `mutableListOf<T>()` with `capture` for multiple captures. Always check `slot.isCaptured` before accessing `slot.captured`.
- **`coEvery` on non-suspend**: `coEvery` works for both suspend and non-suspend functions, but `every` doesn't work for suspend. Use `coEvery` consistently if you're unsure.
- **`answers` vs `returns`**: `returns` returns a fixed value. `answers { }` computes a value based on the call arguments. Use `answers` for dynamic responses.

## Related
- kotlin/testing/junit-kotlin.md
- kotlin/coroutines/flow.md
