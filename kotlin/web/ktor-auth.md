---
id: "kotlin-web-ktor-auth"
title: "Ktor Authentication: Sessions, JWT, OAuth, Route Protection"
language: "kotlin"
category: "web"
tags: ["kotlin", "ktor", "auth", "jwt", "oauth", "sessions"]
version: "2.x+"
retrieval_hint: "kotlin ktor authentication JWT session OAuth route protection"
last_verified: "2026-05-24"
confidence: "high"
---

# Ktor Authentication: Sessions, JWT, OAuth, Route Protection

## When to Use
- Adding authentication to Ktor applications
- Implementing JWT-based stateless authentication
- Managing server-side sessions
- Protecting specific routes with authentication

## Standard Pattern

```kotlin
import io.ktor.server.application.*
import io.ktor.server.auth.*
import io.ktor.server.auth.jwt.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import io.ktor.http.*
import com.auth0.jwk.JwkProvider
import com.auth0.jwk.UrlJwkProvider
import io.ktor.server.sessions.*

// --- Data Classes ---
data class UserSession(val id: String, val name: String)

// --- Configure Authentication ---
// In Application.configureSecurity():
fun Application.configureSecurity() {
    // --- Session Authentication ---
    install(Sessions) {
        cookie<UserSession>("user_session") {
            cookie.path = "/"
            cookie.maxAgeInSeconds = 3600
            cookie.httpOnly = true
            cookie.secure = !isDevelopment()  // HTTPS in production
            transform(SessionTransportTransformerEncrypt("your-secret-key-32-chars-long-for-AES"))
        }
    }

    authentication {
        // Session auth provider
        session<UserSession>("auth-session") {
            validate { session ->
                // Validate session (e.g., check if user still exists)
                if (session.id.isNotEmpty()) session else null
            }
            challenge {
                call.respond(HttpStatusCode.Unauthorized, "Invalid session")
            }
        }

        // --- JWT Authentication ---
        jwt("auth-jwt") {
            verifier(
                JWTVerifier(
                    issuer = "my-app",
                    secret = System.getenv("JWT_SECRET") ?: "dev-secret"
                )
            )
            validate { credential ->
                val userId = credential.payload.getClaim("id").asString()
                if (userId != null) {
                    JWTPrincipal(credential.payload)
                } else {
                    null  // Validation failed
                }
            }
            challenge {
                call.respond(HttpStatusCode.Unauthorized, "Invalid or expired token")
            }
        }

        // --- Basic Auth (for internal tools) ---
        basic("auth-basic") {
            realm = "My App"
            validate { credentials ->
                if (credentials.name == "admin" && credentials.password == "secret") {
                    UserIdPrincipal(credentials.name)
                } else {
                    null
                }
            }
        }
    }
}

// --- Token Generation Utility ---
fun generateToken(userId: String): String {
    val now = Clock.System.now()
    return JWTVerifier(
        issuer = "my-app",
        secret = System.getenv("JWT_SECRET") ?: "dev-secret"
    ).createJWT {
        withClaim("id", userId)
        withExpiresAt(now.plus(1, DateTimeUnit.HOUR).toJavaInstant())
    }
}

// --- Route Protection ---
fun Application.configureRouting() {
    routing {
        // Public route
        post("/login") {
            val login = call.receive<LoginRequest>()
            // Validate credentials...
            val token = generateToken("user-123")
            call.respond(mapOf("token" to token))
        }

        post("/register") {
            // Public registration
            call.respond(HttpStatusCode.Created, "Registered")
        }

        // Protected routes (session)
        authenticate("auth-session") {
            get("/profile") {
                val session = call.principal<UserSession>()
                call.respond(mapOf("user" to session?.name))
            }

            post("/logout") {
                call.sessions.clear<UserSession>()
                call.respond(HttpStatusCode.OK, "Logged out")
            }
        }

        // Protected routes (JWT)
        authenticate("auth-jwt") {
            get("/api/users") {
                val principal = call.principal<JWTPrincipal>()
                val userId = principal?.payload?.getClaim("id")?.asString()
                // Fetch and return users...
                call.respond(mapOf("users" to listOf<String>()))
            }

            get("/api/users/{id}") {
                // ... protected endpoint
            }

            // Admin-only sub-route
            route("/api/admin") {
                // All routes under /api/admin require JWT
                get("/dashboard") {
                    call.respond(mapOf("dashboard" to "admin data"))
                }
            }
        }
    }
}

// --- Login Handler with Session ---
fun Routing.loginWithSession() {
    post("/login-session") {
        val login = call.receive<LoginRequest>()

        // Validate credentials (check DB, hash password, etc.)
        if (login.username == "admin" && login.password == "password") {
            call.sessions.set(UserSession(id = "1", name = "Admin"))
            call.respond(HttpStatusCode.OK, "Logged in")
        } else {
            call.respond(HttpStatusCode.Unauthorized, "Invalid credentials")
        }
    }
}

data class LoginRequest(val username: String, val password: String)
```

## Common Mistakes

```kotlin
// WRONG: Not configuring JWT verifier (token can't be verified)
jwt("auth-jwt") {
    // No verifier configured!
    validate { credential -> JWTPrincipal(credential.payload) }
}
// Tokens won't be validated — any token passes

// CORRECT: Configure verifier
jwt("auth-jwt") {
    verifier(JWTVerifier(issuer = "my-app", secret = secret))
    validate { credential ->
        // Additional validation
    }
}


// WRONG: Missing authenticate on routes (route unprotected)
routing {
    get("/api/secret-data") {  // No authenticate()!
        // Anyone can access this
    }
}

// CORRECT: Protect routes
routing {
    authenticate("auth-jwt") {
        get("/api/secret-data") {
            // Only authenticated users
        }
    }
}


// WRONG: Session cookie not configured for production
Sessions {
    cookie<UserSession>("user_session") {
        cookie.secure = false  // Sent over HTTP in production!
    }
}

// CORRECT: Only secure in production
cookie.secure = System.getenv("ENV") == "production"
```

## Gotchas
- **JWT issuer validation**: Always validate the `issuer` claim to prevent token substitution attacks. An attacker could sign a token with a different issuer that your verifier accepts.
- **OAuth callback state parameter**: When implementing OAuth, always use the `state` parameter to prevent CSRF attacks on the callback endpoint. Ktor's OAuth provider handles this automatically.
- **Session transport**: Sessions can be stored in cookies (stateless but limited to ~4KB) or server-side (stateful, requires storage). Cookie sessions are encrypted by default. Server sessions need session storage configuration.
- **JWT secret management**: Never hardcode JWT secrets. Use environment variables, secrets manager, or config files outside version control. Rotate secrets periodically.
- **Multiple auth providers**: Ktor supports chaining multiple auth providers. The first one that succeeds authenticates the request. Order matters — put more specific providers first.
- **CORS and auth**: If your frontend is on a different origin, configure CORS before authentication. CORS preflight (OPTIONS) requests must not require authentication.
- **Session fixation**: When using session auth, regenerate the session ID after login. Ktor's session plugin handles this automatically when you call `call.sessions.set()`.

## Related
- kotlin/web/ktor.md
- kotlin/web/spring-boot-kotlin.md
- kotlin/stdlib/serialization.md
