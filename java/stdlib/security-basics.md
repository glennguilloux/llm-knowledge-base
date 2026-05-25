---
id: "java-stdlib-security-basics"
title: "Java Security Basics: SQL Injection, Password Hashing, Secure Random, Bean Validation, TLS"
language: "java"
category: "stdlib"
tags: ["security", "sql-injection", "bcrypt", "secure-random", "bean-validation", "tls", "input-validation"]
version: "17+"
retrieval_hint: "Java security SQL injection PreparedStatement BCrypt SecureRandom Bean Validation TLS"
last_verified: "2026-05-24"
confidence: "high"
---

# Java Security Basics

## When to Use
- Building web services that accept user input
- Storing passwords or sensitive credentials
- Connecting to databases with dynamic queries
- Generating secure random tokens (session IDs, CSRF tokens)
- Validating request payloads in Spring Boot or Jakarta EE applications
- Configuring HTTPS on embedded servers

## Standard Pattern

```java
import javax.net.ssl.KeyManagerFactory;
import javax.net.ssl.SSLContext;
import javax.net.ssl.TrustManagerFactory;
import java.io.FileInputStream;
import java.security.KeyStore;
import java.security.SecureRandom;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.Base64;
import java.util.regex.Pattern;

import org.mindrot.jbcrypt.BCrypt;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

// --- Input Validation ---

public class InputValidator {
    private static final Logger log = LoggerFactory.getLogger(InputValidator.class);
    private static final Pattern EMAIL_PATTERN =
        Pattern.compile("^[a-zA-Z0-9._%+\\-]+@[a-zA-Z0-9.\\-]+\\.[a-zA-Z]{2,}$");
    private static final Pattern USERNAME_PATTERN = Pattern.compile("^[a-zA-Z0-9_]{3,32}$");

    public static String validateEmail(String email) {
        if (email == null || email.isBlank()) {
            throw new ValidationException("email", "cannot be empty");
        }
        email = email.trim().toLowerCase();
        if (email.length() > 254) {
            throw new ValidationException("email", "exceeds maximum length of 254");
        }
        if (!EMAIL_PATTERN.matcher(email).matches()) {
            throw new ValidationException("email", "invalid format");
        }
        return email;
    }

    public static String validateUsername(String username) {
        if (username == null || username.isBlank()) {
            throw new ValidationException("username", "cannot be empty");
        }
        username = username.trim();
        if (!USERNAME_PATTERN.matcher(username).matches()) {
            throw new ValidationException("username", "must be 3-32 alphanumeric characters or underscore");
        }
        return username;
    }

    public static String validatePassword(String password) {
        if (password == null || password.length() < 8) {
            throw new ValidationException("password", "must be at least 8 characters");
        }
        if (password.length() > 128) {
            throw new ValidationException("password", "exceeds maximum length of 128");
        }
        return password;
    }
}

class ValidationException extends RuntimeException {
    private final String field;

    ValidationException(String field, String message) {
        super(field + ": " + message);
        this.field = field;
    }

    public String getField() { return field; }
}

// --- SQL Injection Prevention with PreparedStatement ---

public class UserRepository {
    private static final Logger log = LoggerFactory.getLogger(UserRepository.class);
    private final Connection conn;

    public UserRepository(Connection conn) {
        this.conn = conn;
    }

    // ALWAYS use PreparedStatement — never string concatenation
    public User findByEmail(String email) throws SQLException {
        String sql = "SELECT id, email, username FROM users WHERE email = ?";
        try (PreparedStatement stmt = conn.prepareStatement(sql)) {
            stmt.setString(1, email);  // Parameterized — safe from SQL injection
            try (ResultSet rs = stmt.executeQuery()) {
                if (rs.next()) {
                    return new User(
                        rs.getLong("id"),
                        rs.getString("email"),
                        rs.getString("username")
                    );
                }
                return null;
            }
        }
    }

    public long createUser(String email, String username) throws SQLException {
        String sql = "INSERT INTO users (email, username) VALUES (?, ?)";
        try (PreparedStatement stmt = conn.prepareStatement(sql, PreparedStatement.RETURN_GENERATED_KEYS)) {
            stmt.setString(1, email);
            stmt.setString(2, username);
            stmt.executeUpdate();
            try (ResultSet keys = stmt.getGeneratedKeys()) {
                if (keys.next()) {
                    return keys.getLong(1);
                }
                throw new SQLException("No generated key returned");
            }
        }
    }

    // For dynamic sorting — use a whitelist, never user input directly
    private static final Set<String> ALLOWED_SORT_COLUMNS = Set.of("id", "email", "username", "created_at");

    public List<User> findAll(String sortColumn, String direction) throws SQLException {
        if (!ALLOWED_SORT_COLUMNS.contains(sortColumn)) {
            throw new ValidationException("sortColumn", "invalid sort column: " + sortColumn);
        }
        if (!direction.equalsIgnoreCase("ASC") && !direction.equalsIgnoreCase("DESC")) {
            throw new ValidationException("direction", "must be ASC or DESC");
        }
        // Safe: sortColumn and direction are validated against whitelists
        String sql = "SELECT id, email, username FROM users ORDER BY " + sortColumn + " " + direction;
        try (PreparedStatement stmt = conn.prepareStatement(sql);
             ResultSet rs = stmt.executeQuery()) {
            List<User> users = new ArrayList<>();
            while (rs.next()) {
                users.add(new User(rs.getLong("id"), rs.getString("email"), rs.getString("username")));
            }
            return users;
        }
    }
}

record User(long id, String email, String username) {}

// --- Password Hashing with BCrypt ---

public class PasswordService {
    // workFactor 12 is a good default (takes ~250ms on modern hardware)
    private static final int WORK_FACTOR = 12;

    public String hashPassword(String plainPassword) {
        return BCrypt.hashpw(plainPassword, BCrypt.gensalt(WORK_FACTOR));
    }

    public boolean verifyPassword(String plainPassword, String hashedPassword) {
        return BCrypt.checkpw(plainPassword, hashedPassword);
    }
}

// --- Secure Random Generation ---

public class TokenService {
    private static final SecureRandom secureRandom = new SecureRandom();
    private static final Base64.Encoder encoder = Base64.getUrlEncoder().withoutPadding();

    public String generateSessionToken() {
        byte[] bytes = new byte[32];
        secureRandom.nextBytes(bytes);
        return encoder.encodeToString(bytes);
    }

    public String generateCsrfToken() {
        byte[] bytes = new byte[16];
        secureRandom.nextBytes(bytes);
        return encoder.encodeToString(bytes);
    }

    public String generateApiKey() {
        byte[] bytes = new byte[24];
        secureRandom.nextBytes(bytes);
        return "sk_" + encoder.encodeToString(bytes);
    }
}

// --- TLS Configuration ---

public class TlsConfig {
    public static SSLContext createSSLContext(
            String keyStorePath, String keyStorePassword,
            String trustStorePath, String trustStorePassword) throws Exception {

        // Load keystore
        KeyStore keyStore = KeyStore.getInstance("PKCS12");
        try (FileInputStream fis = new FileInputStream(keyStorePath)) {
            keyStore.load(fis, keyStorePassword.toCharArray());
        }

        KeyManagerFactory kmf = KeyManagerFactory.getInstance(KeyManagerFactory.getDefaultAlgorithm());
        kmf.init(keyStore, keyStorePassword.toCharArray());

        // Load truststore
        KeyStore trustStore = KeyStore.getInstance("PKCS12");
        try (FileInputStream fis = new FileInputStream(trustStorePath)) {
            trustStore.load(fis, trustStorePassword.toCharArray());
        }

        TrustManagerFactory tmf = TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm());
        tmf.init(trustStore);

        // Create SSL context with TLS 1.2+
        SSLContext sslContext = SSLContext.getInstance("TLSv1.2");
        sslContext.init(kmf.getKeyManagers(), tmf.getTrustManagers(), new SecureRandom());

        return sslContext;
    }
}

// --- Bean Validation (Jakarta Validation API) ---

/*
// Add to pom.xml:
// <dependency>
//   <groupId>org.springframework.boot</groupId>
//   <artifactId>spring-boot-starter-validation</artifactId>
// </dependency>
*/

/*
import jakarta.validation.constraints.*;

public class CreateUserRequest {
    @NotBlank(message = "Email is required")
    @Email(message = "Invalid email format")
    @Size(max = 254, message = "Email must not exceed 254 characters")
    private String email;

    @NotBlank(message = "Username is required")
    @Size(min = 3, max = 32, message = "Username must be 3-32 characters")
    @Pattern(regexp = "^[a-zA-Z0-9_]+$", message = "Only alphanumeric and underscore")
    private String username;

    @NotBlank(message = "Password is required")
    @Size(min = 8, max = 128, message = "Password must be 8-128 characters")
    private String password;

    // Getters and setters...
}

// In Spring Boot controller:
@PostMapping("/users")
public ResponseEntity<?> createUser(@Valid @RequestBody CreateUserRequest request) {
    // Validation happens automatically before this method is called
    // Returns 400 with error details if validation fails
    userService.create(request);
    return ResponseEntity.status(201).build();
}
*/
```

## Common Mistakes

```java
// WRONG: String concatenation in SQL queries
String sql = "SELECT * FROM users WHERE email = '" + email + "'";
Statement stmt = conn.createStatement();
ResultSet rs = stmt.executeQuery(sql);
// Attacker: email = "' OR '1'='1' --" → returns all users

// CORRECT: Use PreparedStatement with parameterized queries
String sql = "SELECT * FROM users WHERE email = ?";
PreparedStatement stmt = conn.prepareStatement(sql);
stmt.setString(1, email);
ResultSet rs = stmt.executeQuery();

// WRONG: Storing passwords with fast hashes (SHA-256, MD5)
MessageDigest md = MessageDigest.getInstance("SHA-256");
byte[] hash = md.digest(password.getBytes());
// SHA-256 is designed to be fast — bad for password storage

// CORRECT: Use BCrypt (adaptive, slow by design)
String hash = BCrypt.hashpw(password, BCrypt.gensalt(12));

// WRONG: Using java.util.Random for security tokens
Random random = new Random();
int token = random.nextInt();
// java.util.Random is predictable — attacker can guess future tokens

// CORRECT: Use SecureRandom
SecureRandom secureRandom = new SecureRandom();
byte[] bytes = new byte[32];
secureRandom.nextBytes(bytes);

// WRONG: Using blacklist for input validation
if (!input.contains("<script>")) {
    // "safe" — easily bypassed with <Script>, <scr<script>ipt>, etc.
}

// CORRECT: Use whitelist validation
if (!EMAIL_PATTERN.matcher(input).matches()) {
    throw new ValidationException("email", "invalid format");
}

// WRONG: Not using try-with-resources for PreparedStatement
PreparedStatement stmt = conn.prepareStatement(sql);
stmt.setString(1, email);
ResultSet rs = stmt.executeQuery();
// If an exception occurs, statement and result set are leaked

// CORRECT: Use try-with-resources
try (PreparedStatement stmt = conn.prepareStatement(sql)) {
    stmt.setString(1, email);
    try (ResultSet rs = stmt.executeQuery()) {
        // Process results
    }
}

// WRONG: Dynamic ORDER BY with user input
String sql = "SELECT * FROM users ORDER BY " + request.getSortColumn();
// Attacker can inject arbitrary SQL through sortColumn

// CORRECT: Validate against whitelist
if (!ALLOWED_SORT_COLUMNS.contains(sortColumn)) {
    throw new ValidationException("sortColumn", "invalid");
}
String sql = "SELECT * FROM users ORDER BY " + sortColumn;
```

## Gotchas
- `PreparedStatement` prevents injection for VALUES and WHERE clauses, but NOT for table/column names or ORDER BY — use whitelists for those
- BCrypt truncates passwords at 72 bytes — pre-hash with SHA-256 if you need longer passwords
- `SecureRandom` may block on Linux if entropy pool is exhausted — use `SecureRandom.getInstanceStrong()` for key generation, but `new SecureRandom()` for session tokens
- Bean Validation (`@Valid`) returns 400 automatically in Spring Boot — don't manually validate in the controller
- TLS 1.0 and 1.1 are deprecated — always use TLS 1.2 minimum (`SSLContext.getInstance("TLSv1.2")`)
- `BCrypt.gensalt()` without a parameter uses work factor 10 — use 12+ for production
- Input validation should happen at the controller/handler boundary, not in the service layer
- `SecureRandom` is thread-safe — you can share a single instance across all threads
- Jakarta Validation annotations work on records, classes, and method parameters — use `@Valid` to trigger cascading validation

## Related
- java/stdlib/logging.md
- java/stdlib/exception-handling.md
- patterns/input-validation.md
- patterns/rate-limiting.md
