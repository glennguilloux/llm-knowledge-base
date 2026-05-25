---
id: "java-stdlib-optional"
title: "Java Optional"
language: "java"
category: "stdlib"
subcategory: "null-safety"
tags: ["optional", "null", "null-safety", "maybe"]
version: "17+"
retrieval_hint: "Java Optional null safety maybe empty orElse"
last_verified: "2026-05-24"
confidence: "high"
---

# Java Optional

## When to Use
- Returning values that may be absent
- Avoiding NullPointerException
- Chaining operations on nullable values
- API design for optional parameters

## Standard Pattern

```java
import java.util.Optional;

// Creating Optional
Optional<String> empty = Optional.empty();
Optional<String> present = Optional.of("hello");
Optional<String> nullable = Optional.ofNullable(getNullableValue());

// Checking presence
if (present.isPresent()) {
    System.out.println(present.get());
}

// Default values
String value = empty.orElse("default");
String value2 = empty.orElseGet(() -> computeDefault());
String value3 = empty.orElseThrow(() -> new NotFoundException("Not found"));

// Chaining operations
Optional<String> upper = present
    .map(String::toUpperCase)
    .filter(s -> s.length() > 3)
    .map(s -> s + "!");

// flatMap for nested Optional
Optional<Optional<String>> nested = Optional.of(Optional.of("hello"));
Optional<String> flat = nested.flatMap(Function.identity());

// or() for alternative suppliers (Java 9+)
Optional<String> result = empty.or(() -> Optional.of("fallback"));

// ifPresent and ifPresentOrElse
present.ifPresent(System.out::println);
empty.ifPresentOrElse(
    System.out::println,
    () -> System.out.println("Empty")
);

// Stream conversion
List<String> values = Optional.of("hello")
    .stream()
    .collect(Collectors.toList());

// API usage
public Optional<User> findUserById(int id) {
    User user = db.get(id);
    return Optional.ofNullable(user);
}

// Usage
findUserById(1)
    .map(User::getName)
    .ifPresent(name -> System.out.println("Found: " + name));
```

## Common Mistakes

```java
// WRONG: Using Optional for parameters
public void process(Optional<String> name) {  // Bad API design!
    name.ifPresent(n -> doSomething(n));
}

// CORRECT: Use method overloading or nullable
public void process(String name) { ... }
public void process() { ... }

// WRONG: Using get() without checking
String value = optional.get();  // NoSuchElementException if empty!

// CORRECT: Use orElse or orElseThrow
String value = optional.orElse("default");
String value = optional.orElseThrow(() -> new NotFoundException());

// WRONG: Optional in collections or fields
List<Optional<String>> names = new ArrayList<>();  // Confusing!
Map<String, Optional<Integer>> ages = new HashMap<>();  // Unnecessary complexity!

// CORRECT: Filter out empty values
List<String> names = optionals.stream()
    .filter(Optional::isPresent)
    .map(Optional::get)
    .collect(Collectors.toList());

// Or use flatMap
List<String> names = optionals.stream()
    .flatMap(Optional::stream)
    .collect(Collectors.toList());
```

## Gotchas
- Optional is not Serializable — don't use in serializable classes
- Don't use Optional for fields, method parameters, or collections
- `Optional.of(null)` throws NPE — use `Optional.ofNullable()`
- `orElse()` always evaluates the argument; `orElseGet()` is lazy
- Optional is a value-based class — don't use identity operations
- Use `Optional.stream()` (Java 9+) for stream integration
- `Optional.isEmpty()` (Java 11+) is cleaner than `!isPresent()`

## Related
- java/stdlib/collections.md
- java/stdlib/records.md
