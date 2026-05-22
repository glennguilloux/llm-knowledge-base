---
id: "java-stdlib-records"
title: "Java Records"
language: "java"
category: "stdlib"
subcategory: "data-structures"
tags: ["records", "immutable", "data-class", "pattern-matching"]
version: "16+"
retrieval_hint: "Java records immutable data class pattern matching"
last_verified: "2026-05-22"
confidence: "high"
---

# Java Records

## When to Use
- Immutable data carriers
- DTOs (Data Transfer Objects)
- Value objects
- Replacing boilerplate POJOs

## Standard Pattern

```java
// Basic record
public record Point(double x, double y) {}

Point p = new Point(1.0, 2.0);
double x = p.x();  // Accessor method (not getX())
double y = p.y();

// Record with validation
public record Range(int min, int max) {
    public Range {
        if (min > max) {
            throw new IllegalArgumentException("min must be <= max");
        }
    }
}

// Record with computed methods
public record Rectangle(double width, double height) {
    public double area() {
        return width * height;
    }

    public boolean isSquare() {
        return width == height;
    }
}

// Record with static factory
public record Email(String address) {
    public Email {
        if (!address.contains("@")) {
            throw new IllegalArgumentException("Invalid email");
        }
    }

    public static Email of(String address) {
        return new Email(address.toLowerCase().trim());
    }
}

// Record implementing interface
public record Person(String name, int age) implements Comparable<Person> {
    @Override
    public int compareTo(Person other) {
        return Integer.compare(this.age, other.age);
    }
}

// Pattern matching (Java 21+)
public static String describe(Object obj) {
    return switch (obj) {
        case Point p when p.x() == 0 && p.y() == 0 -> "Origin";
        case Point p -> "Point(" + p.x() + ", " + p.y() + ")";
        case Rectangle r when r.isSquare() -> "Square";
        case Rectangle r -> "Rectangle";
        default -> "Unknown";
    };
}
```

## Common Mistakes

```java
// WRONG: Trying to set fields
Point p = new Point(1.0, 2.0);
p.x = 3.0;  // Compilation error — records are immutable!

// CORRECT: Create new instance
Point p2 = new Point(3.0, p.y());

// WRONG: Defining mutable fields in record
public record User(String name, List<String> tags) {
    // tags list is mutable! Caller can modify it.
}

// CORRECT: Use defensive copy
public record User(String name, List<String> tags) {
    public User {
        tags = List.copyOf(tags);  // Defensive copy
    }
}

// WRONG: Using getX() convention
p.getX()  // Records use x(), not getX()

// CORRECT: Use accessor name
p.x()
```

## Gotchas
- Records are implicitly `final` — cannot be extended
- All fields are `private final` — accessors have no `get` prefix
- Records get `equals()`, `hashCode()`, and `toString()` automatically
- Records can implement interfaces but cannot extend classes
- Mutable fields (arrays, lists) need defensive copies
- Records can have static fields and methods
- Records are not suitable for entities with identity (use classes)

## Related
- java/stdlib/collections.md
- java/stdlib/optional.md
