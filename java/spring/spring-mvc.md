---
id: "java-spring-mvc"
title: "Spring MVC Request Handling"
language: "java"
category: "web"
subcategory: "api-framework"
tags: ["spring", "mvc", "controller", "request", "response", "exception"]
version: "17+"
retrieval_hint: "Spring MVC controller request mapping exception handler"
last_verified: "2026-05-24"
confidence: "high"
---

# Spring MVC Request Handling

## When to Use
- Building REST APIs with Spring
- Request/response mapping
- Exception handling
- Request validation

## Standard Pattern

```java
import org.springframework.web.bind.annotation.*;
import org.springframework.http.*;

// Controller with request mapping
@RestController
@RequestMapping("/api/v1")
public class ApiController {

    @GetMapping("/users")
    public ResponseEntity<List<User>> listUsers(
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "10") int size,
        @RequestParam(required = false) String search
    ) {
        List<User> users = userService.findAll(page, size, search);
        return ResponseEntity.ok(users);
    }

    @GetMapping("/users/{id}")
    public ResponseEntity<User> getUser(@PathVariable Long id) {
        return userService.findById(id)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    @PostMapping("/users")
    public ResponseEntity<User> createUser(@Valid @RequestBody UserRequest request) {
        User user = userService.create(request);
        URI location = URI.create("/api/v1/users/" + user.getId());
        return ResponseEntity.created(location).body(user);
    }

    @PatchMapping("/users/{id}")
    public ResponseEntity<User> updateUser(
        @PathVariable Long id,
        @RequestBody Map<String, Object> updates
    ) {
        return ResponseEntity.ok(userService.partialUpdate(id, updates));
    }
}

// Global exception handler
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleNotFound(ResourceNotFoundException ex) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
            .body(new ErrorResponse("NOT_FOUND", ex.getMessage()));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidation(MethodArgumentNotValidationException ex) {
        List<String> errors = ex.getBindingResult().getFieldErrors().stream()
            .map(e -> e.getField() + ": " + e.getDefaultMessage())
            .collect(Collectors.toList());
        return ResponseEntity.badRequest()
            .body(new ErrorResponse("VALIDATION_ERROR", errors));
    }
}

// DTO with validation
public record UserRequest(
    @NotBlank String name,
    @Email String email,
    @Min(0) @Max(150) int age
) {}
```

## Common Mistakes

```java
// WRONG: Returning raw objects without ResponseEntity
@GetMapping("/users/{id}")
public User getUser(@PathVariable Long id) {
    return userService.findById(id);  // Always 200, even if null!
}

// CORRECT: Use ResponseEntity for control
@GetMapping("/users/{id}")
public ResponseEntity<User> getUser(@PathVariable Long id) {
    return userService.findById(id)
        .map(ResponseEntity::ok)
        .orElse(ResponseEntity.notFound().build());
}

// WRONG: Catching exceptions in controller
@GetMapping("/users/{id}")
public User getUser(@PathVariable Long id) {
    try {
        return userService.findById(id);
    } catch (Exception e) {
        return null;  // 200 with null body!
    }
}

// CORRECT: Use @ControllerAdvice for exception handling

// WRONG: Missing @RequestBody on POST parameter
@PostMapping("/users")
public User createUser(UserRequest request) {
    // Request body not deserialized — fields are null!
    return userService.create(request);
}

// CORRECT: Add @RequestBody
@PostMapping("/users")
public User createUser(@RequestBody UserRequest request) {
    return userService.create(request);
}
```

## Gotchas
- `@RestController` = `@Controller` + `@ResponseBody`
- `@PathVariable` for URL path parameters, `@RequestParam` for query parameters
- `@RequestBody` for JSON body
- `ResponseEntity.created(location).body(resource)` for 201 responses
- `@Valid` triggers Bean Validation annotations
- `@ControllerAdvice` handles exceptions across all controllers
- Use `@PatchMapping` for partial updates

## Related
- java/spring/boot-basics.md
- java/spring/spring-security/jwt-auth.md
- java/spring/spring-data/jpa-repositories.md
