---
id: "java-stdlib-exception-handling"
title: "Java Exception Handling: try-catch, Custom Exception Hierarchy"
language: "java"
category: "stdlib"
tags: ["java", "exception", "try-catch", "throws", "custom-exception", "checked", "unchecked", "finally", "handling"]
version: "17+"
retrieval_hint: "Java exception handling try catch throws custom checked unchecked finally hierarchy exception handling"
last_verified: "2026-05-24"
confidence: "high"
---

# Exception Handling Hierarchy

## When to Use
- Handling recoverable errors (I/O failures, network timeouts, validation)
- Defining custom exception types for domain-specific errors
- Deciding between checked and unchecked exceptions
- Ensuring resource cleanup with try-with-resources

## Standard Pattern

```java
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

// --- Custom exception hierarchy ---
public class AppException extends Exception {
    private final String errorCode;

    public AppException(String message, String errorCode) {
        super(message);
        this.errorCode = errorCode;
    }

    public AppException(String message, String errorCode, Throwable cause) {
        super(message, cause);
        this.errorCode = errorCode;
    }

    public String getErrorCode() { return errorCode; }
}

public class ValidationException extends AppException {
    public ValidationException(String field, String message) {
        super("Validation failed for '%s': %s".formatted(field, message), "VALIDATION_ERROR");
    }
}

public class NotFoundException extends AppException {
    public NotFoundException(String resource, Object id) {
        super("%s with id %s not found".formatted(resource, id), "NOT_FOUND");
    }
}

// --- Checked vs Unchecked ---
// Checked: compiler forces handling (extends Exception)
// Unchecked: runtime errors (extends RuntimeException)

public class UserService {
    // Checked exception — must declare or handle
    public User findById(long id) throws AppException {
        // ...
        throw new NotFoundException("User", id);
    }

    // Unchecked exception — no declaration needed
    public void validateEmail(String email) {
        if (email == null || !email.contains("@")) {
            throw new IllegalArgumentException("Invalid email: " + email);
        }
    }
}

// --- Try-with-resources ---
public String readFile(Path path) throws IOException {
    try (var reader = Files.newBufferedReader(path)) {
        return reader.lines().collect(java.util.stream.Collectors.joining("\n"));
    } // reader.close() called automatically, even on exception
}

// --- Multi-catch and rethrow ---
public void processData(String input) throws AppException {
    try {
        int value = Integer.parseInt(input);
        saveToDatabase(value);
    } catch (NumberFormatException e) {
        throw new ValidationException("input", "must be a number");
    } catch (SQLException e) {
        throw new AppException("Database error", "DB_ERROR", e);
    }
}

// --- Finally for cleanup (prefer try-with-resources) ---
public void legacyProcess() {
    Connection conn = null;
    try {
        conn = getConnection();
        conn.execute("...");
    } finally {
        if (conn != null) {
            try { conn.close(); } catch (SQLException ignored) {}
        }
    }
}
```

## Common Mistakes

```java
// WRONG: Catching Exception or Throwable (swallows everything)
try {
    process(data);
} catch (Exception e) {
    // Catches programming errors (NPE, ClassCast) — hides bugs!
    log.error("Something went wrong", e);
}

// CORRECT: Catch specific exceptions
try {
    process(data);
} catch (IOException e) {
    log.error("I/O error processing data", e);
} catch (ValidationException e) {
    log.warn("Validation failed: {}", e.getMessage());
}

// WRONG: Empty catch block (silent failure)
try {
    riskyOperation();
} catch (Exception e) {
    // Error swallowed — no log, no rethrow
}

// CORRECT: At minimum, log the exception
try {
    riskyOperation();
} catch (Exception e) {
    log.error("Operation failed", e);
    throw new AppException("Operation failed", "OP_ERROR", e);
}

// WRONG: Using exception for control flow
try {
    int index = list.indexOf(item);
    String value = list.get(index);
} catch (IndexOutOfBoundsException e) {
    // Not found — exceptions are expensive for control flow!
}

// CORRECT: Check condition first
if (list.contains(item)) {
    String value = list.get(list.indexOf(item));
}

// WRONG: Not including cause in rethrown exception
catch (IOException e) {
    throw new AppException("Failed", "ERR");  // Lost original cause!
}

// CORRECT: Chain the cause
catch (IOException e) {
    throw new AppException("Failed", "ERR", e);  // Preserves stack trace
}

// WRONG: Declaring checked exceptions that callers can't handle
public User getUser(long id) throws SQLException, IOException, ParseException {
    // Caller can't reasonably handle all of these
}

// CORRECT: Wrap in domain-specific unchecked exception
public User getUser(long id) {
    try {
        return repository.findById(id);
    } catch (SQLException e) {
        throw new DataAccessException("Failed to load user", e);
    }
}
```

## Gotchas
- Checked exceptions force callers to handle errors — good for recoverable conditions, noisy for unrecoverable ones
- Unchecked exceptions (RuntimeException) are for programming errors — don't catch NPE or ClassCast
- `try-with-resources` requires `AutoCloseable` — all I/O classes implement it
- `finally` runs even if `try` or `catch` returns — be careful with return values in finally
- `e.getMessage()` may be null — use `e.getClass().getSimpleName()` for logging
- Exception chaining (`new Exception("msg", cause)`) preserves the original stack trace — always chain
- `Thread.interrupted()` clears the interrupt flag — check it in catch blocks for InterruptedException

## Related
- java/stdlib/collections.md
- java/spring/spring-mvc.md
