---
id: "java-stdlib-null-handling"
title: "Java Null Handling"
language: "java"
category: "stdlib"
subcategory: "utilities"
tags: ["null", "optional", "require-non-null", "nullable", "npe", "null-safety"]
version: "17+"
retrieval_hint: "Java null handling Optional Objects.requireNonNull Nullable annotation avoid NPE"
last_verified: "2026-05-24"
confidence: "high"
---

# Java Null Handling

## When to Use
- Validating method precondition inputs (Objects.requireNonNull)
- Representing potentially absent return values (Optional)
- Documenting nullability in APIs (@Nullable, @NonNull)
- Avoiding NullPointerException through defensive patterns

## Standard Pattern

```java
import java.util.Objects;
import java.util.Optional;
import java.util.List;

public class NullHandling {

    // Objects.requireNonNull for fail-fast parameter validation
    public static String formatName(String first, String last) {
        Objects.requireNonNull(first, "first name must not be null");
        Objects.requireNonNull(last, "last name must not be null");
        return first + " " + last;
    }

    // Optional for return values that might be absent
    public static Optional<Integer> parsePositiveInt(String text) {
        if (text == null || text.isBlank()) {
            return Optional.empty();
        }
        try {
            int value = Integer.parseInt(text.strip());
            return value > 0 ? Optional.of(value) : Optional.empty();
        } catch (NumberFormatException e) {
            return Optional.empty();
        }
    }

    // Chaining Optional operations
    public static String getDisplayName(String input) {
        return Optional.ofNullable(input)
                .filter(s -> !s.isBlank())
                .map(String::strip)
                .map(String::toUpperCase)
                .orElse("UNKNOWN");
    }

    // Null-safe collection processing
    public static List<String> safeProcess(List<String> inputs) {
        if (inputs == null) {
            return List.of();
        }
        return inputs.stream()
                .filter(Objects::nonNull)
                .map(String::strip)
                .filter(s -> !s.isEmpty())
                .toList();
    }

    // Optional.orElseThrow for explicit failure when value is required
    public static int requirePositive(String text) {
        return Optional.ofNullable(text)
                .map(String::strip)
                .flatMap(s -> {
                    try {
                        return Optional.of(Integer.parseInt(s));
                    } catch (NumberFormatException e) {
                        return Optional.empty();
                    }
                })
                .filter(n -> n > 0)
                .orElseThrow(() -> new IllegalArgumentException(
                    "Expected positive integer, got: " + text));
    }

    // Guard pattern: return early on null
    public static int safeStringLength(String text) {
        if (text == null) return 0;
        return text.length();
    }

    public static void main(String[] args) {
        System.out.println(formatName("John", "Doe"));
        System.out.println(parsePositiveInt("42"));       // Optional[42]
        System.out.println(parsePositiveInt("abc"));       // Optional.empty
        System.out.println(getDisplayName("  alice  "));
        System.out.println(safeProcess(List.of("a", null, "", "  b  ")));

        try {
            requirePositive("abc");
        } catch (IllegalArgumentException e) {
            System.out.println("Error: " + e.getMessage());
        }

        try {
            formatName(null, "Doe");
        } catch (NullPointerException e) {
            System.out.println("Error: " + e.getMessage());
        }
    }
}
```

## Common Mistakes

```java
// WRONG: Using Optional as a field type - not serializable, adds overhead
public class User {
    private Optional<String> middleName = Optional.empty();  // Don't do this!
}

// CORRECT: Use null for fields, Optional only for return types
public class User {
    private String middleName;  // null means absent
}

// WRONG: Calling Optional.get() without checking - throws NoSuchElementException
Optional<String> opt = Optional.ofNullable(getNullableValue());
String value = opt.get();  // Throws NoSuchElementException if empty!

// CORRECT: Use orElse, orElseThrow, orElseGet, or ifPresent
String value = opt.orElse("default");
String value = opt.orElseThrow(() -> new IllegalStateException("Missing value"));

// WRONG: Wrapping and immediately unwrapping Optional
Optional<String> result = Optional.of(value);  // value is already non-null
return result.orElse(null);  // defeats the purpose

// CORRECT: Return value directly or use Optional.ofNullable for nullable values
public Optional<String> findUser(int id) {
    User user = lookup(id);
    return Optional.ofNullable(user).map(User::getName);
}

// WRONG: Using Optional.isPresent() + get() instead of functional methods
if (opt.isPresent()) {
    System.out.println(opt.get());  // Verbose and risky
}

// CORRECT: Use ifPresent
opt.ifPresent(System.out::println);

// WRONG: Objects.requireNonNull only throws NPE with no message - hard to debug
Objects.requireNonNull(input);  // NullPointerException at line 42... but why?

// CORRECT: Add descriptive message
Objects.requireNonNull(input, "input must not be null for user processing");

// WRONG: @Nullable annotation doesn't actually enforce anything at runtime
// It's purely informational for static analysis tools
@Nullable
public String findName(String id) { ... }  // Still returns null silently

// CORRECT: Combine @Nullable with clear documentation and Optional for callers
/**
 * Finds a name by ID. @return the name, or null if not found.
 */
@Nullable
public String findName(String id) { ... }
```

## Gotchas
- `Optional.of(null)` throws NullPointerException immediately - use `Optional.ofNullable(null)` which returns `Optional.empty()`
- `Optional` should **never** be used for fields, method parameters, or collection elements - it's designed exclusively for return types to signal "result may be absent"
- `Objects.requireNonNull` is evaluated lazily when the returned value is used - but for fail-fast, store the result: `this.name = Objects.requireNonNull(name)` which validates on assignment
- Chaining `Optional.flatMap` vs `.map`: use `flatMap` when the mapping function itself returns `Optional`, otherwise `map` wraps it in `Optional<Optional<T>>`
- After calling `Optional.ifPresent(consumer)`, the Optional is consumed - you cannot chain further operations on it or call `get()` later; chain everything first
- `@Nullable` and `@NonNull` annotations (from javax.annotation, jetbrains, or checkerframework) only help static analysis tools - they don't generate runtime checks unless combined with a tool like Checker Framework

## Related
- java/stdlib/optional.md
- java/stdlib/exception-handling.md
