---
id: "java-stdlib-functional-interfaces"
title: "Functional Interfaces and Lambda Expressions"
language: "java"
category: "stdlib"
tags: ["java", "lambda", "functional", "stream", "predicate", "function"]
version: "17+"
retrieval_hint: "lambda functional interface Predicate Function Consumer Supplier stream"
last_verified: "2026-05-24"
confidence: "high"
---

# Functional Interfaces and Lambda Expressions

## When to Use
- Passing behavior as arguments (callbacks, strategies)
- Working with Streams API
- Event handling
- Simplifying anonymous classes

## Standard Pattern

```java
import java.util.function.*;
import java.util.stream.*;

// Built-in functional interfaces
Predicate<String> isLong = s -> s.length() > 10;
Function<String, Integer> toLength = String::length;
Consumer<String> print = System.out::println;
Supplier<List<String>> listFactory = ArrayList::new;
BiFunction<String, String, String> concat = String::concat;
BinaryOperator<Integer> sum = Integer::sum;

// Lambda expressions
List<String> names = List.of("Alice", "Bob", "Charlie");

// Stream with lambdas
List<String> result = names.stream()
    .filter(name -> name.length() > 3)
    .map(String::toUpperCase)
    .sorted()
    .toList();

// Method references
names.forEach(System.out::println);           // Static method
names.stream().map(String::length);           // Instance method
names.stream().map(s -> s.toUpperCase());     // Same as String::toUpperCase

// Custom functional interface
@FunctionalInterface
interface Transformer<T, R> {
    R transform(T input);
    // Can have default methods
    default Transformer<T, R> andThen(Transformer<R, R> after) {
        return input -> after.transform(this.transform(input));
    }
}

Transformer<String, Integer> length = String::length;
Transformer<String, String> upper = String::toUpperCase;

// Composing functions
Function<String, String> trim = String::trim;
Function<String, String> lower = String::toLowerCase;
Function<String, String> pipeline = trim.andThen(lower);

// Collectors with lambdas
Map<Integer, List<String>> byLength = names.stream()
    .collect(Collectors.groupingBy(String::length));

String joined = names.stream()
    .collect(Collectors.joining(", "));
```

## Common Mistakes

```java
// WRONG: Using anonymous class instead of lambda
button.addActionListener(new ActionListener() {
    @Override
    public void actionPerformed(ActionEvent e) {
        handleClick();
    }
});

// CORRECT: Use lambda
button.addActionListener(e -> handleClick());

// WRONG: Reimplementing stream operations
List<String> result = new ArrayList<>();
for (String name : names) {
    if (name.length() > 3) {
        result.add(name.toUpperCase());
    }
}

// CORRECT: Use streams
List<String> result = names.stream()
    .filter(name -> name.length() > 3)
    .map(String::toUpperCase)
    .toList();

// WRONG: Modifying external variable in lambda
int count = 0;
names.forEach(name -> count++);  // Compile error — must be effectively final

// CORRECT: Use AtomicInteger or collect
AtomicInteger count = new AtomicInteger();
names.forEach(name -> count.incrementAndGet());

// WRONG: Complex lambda body
names.stream()
    .filter(name -> {
        boolean valid = name.length() > 3;
        boolean active = !name.startsWith("X");
        return valid && active;  // Hard to read
    })

// CORRECT: Extract to method
names.stream()
    .filter(this::isValidName)
    .map(String::toUpperCase)
    .toList();

private boolean isValidName(String name) {
    return name.length() > 3 && !name.startsWith("X");
}
```

## Gotchas
- `@FunctionalInterface` is optional but recommended — enforces single abstract method
- Lambdas capture variables that are effectively final (assigned once)
- Method references are syntactic sugar for lambdas: `String::length` = `s -> s.length()`
- `Stream` operations are lazy — intermediate ops don't execute until terminal op
- `toList()` (Java 16+) returns unmodifiable list — `collect(Collectors.toList())` returns mutable
- `forEach` is a terminal operation — can't reuse the stream after
- `Collectors.toMap` throws on duplicate keys — use merge function
- Parallel streams have overhead — only beneficial for large datasets with CPU-bound work

## Related
- java/stdlib/generics-wildcards.md
- java/stdlib/optional-deep-dive.md
- anti-patterns/java-antipatterns.md
