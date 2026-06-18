---
id: "kotlin-web-spring-boot"
title: "Spring Boot with Kotlin: Controllers, Beans, and Coroutines"
language: "kotlin"
category: "web"
tags: ["kotlin", "spring-boot", "controller", "beans", "coroutines", "webflux"]
version: "1.9+"
retrieval_hint: "kotlin Spring Boot application class routing beans extension functions coroutines Spring"
last_verified: "2026-05-24"
confidence: "high"
---

# Spring Boot with Kotlin: Controllers, Beans, and Coroutines

## When to Use
- Building Spring Boot applications with Kotlin
- Leveraging Spring ecosystem (Security, Data, Cloud) with Kotlin idioms
- Using extension functions to enhance Spring APIs
- Integrating coroutines with Spring WebFlux

## Standard Pattern

```kotlin
import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.runApplication
import org.springframework.web.bind.annotation.*
import org.springframework.stereotype.Service
import org.springframework.stereotype.Repository
import org.springframework.data.repository.CrudRepository
import org.springframework.http.HttpStatus
import org.springframework.web.server.ResponseStatusException

@SpringBootApplication
class Application

fun main(args: Array<String>) {
    runApplication<Application>(*args)
}

// Controller with Kotlin idioms
@RestController
@RequestMapping("/api/users")
class UserController(private val userService: UserService) {

    @GetMapping
    fun getAllUsers(): List<UserDto> = userService.findAll()

    @GetMapping("/{id}")
    fun getUser(@PathVariable id: Int): UserDto =
        userService.findById(id)
            ?: throw ResponseStatusException(HttpStatus.NOT_FOUND, "User not found")

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    fun createUser(@RequestBody @Valid request: CreateUserRequest): UserDto =
        userService.create(request)

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    fun deleteUser(@PathVariable id: Int) {
        if (!userService.delete(id)) {
            throw ResponseStatusException(HttpStatus.NOT_FOUND, "User not found")
        }
    }
}

// Service with Kotlin idioms
@Service
class UserService(private val userRepository: UserRepository) {

    fun findAll(): List<UserDto> =
        userRepository.findAll().map { it.toDto() }

    fun findById(id: Int): UserDto? =
        userRepository.findById(id).orElse(null)?.toDto()

    fun create(request: CreateUserRequest): UserDto {
        val user = User(name = request.name, email = request.email)
        return userRepository.save(user).toDto()
    }

    fun delete(id: Int): Boolean {
        if (!userRepository.existsById(id)) return false
        userRepository.deleteById(id)
        return true
    }
}

// Extension function for DTO conversion — Kotlin idiom
fun User.toDto() = UserDto(id = this.id!!, name = this.name, email = this.email)

// Repository
interface UserRepository : CrudRepository<User, Int>

// Entity (using Spring Data)
import javax.persistence.*

@Entity
@Table(name = "users")
class User(
    @Column(nullable = false) var name: String = "",
    @Column(nullable = false) var email: String = "",
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) var id: Int? = null
)

// DTOs
data class UserDto(val id: Int, val name: String, val email: String)
data class CreateUserRequest(val name: String, val email: String)

// Coroutines with Spring WebFlux
@RestController
@RequestMapping("/api/async")
class AsyncController(private val asyncService: AsyncService) {

    @GetMapping("/data")
    suspend fun getData(): DataDto = asyncService.fetchData()

    @GetMapping("/batch")
    suspend fun getBatch(): List<DataDto> = asyncService.fetchBatch()
}

@Service
class AsyncService {
    suspend fun fetchData(): DataDto {
        kotlinx.coroutines.delay(100)  // Non-blocking
        return DataDto("result")
    }

    suspend fun fetchBatch(): List<DataDto> = coroutineScope {
        val deferred1 = async { fetchData() }
        val deferred2 = async { fetchData() }
        listOf(deferred1.await(), deferred2.await())
    }
}

data class DataDto(val value: String)
```

## Common Mistakes

```kotlin
// WRONG: Using var for constructor parameters in Spring beans
@Service
class UserService(userRepository: UserRepository) {
    // userRepository is not a property — can't access it!
    fun findAll() = userRepository.findAll()  // Compile error
}

// CORRECT: Use val to make it a property
@Service
class UserService(private val userRepository: UserRepository) {
    fun findAll() = userRepository.findAll()  // OK
}

// WRONG: Not using data class for DTOs
class UserDto(val id: Int, val name: String, val email: String)
// No equals, hashCode, toString, copy!

// CORRECT: Use data class for DTOs
data class UserDto(val id: Int, val name: String, val email: String)

// WRONG: Using Java-style null checks instead of Kotlin null safety
fun getUser(id: Int): UserDto {
    val user = repository.findById(id)
    if (user == null) {
        throw ResponseStatusException(HttpStatus.NOT_FOUND)
    }
    return user.toDto()
}

// CORRECT: Use Kotlin elvis operator
fun getUser(id: Int): UserDto =
    repository.findById(id)?.toDto()
        ?: throw ResponseStatusException(HttpStatus.NOT_FOUND)

// WRONG: Blocking in coroutine-based controller
@GetMapping("/data")
suspend fun getData(): DataDto {
    return blockingService.fetch()  // Blocks the event loop!
}

// CORRECT: Use suspend functions throughout
@GetMapping("/data")
suspend fun getData(): DataDto {
    return suspendableService.fetch()  // Non-blocking
}

// WRONG: Not using extension functions for cross-cutting concerns
@GetMapping("/users")
fun getUsers(): List<UserDto> {
    logger.info("Fetching users")
    val users = userService.findAll()
    logger.info("Found ${users.size} users")
    return users
}

// CORRECT: Use extension functions or AOP for cross-cutting concerns
inline fun <T>.logExecution(name: String, block: () -> T): T {
    logger.info("Starting: $name")
    val result = block()
    logger.info("Completed: $name")
    return result
}
```

## Gotchas
- Spring Boot 3.x requires Kotlin 1.7+ and Java 17+. Check compatibility.
- `private val` in the primary constructor creates a property AND assigns the parameter. Just `val` without `private` also works but exposes the field.
- Kotlin `data class` is perfect for DTOs — auto-generates `equals()`, `hashCode()`, `toString()`, `copy()`, and `componentN()`.
- Spring Data repositories work seamlessly with Kotlin. Use `CrudRepository` or `JpaRepository`.
- For coroutine support, use Spring WebFlux (not Spring MVC). Controllers can have `suspend` functions.
- `ResponseStatusException` is the idiomatic way to return error responses in Spring.
- Extension functions are a powerful Kotlin idiom for adding utility methods to Spring classes.
- `@ConfigurationProperties` works with `data class` for type-safe configuration.

## Related
- kotlin/stdlib/coroutines.md
- kotlin/stdlib/basics.md
- kotlin/web/ktor.md
- kotlin/stdlib/classes.md
