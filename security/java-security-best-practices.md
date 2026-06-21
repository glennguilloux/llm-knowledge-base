---
id: "security-java-best-practices"
title: "Java Security Best Practices"
language: "java"
category: "security"
tags: ["java", "security", "best-practices", "secure-defaults", "validation", "preparedstatement", "secrets", "logging"]
version: "17+"
retrieval_hint: "Java security best practices secure defaults validation PreparedStatement environment variables logging redaction Spring Security"
last_verified: "2026-06-20"
confidence: "medium"
---

# Java Security Best Practices

## When to Use
- Building Java services with Spring Boot, Jakarta EE, or plain JDBC
- Reviewing Java code for secure defaults, validation, and safe database access
- Hardening configuration before production deployment
- Training Java developers on practical defensive security patterns

## Standard Pattern

```java
// === Java: Secure Defaults and Validation ===
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

record CreateUserRequest(
    @Email @NotBlank String email,
    @Size(min = 1, max = 80) String displayName,
    @Min(0) @Max(130) int age
) {}

final class SecurityDefaults {
    static final boolean DEBUG = Boolean.parseBoolean(System.getenv("DEBUG"));
    static final boolean HSTS_ENABLED = true;
    static final boolean COOKIE_HTTP_ONLY = true;
    static final boolean COOKIE_SECURE = true;
}
```

```java
// === Java: PreparedStatement for User Input ===
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.util.Optional;

public Optional<User> findByEmail(Connection conn, String email) throws SQLException {
    String sql = "SELECT id, email, display_name FROM users WHERE email = ? AND active = ?";
    try (PreparedStatement stmt = conn.prepareStatement(sql)) {
        stmt.setString(1, email);
        stmt.setBoolean(2, true);
        try (ResultSet rs = stmt.executeQuery()) {
            if (rs.next()) {
                return Optional.of(new User(
                    rs.getLong("id"),
                    rs.getString("email"),
                    rs.getString("display_name")
                ));
            }
        }
    }
    return Optional.empty();
}
```

```java
// === Java: Safe Identifier Allowlist ===
import java.util.Set;

Set<String> ALLOWED_SORT_COLUMNS = Set.of("created_at", "email", "display_name");

String chooseSortColumn(String requested) {
    return ALLOWED_SORT_COLUMNS.contains(requested) ? requested : "created_at";
}

String buildListQuery(String requestedSort) {
    String column = chooseSortColumn(requestedSort);
    return "SELECT id, email, display_name FROM users ORDER BY " + column + " LIMIT 100";
}
```

```java
// === Java: Redact Sensitive Log Fields ===
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

Logger log = LoggerFactory.getLogger(AuthController.class);

void logLogin(String email, String clientIp, boolean success) {
    log.info("login email={} ip={} success={}", email, clientIp, success);
}
```

## Common Mistakes

```java
// WRONG: Hardcoded secret in source
String apiKey = "example-secret";

// CORRECT: Read required secrets from environment
String apiKey = System.getenv("API_KEY");
```

```java
// WRONG: String concatenation in SQL
String sql = "SELECT * FROM users WHERE email = '" + email + "'";

// CORRECT: PreparedStatement with bind parameters
PreparedStatement stmt = conn.prepareStatement("SELECT * FROM users WHERE email = ?");
stmt.setString(1, email);
```

```java
// WRONG: Logging sensitive request values
log.info("request token={} credential={}", authorizationHeader, rawCredential);

// CORRECT: Log safe context only
log.info("request ip={} path={} status={}", clientIp, path, status);
```

```java
// WRONG: Trusting request parameters for SQL identifiers
String sort = request.getParameter("sort");
String sql = "SELECT * FROM users ORDER BY " + sort;

// CORRECT: Use an allowlist before composing identifiers
String sort = request.getParameter("sort");
String column = ALLOWED_SORT_COLUMNS.contains(sort) ? sort : "created_at";
```

## Gotchas
- `PreparedStatement` protects values, but dynamic table and column names still require allowlisting
- `System.getenv()` should be checked during startup so missing secrets fail before serving traffic
- Bean Validation annotations need to be enforced by the framework or service boundary
- `Logger` calls should avoid exceptions that include credentials, tokens, or session identifiers
- Spring Boot debug endpoints and detailed error pages should be disabled in production profiles
- `Optional.empty()` is safe for missing records, but authorization checks must still happen after lookup

## Related
- security/owasp-top-10.md
- security/web-security-basics.md
- security/authentication-best-practices.md
- security/sql-injection-prevention.md
