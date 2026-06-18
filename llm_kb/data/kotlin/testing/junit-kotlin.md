---
id: "kotlin-testing-junit"
title: "Kotlin Testing: JUnit 5, MockK, and Coroutine Testing"
language: "kotlin"
category: "testing"
tags: ["kotlin", "testing", "junit5", "mockk", "kotest", "coroutines"]
version: "1.9+"
retrieval_hint: "kotlin JUnit 5 testing mockk kotest assertions testing coroutines sealed classes"
last_verified: "2026-05-24"
confidence: "high"
---

# Kotlin Testing: JUnit 5, MockK, and Coroutine Testing

## When to Use
- Writing unit tests for Kotlin code
- Mocking dependencies with MockK (Kotlin-native mocking)
- Testing coroutines and suspend functions
- Using Kotest for more expressive assertions
- Testing sealed class hierarchies

## Standard Pattern

```kotlin
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.BeforeEach
import io.mockk.*
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.advanceUntilIdle

// Basic JUnit 5 test
class UserServiceTest {

    private lateinit var userRepository: UserRepository
    private lateinit var userService: UserService

    @BeforeEach
    fun setup() {
        userRepository = mockk()
        userService = UserService(userRepository)
    }

    @Test
    fun `findById returns user when exists`() {
        // Given
        val user = User(1, "Alice", "alice@example.com")
        every { userRepository.findById(1) } returns user

        // When
        val result = userService.findById(1)

        // Then
        assertNotNull(result)
        assertEquals("Alice", result?.name)
        verify { userRepository.findById(1) }
    }

    @Test
    fun `findById returns null when not found`() {
        every { userRepository.findById(any()) } returns null

        val result = userService.findById(999)

        assertNull(result)
    }

    @Test
    fun `create throws on invalid email`() {
        val request = CreateUserRequest("Alice", "invalid-email")

        val exception = assertThrows(IllegalArgumentException::class.java) {
            userService.create(request)
        }

        assertEquals("Invalid email", exception.message)
    }

    @Test
    fun `delete returns false when user not found`() {
        every { userRepository.existsById(any()) } returns false

        val result = userService.delete(999)

        assertFalse(result)
        verify(exactly = 0) { userRepository.deleteById(any()) }
    }
}

// MockK patterns
class MockKExamplesTest {

    @Test
    fun `mockk basic usage`() {
        val repository = mockk<UserRepository>()

        // Stub
        every { repository.findById(1) } returns User(1, "Alice", "a@b.com")
        every { repository.findById(any()) } returns null

        // Call
        val user = repository.findById(1)

        // Verify
        verify { repository.findById(1) }
        confirmVerified(repository)
    }

    @Test
    fun `mockk relaxed — returns default values for unstubbed methods`() {
        val repository = mockk<UserRepository>(relaxed = true)
        // Unstubbed methods return default values (null, 0, false, emptyList)
        val users = repository.findAll()  // Returns emptyList()
        assertTrue(users.isEmpty())
    }

    @Test
    fun `mockk captures arguments`() {
        val repository = mockk<UserRepository>()
        val slot = slot<User>()

        every { repository.save(capture(slot)) } answers { slot.captured }

        repository.save(User(1, "Alice", "a@b.com"))

        assertEquals("Alice", slot.captured.name)
    }

    @Test
    fun `mockk throws exception`() {
        val repository = mockk<UserRepository>()
        every { repository.findById(any()) } throws RuntimeException("DB error")

        assertThrows(RuntimeException::class.java) {
            repository.findById(1)
        }
    }
}

// Testing coroutines
class CoroutineTest {

    @Test
    fun `test suspend function with runTest`() = runTest {
        val service = AsyncService()
        val result = service.fetchData()
        assertEquals("expected", result)
    }

    @Test
    fun `test concurrent coroutines`() = runTest {
        val service = AsyncService()

        val results = listOf(
            async { service.fetchData() },
            async { service.fetchData() }
        ).awaitAll()

        assertEquals(2, results.size)
    }
}

// Kotest assertions (alternative to JUnit assertions)
class KotestStyleTest {
    @Test
    fun `kotest style assertions`() {
        val user = User(1, "Alice", "alice@example.com")

        user.name shouldBe "Alice"
        user.email shouldContain "@"
        user.id shouldBeGreaterThan 0

        val users = listOf(user)
        users.shouldNotBeEmpty()
        users.shouldHaveSize(1)
    }

    @Test
    fun `kotest exception testing`() {
        shouldThrow<IllegalArgumentException> {
            validateEmail("invalid")
        }
    }
}

data class User(val id: Int, val name: String, val email: String)
data class CreateUserRequest(val name: String, val email: String)
class UserService(private val userRepository: UserRepository) {
    fun findById(id: Int): User? = userRepository.findById(id)
    fun create(request: CreateUserRequest): User {
        require(request.email.contains("@")) { "Invalid email" }
        return userRepository.save(User(0, request.name, request.email))
    }
    fun delete(id: Int): Boolean {
        if (!userRepository.existsById(id)) return false
        userRepository.deleteById(id)
        return true
    }
}
interface UserRepository {
    fun findById(id: Int): User?
    fun findAll(): List<User>
    fun save(user: User): User
    fun existsById(id: Int): Boolean
    fun deleteById(id: Int)
}
class AsyncService {
    suspend fun fetchData(): String = "expected"
}
fun validateEmail(email: String) {
    require(email.contains("@")) { "Invalid email" }
}
```

## Common Mistakes

```kotlin
// WRONG: Using Mockito with Kotlin (doesn't handle final classes well)
val repository = Mockito.mock(UserRepository::class.java)
// Mockito can't mock final classes by default — Kotlin classes are final!

// CORRECT: Use MockK — designed for Kotlin
val repository = mockk<UserRepository>()

// WRONG: Not using runTest for coroutines
@Test
fun testCoroutine() {
    val result = service.fetchData()  // Compile error: suspend function outside coroutine
}

// CORRECT: Use runTest
@Test
fun testCoroutine() = runTest {
    val result = service.fetchData()  // OK
}

// WRONG: Not verifying mock calls
every { repository.findById(1) } returns user
service.findById(1)
// No verification — test passes even if findById is never called!

// CORRECT: Verify interactions
verify { repository.findById(1) }

// WRONG: Using JUnit 4 @Test annotation
import org.junit.Test  // JUnit 4!
@Test fun myTest() { }

// CORRECT: Use JUnit 5 @Test
import org.junit.jupiter.api.Test  // JUnit 5
@Test fun myTest() { }

// WRONG: Not using backtick test names (Kotlin convention)
@Test
fun testFindByIdReturnsNullWhenUserDoesNotExist() { }

// CORRECT: Use backtick names for readable test names
@Test
fun `findById returns null when user does not exist` { }
```

## Gotchas
- Kotlin classes are `final` by default. Mockito can't mock them without extra configuration. Use **MockK** instead — it handles final classes natively.
- `runTest` from `kotlinx-coroutines-test` provides a virtual time dispatcher for testing coroutines deterministically.
- MockK's `every { }` is for stubbing, `verify { }` is for verification. `confirmVerified()` ensures no unexpected calls.
- Use backtick test names in Kotlin: `` `should return null when not found` `` — no camelCase needed.
- `relaxed = true` on mockk creates a mock that returns default values for unstubbed methods.
- `slot<T>()` captures arguments for later assertion.
- Kotest provides more expressive assertions (`shouldBe`, `shouldContain`, `shouldThrow`) but requires an additional dependency.
- `@BeforeEach` runs before each test. Use `@BeforeAll` (static) for shared setup.

## Related
- kotlin/stdlib/coroutines.md
- kotlin/stdlib/basics.md
- kotlin/stdlib/error-handling.md
- kotlin/stdlib/classes.md
