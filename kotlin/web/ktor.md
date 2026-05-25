---
id: "kotlin-web-ktor"
title: "Ktor Server: Routing, Content Negotiation, and Authentication"
language: "kotlin"
category: "web"
tags: ["kotlin", "ktor", "server", "routing", "content-negotiation", "authentication"]
version: "1.9+"
retrieval_hint: "kotlin Ktor server setup routing content negotiation authentication middleware testing"
last_verified: "2026-05-24"
confidence: "high"
---

# Ktor Server: Routing, Content Negotiation, and Authentication

## When to Use
- Building HTTP servers and REST APIs with Kotlin
- Creating lightweight microservices
- When you want a Kotlin-native web framework (not Spring Boot)
- Building server-side applications with coroutines support

## Standard Pattern

```kotlin
import io.ktor.server.application.*
import io.ktor.server.engine.*
import io.ktor.server.netty.*
import io.ktor.server.routing.*
import io.ktor.server.request.*
import io.ktor.server.response.*
import io.ktor.server.plugins.contentnegotiation.*
import io.ktor.serialization.kotlinx.json.*
import io.ktor.server.auth.*
import io.ktor.server.plugins.statuspages.*
import io.ktor.http.*
import kotlinx.serialization.Serializable

fun main() {
    embeddedServer(Netty, port = 8080) {
        install(ContentNegotiation) {
            json(Json {
                prettyPrint = true
                ignoreUnknownKeys = true
            })
        }
        install(StatusPages) {
            exception<IllegalArgumentException> { call, cause ->
                call.respond(HttpStatusCode.BadRequest, mapOf("error" to cause.message))
            }
            exception<NotFoundException> { call, cause ->
                call.respond(HttpStatusCode.NotFound, mapOf("error" to cause.message))
            }
        }
        install(Authentication) {
            basic("auth-basic") {
                realm = "Ktor Server"
                validate { credentials ->
                    if (credentials.name == "admin" && credentials.password == "password") {
                        UserIdPrincipal(credentials.name)
                    } else null
                }
            }
        }
        routing {
            get("/") {
                call.respond(mapOf("message" to "Hello, Ktor!"))
            }

            get("/users/{id}") {
                val id = call.parameters["id"]?.toIntOrNull()
                    ?: throw IllegalArgumentException("Invalid ID")
                val user = userService.findById(id)
                    ?: throw NotFoundException("User not found")
                call.respond(user)
            }

            post("/users") {
                val request = call.receive<CreateUserRequest>()
                val user = userService.create(request)
                call.respond(HttpStatusCode.Created, user)
            }

            authenticate("auth-basic") {
                delete("/users/{id}") {
                    val id = call.parameters["id"]?.toIntOrNull()
                        ?: throw IllegalArgumentException("Invalid ID")
                    userService.delete(id)
                    call.respond(HttpStatusCode.NoContent)
                }
            }
        }
    }.start(wait = true)
}

@Serializable
data class User(val id: Int, val name: String, val email: String)

@Serializable
data class CreateUserRequest(val name: String, val email: String)

class UserService {
    private val users = mutableMapOf<Int, User>()
    private var nextId = 1

    fun findById(id: Int): User? = users[id]
    fun create(request: CreateUserRequest): User {
        val user = User(nextId++, request.name, request.email)
        users[user.id] = user
        return user
    }
    fun delete(id: Int) { users.remove(id) }
}

class NotFoundException(message: String) : RuntimeException(message)
```

## Common Mistakes

```kotlin
// WRONG: Not installing ContentNegotiation before using receive/respond with JSON
fun Application.module() {
    routing {
        post("/users") {
            val request = call.receive<CreateUserRequest>()  // Fails without ContentNegotiation!
            call.respond(request)
        }
    }
}

// CORRECT: Install ContentNegotiation first
fun Application.module() {
    install(ContentNegotiation) { json() }
    routing {
        post("/users") {
            val request = call.receive<CreateUserRequest>()  // Works!
            call.respond(request)
        }
    }
}

// WRONG: Not handling path parameter parsing safely
get("/users/{id}") {
    val id = call.parameters["id"]!!.toInt()  // Crashes if missing or not a number!
}

// CORRECT: Safe parameter parsing
get("/users/{id}") {
    val id = call.parameters["id"]?.toIntOrNull()
        ?: throw IllegalArgumentException("Invalid ID")
}

// WRONG: Not setting HTTP status codes for errors
delete("/users/{id}") {
    userService.delete(id)
    // Returns 200 OK even if user didn't exist
}

// CORRECT: Return appropriate status codes
delete("/users/{id}") {
    val deleted = userService.delete(id)
    if (deleted) call.respond(HttpStatusCode.NoContent)
    else throw NotFoundException("User not found")
}

// WRONG: Blocking the thread in a route handler
get("/data") {
    val result = blockingDatabaseCall()  // Blocks the Netty event loop!
    call.respond(result)
}

// CORRECT: Use suspend functions or withContext
get("/data") {
    val result = withContext(Dispatchers.IO) {
        databaseCall()  // Runs on IO thread pool
    }
    call.respond(result)
}
```

## Gotchas
- Ktor route handlers are `suspend` functions — you can call other suspend functions directly.
- `ContentNegotiation` must be installed before using `call.receive<T>()` or `call.respond(object)` with JSON.
- Path parameters are always `String?`. Parse them safely with `toIntOrNull()`, `toLongOrNull()`, etc.
- `StatusPages` plugin handles exceptions globally — no need for try/catch in every route.
- Ktor uses Netty by default. The event loop is single-threaded per core — never block it.
- `authenticate { }` blocks protect routes. Unauthenticated requests get 401 automatically.
- `call.receive<T>()` reads the request body. The body can only be read once.
- Use `call.respondText()` for plain text, `call.respond()` for objects (serialized via ContentNegotiation).

## Related
- kotlin/stdlib/coroutines.md
- kotlin/stdlib/serialization.md
- kotlin/stdlib/error-handling.md
- kotlin/web/spring-boot-kotlin.md
