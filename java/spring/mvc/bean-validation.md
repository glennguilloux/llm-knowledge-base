---
id: "java-spring-mvc-bean-validation"
title: "Request Validation with Bean Validation"
language: "java"
category: "web"
subcategory: "validation"
tags: ["spring", "mvc", "validation", "bean", "constraint", "valid", "request"]
version: "17+"
retrieval_hint: "Spring MVC Bean Validation @Valid @NotNull @Size @Email constraints"
last_verified: "2026-05-22"
confidence: "high"
---

# Request Validation with Bean Validation

## When to Use
- Validating API request bodies before processing
- Enforcing business rules at the API boundary
- Returning structured validation error responses
- Validating path variables, query parameters, and form data

## Standard Pattern

```java
// --- Request DTO with validation constraints ---
public record CreateUserRequest(
    @NotBlank(message = "Name is required")
    @Size(min = 1, max = 100, message = "Name must be 1-100 characters")
    String name,

    @NotBlank(message = "Email is required")
    @Email(message = "Invalid email format")
    String email,

    @NotNull(message = "Age is required")
    @Min(value = 0, message = "Age must be positive")
    @Max(value = 150, message = "Age must be realistic")
    Integer age,

    @Size(min = 8, message = "Password must be at least 8 characters")
    String password,

    @Pattern(regexp = "^\\+?[0-9]{10,15}$", message = "Invalid phone number")
    String phone
) {}

// --- Controller with @Valid ---
@RestController
@RequestMapping("/api/users")
public class UserController {
    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    @PostMapping
    public ResponseEntity<UserResponse> createUser(@Valid @RequestBody CreateUserRequest request) {
        UserResponse user = userService.create(request);
        return ResponseEntity.status(201).body(user);
    }

    // Validate path variable
    @GetMapping("/{id}")
    public UserResponse getUser(@PathVariable @Min(1) Long id) {
        return userService.findById(id);
    }

    // Validate query parameters
    @GetMapping
    public List<UserResponse> searchUsers(
        @RequestParam @Size(min = 2, max = 50) String query,
        @RequestParam(defaultValue = "0") @Min(0) int page,
        @RequestParam(defaultValue = "20") @Min(1) @Max(100) int size
    ) {
        return userService.search(query, page, size);
    }
}

// --- Custom validation annotation ---
@Target({ElementType.FIELD, ElementType.PARAMETER})
@Retention(RetentionPolicy.RUNTIME)
@Constraint(validatedBy = NoWhitespaceValidator.class)
public @interface NoWhitespace {
    String message() default "Must not contain leading/trailing whitespace";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
}

public class NoWhitespaceValidator implements ConstraintValidator<NoWhitespace, String> {
    @Override
    public boolean isValid(String value, ConstraintValidatorContext context) {
        if (value == null) return true;  // Use @NotNull for null check
        return value.equals(value.trim());
    }
}

// --- Validation groups ---
public interface ValidationGroups {
    interface Create {}
    interface Update {}
}

public record UpdateUserRequest(
    @NotBlank(groups = ValidationGroups.Update.class) String name,
    @Email(groups = ValidationGroups.Update.class) String email
) {}

// In controller: @Validated(ValidationGroups.Update.class)
```

## Common Mistakes

```java
// WRONG: Missing @Valid — validation not triggered
@PostMapping
public User createUser(@RequestBody CreateUserRequest request) {
    // request.name could be null, empty, or 500 chars
    return userService.create(request);
}

// CORRECT: Add @Valid
@PostMapping
public User createUser(@Valid @RequestBody CreateUserRequest request) {
    return userService.create(request);
}

// WRONG: Using @Valid on @PathVariable without configuration
@GetMapping("/{id}")
public User getUser(@Valid @PathVariable Long id) {
    // @Valid doesn't work on simple types without @Validated on class
}

// CORRECT: Use @Validated on controller class for method-level validation
@RestController
@Validated
public class UserController {
    @GetMapping("/{id}")
    public User getUser(@PathVariable @Min(1) Long id) { ... }
}

// WRONG: Catching ConstraintViolationException manually
try {
    validator.validate(request);
} catch (ConstraintViolationException e) {
    // Manual handling — let Spring do this automatically
}

// CORRECT: Let @Valid + @ControllerAdvice handle it
@ExceptionHandler(MethodArgumentNotValidException.class)
public ResponseEntity<ApiError> handleValidation(MethodArgumentNotValidException ex) {
    // Auto-handled by your @ControllerAdvice
}
```

## Gotchas
- `@Valid` triggers validation; without it, constraints are ignored
- `@Validated` on the controller class enables validation on `@PathVariable` and `@RequestParam`
- Validation groups let you apply different rules for create vs update
- Custom validators implement `ConstraintValidator<Annotation, Type>`
- `@NotNull` vs `@NotBlank` vs `@NotEmpty`: null, empty string, empty collection
- `@Email` uses a simple regex — for strict validation, use `@Pattern` with a better regex
- `@Min`/`@Max` work on numeric types; `@Size` works on String, Collection, Map, Array
- Bean Validation 3.0 (Jakarta) uses `jakarta.validation` package, not `javax.validation`

## Related
- java/spring/mvc/controller-advice.md
- java/spring/spring-mvc.md
- java/spring/boot-basics.md
