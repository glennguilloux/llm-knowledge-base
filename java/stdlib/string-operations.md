---
id: "java-stdlib-string-operations"
title: "Java String Operations"
language: "java"
category: "stdlib"
subcategory: "strings"
tags: ["string", "stringbuilder", "format", "text-blocks", "string-methods", "switch"]
version: "17+"
retrieval_hint: "Java string concatenation StringBuilder format text blocks switch expression string methods"
last_verified: "2026-05-24"
confidence: "high"
---

# Java String Operations

## When to Use
- String concatenation in loops (StringBuilder)
- Formatted output (String.format, printf)
- Multi-line strings like SQL, JSON, HTML (text blocks, Java 15+)
- Common string manipulation (split, join, replace, strip)
- Switch expressions with String cases

## Standard Pattern

```java
import java.util.Objects;

public class StringOperations {

    // Prefer + for simple concatenation (compiler uses StringBuilder)
    public static String simpleConcat(String first, String last) {
        return "Hello, " + first + " " + last + "!";
    }

    // Use StringBuilder for loops or conditional building
    public static String buildCsv(String[] items) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < items.length; i++) {
            if (i > 0) sb.append(", ");
            sb.append(items[i]);
        }
        return sb.toString();
    }

    // String.format for complex layouts
    public static String formatUser(String name, int age, double score) {
        return String.format("User: %-15s | Age: %3d | Score: %6.2f", name, age, score);
    }

    // Text blocks (Java 15+) for multi-line content
    public static String buildSqlQuery() {
        return """
            SELECT u.id, u.name, COUNT(o.id) AS order_count
            FROM users u
            LEFT JOIN orders o ON u.id = o.user_id
            WHERE u.active = true
            GROUP BY u.id, u.name
            ORDER BY order_count DESC
            """;
    }

    // Common string methods
    public static boolean validateEmail(String email) {
        if (email == null) return false;
        email = email.strip();  // Java 11+, trims whitespace including unicode
        return email.contains("@")
            && !email.isBlank()         // Java 11+
            && email.indexOf('@') > 0
            && email.indexOf('@') < email.length() - 1;
    }

    // Joining and splitting
    public static String joinWithDelimiter(java.util.List<String> parts) {
        return String.join(", ", parts);
    }

    // Switch expression with strings (Java 14+)
    public static String describeDay(String day) {
        return switch (day.toUpperCase()) {
            case "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY" -> "Weekday";
            case "SATURDAY", "SUNDAY" -> "Weekend";
            default -> "Unknown";
        };
    }

    public static void main(String[] args) {
        System.out.println(simpleConcat("John", "Doe"));
        System.out.println(buildCsv(new String[]{"a", "b", "c"}));
        System.out.println(formatUser("Alice", 30, 95.456));
        System.out.println(buildSqlQuery());
        System.out.println(validateEmail("  test@example.com  "));
        System.out.println(joinWithDelimiter(java.util.List.of("x", "y", "z")));
        System.out.println(describeDay("Saturday"));
    }
}
```

## Common Mistakes

```java
// WRONG: Using + in a loop - creates many intermediate String objects
String result = "";
for (String item : items) {
    result += item + ", ";  // Creates new StringBuilder each iteration!
}

// CORRECT: Use StringBuilder explicitly
StringBuilder sb = new StringBuilder();
for (String item : items) {
    if (sb.length() > 0) sb.append(", ");
    sb.append(item);
}
String result = sb.toString();

// WRONG: Forgetting String.format returns a value, doesn't print
System.out.println("Name: %s, Age: %d", name, age);  // println doesn't format!

// CORRECT: Use String.format or printf
System.out.printf("Name: %s, Age: %d%n", name, age);
String formatted = String.format("Name: %s, Age: %d", name, age);

// WRONG: Text blocks with closing """ not on its own line
String json = """
    {"name": "Alice",
     "age": 30}
""";  // The closing """ is on the same line as content!

// CORRECT: Closing """ must be on its own line
String json = """
    {"name": "Alice",
     "age": 30}
    """;

// WRONG: Comparing strings with == instead of .equals()
if (input == "yes") { ... }  // Compares references, not content!

// CORRECT: Use .equals()
if ("yes".equals(input)) { ... }

// WRONG: Using StringBuilder when simple + suffices (hurts readability)
StringBuilder sb = new StringBuilder("Hello").append(" ").append("World");

// CORRECT: Simple + for straightforward concatenation
String greeting = "Hello" + " " + "World";
```

## Gotchas
- The compiler converts `a + b + c` to a single `StringBuilder` operation, but NOT inside loops - each loop iteration creates a new StringBuilder
- `String.format` uses `Locale.getDefault()` for number formatting - use `Locale.US` for consistent decimal points: `String.format(Locale.US, "%.2f", value)`
- Text blocks automatically strip trailing whitespace; the position of the closing `"""` determines the indentation (incidental whitespace)
- `String.strip()` (Java 11+) handles Unicode whitespace; `String.trim()` only handles characters <= '\u0020'
- Switch on String works because it uses `String.hashCode()` then `.equals()` internally - null cases must be handled before the switch or with a `case null` (Java 17+)
- `String.join` accepts `Iterable<? extends CharSequence>` - passing an `int[]` will compile but join the array reference, not the ints

## Related
- java/stdlib/collections.md
- java/stdlib/regex.md
