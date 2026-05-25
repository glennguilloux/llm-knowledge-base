---
id: "java-spring-mvc-controller-advice"
title: "Global Exception Handling with @ControllerAdvice"
language: "java"
category: "web"
subcategory: "api-framework"
tags: ["spring", "mvc", "exception", "controller-advice", "error", "handler"]
version: "17+"
retrieval_hint: "Spring MVC ControllerAdvice ExceptionHandler global error handling"
last_verified: "2026-05-24"
confidence: "high"
---

# Global Exception Handling with @ControllerAdvice

## When to Use
- Centralizing error handling across all controllers
- Returning consistent error response format (RFC 7807 Problem Details)
- Mapping domain exceptions to HTTP status codes
- Logging errors with context before returning responses

## Standard Pattern

```java
// --- Error response model ---
public record ApiError(
    Instant timestamp,
    int status,
    String error,
    String message,
    String path,
    List<FieldError> fieldErrors
) {
    public record FieldError(String field, String message, Object rejectedValue) {}
}

// --- Global exception handler ---
@RestControllerAdvice
public class GlobalExceptionHandler {
    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    // Handle specific domain exception
    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<ApiError> handleNotFound(ResourceNotFoundException ex, HttpServletRequest request) {
        log.warn("Resource not found: {}", ex.getMessage());
        return buildResponse(404, "Not Found", ex.getMessage(), request.getRequestURI());
    }

    // Handle validation errors (@Valid)
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiError> handleValidation(MethodArgumentNotValidException ex, HttpServletRequest request) {
        List<ApiError.FieldError> fieldErrors = ex.getBindingResult().getFieldErrors().stream()
            .map(e -> new ApiError.FieldError(e.getField(), e.getDefaultMessage(), e.getRejectedValue()))
            .toList();

        ApiError error = new ApiError(
            Instant.now(), 400, "Validation Failed", "Invalid input", request.getRequestURI(), fieldErrors
        );
        return ResponseEntity.badRequest().body(error);
    }

    // Handle access denied
    @ExceptionHandler(AccessDeniedException.class)
    public ResponseEntity<ApiError> handleAccessDenied(AccessDeniedException ex, HttpServletRequest request) {
        return buildResponse(403, "Forbidden", "Access denied", request.getRequestURI());
    }

    // Catch-all for unexpected errors
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiError> handleGeneric(Exception ex, HttpServletRequest request) {
        log.error("Unexpected error at {}", request.getRequestURI(), ex);
        return buildResponse(500, "Internal Server Error", "An unexpected error occurred", request.getRequestURI());
    }

    private ResponseEntity<ApiError> buildResponse(int status, String error, String message, String path) {
        return ResponseEntity.status(status).body(
            new ApiError(Instant.now(), status, error, message, path, List.of())
        );
    }
}

// --- Custom domain exceptions ---
public class ResourceNotFoundException extends RuntimeException {
    public ResourceNotFoundException(String resource, Long id) {
        super(String.format("%s with id %d not found", resource, id));
    }
}

public class ConflictException extends RuntimeException {
    public ConflictException(String message) {
        super(message);
    }
}
```

## Common Mistakes

```java
// WRONG: Catching exceptions in every controller
@RestController
public class UserController {
    @GetMapping("/users/{id}")
    public User getUser(@PathVariable Long id) {
        try {
            return userService.findById(id);
        } catch (NotFoundException e) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND);  // Repetitive
        }
    }
}

// CORRECT: Use @ControllerAdvice for centralized handling
@RestController
public class UserController {
    @GetMapping("/users/{id}")
    public User getUser(@PathVariable Long id) {
        return userService.findById(id);  // Exception handled globally
    }
}

// WRONG: Exposing stack traces in error responses
@ExceptionHandler(Exception.class)
public ResponseEntity<String> handle(Exception ex) {
    return ResponseEntity.status(500).body(ex.toString());  // Leaks internals
}

// CORRECT: Return safe error messages
@ExceptionHandler(Exception.class)
public ResponseEntity<ApiError> handle(Exception ex, HttpServletRequest request) {
    log.error("Unexpected error", ex);  // Log full trace server-side
    return buildResponse(500, "Internal Error", "Something went wrong", request.getRequestURI());
}

// WRONG: Not logging exceptions
@ExceptionHandler(Exception.class)
public ResponseEntity<ApiError> handle(Exception ex) {
    return buildResponse(500, "Error", ex.getMessage(), "/path");  // Silent failure
}

// CORRECT: Always log before returning error response
@ExceptionHandler(Exception.class)
public ResponseEntity<ApiError> handle(Exception ex, HttpServletRequest request) {
    log.error("Error at {}", request.getRequestURI(), ex);
    return buildResponse(500, "Error", "Something went wrong", request.getRequestURI());
}
```

## Gotchas
- `@RestControllerAdvice` = `@ControllerAdvice` + `@ResponseBody` (returns JSON, not views)
- Handler methods are matched by exception type — most specific first
- `@ExceptionHandler` in a controller takes precedence over `@ControllerAdvice`
- Multiple `@ControllerAdvice` classes can coexist — use `@Order` for priority
- `@ControllerAdvice(basePackages = "com.example.api")` scopes to specific controllers
- `MethodArgumentNotValidException` is thrown by `@Valid` on `@RequestBody`
- `BindException` is thrown by `@Valid` on `@ModelAttribute` (form binding)
- Always log the exception before returning — don't swallow errors silently

## Related
- java/spring/spring-mvc.md
- java/spring/boot-basics.md
- java/testing/spring-boot-testing.md
