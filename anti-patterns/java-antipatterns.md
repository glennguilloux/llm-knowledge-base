---
id: "antipatterns-java"
title: "Java Anti-Patterns"
language: "java"
category: "anti-patterns"
tags: ["antipatterns", "java", "common-mistakes", "best-practices"]
version: "n/a"
retrieval_hint: "java common mistakes antipatterns equals hashCode exception handling"
last_verified: "2026-05-24"
confidence: "high"
---

# Java Anti-Patterns

## When to Use
- Reviewing Java code for common mistakes
- Training small LLMs to avoid frequent Java errors
- Code review checklists
- Onboarding developers new to Java

## Standard Pattern

```java
// WRONG: Catching Exception (too broad)
try {
    parseData(input);
} catch (Exception e) {
    // Hides bugs, catches everything
}

// CORRECT: Catch specific exceptions
try {
    parseData(input);
} catch (NumberFormatException e) {
    log.warn("Invalid number format: {}", input);
} catch (IOException e) {
    log.error("IO failure", e);
}

// WRONG: String concatenation in loop
String result = "";
for (int i = 0; i < 10000; i++) {
    result += i;  // O(n^2) — creates new StringBuilder each iteration
}

// CORRECT: Use StringBuilder
StringBuilder sb = new StringBuilder();
for (int i = 0; i < 10000; i++) {
    sb.append(i);
}
String result = sb.toString();

// WRONG: Not overriding equals/hashCode
public class User {
    String email;
    // Missing equals/hashCode — HashMap/Set won't work correctly
}

// CORRECT: Override both together
public class User {
    String email;
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        User user = (User) o;
        return Objects.equals(email, user.email);
    }
    @Override
    public int hashCode() {
        return Objects.hash(email);
    }
}

// WRONG: Comparing Strings with ==
String a = new String("hello");
String b = new String("hello");
if (a == b) {  // false — compares references
    System.out.println("equal");
}

// CORRECT: Use .equals()
if (a.equals(b)) {  // true — compares content
    System.out.println("equal");
}

// WRONG: Not using try-with-resources
FileInputStream fis = null;
try {
    fis = new FileInputStream("file.txt");
    process(fis);
} finally {
    if (fis != null) fis.close();  // May throw, masking original exception
}

// CORRECT: try-with-resources
try (FileInputStream fis = new FileInputStream("file.txt")) {
    process(fis);
}  // Auto-closed, even on exception

// WRONG: Returning null instead of Optional
public User findUser(String id) {
    if (notFound) return null;  // Caller may NPE
}

// CORRECT: Use Optional
public Optional<User> findUser(String id) {
    if (notFound) return Optional.empty();
    return Optional.of(user);
}

// WRONG: Raw types
List list = new ArrayList();  // No type safety
list.add("hello");
list.add(42);  // Compiles but corrupts type

// CORRECT: Use generics
List<String> list = new ArrayList<>();
list.add("hello");
// list.add(42);  // Compile error — caught early

// WRONG: Exposing internal state
public class UserCache {
    private Map<String, User> users = new HashMap<>();
    public Map<String, User> getUsers() { return users; }  // Caller can modify!
}

// CORRECT: Return unmodifiable view
public class UserCache {
    private Map<String, User> users = new HashMap<>();
    public Map<String, User> getUsers() { return Collections.unmodifiableMap(users); }
}
```

## Common Mistakes
Java's most dangerous anti-patterns are catching Exception (hides bugs and makes debugging impossible), String concatenation in loops (O(n^2) performance), and neglecting equals/hashCode (breaks collections). Not using try-with-resources leads to resource leaks. Raw types lose compile-time type safety. Exposing mutable internal state breaks encapsulation.

## Gotchas
- `==` compares references for objects, `.equals()` compares content
- Always override `hashCode()` when you override `equals()` — contract violation breaks HashMap
- `null.equals(anything)` throws NullPointerException — use `Objects.equals()` for null-safe comparison
- `final` on a collection only prevents reassignment, not modification of contents
- `String` is immutable — `concat()` creates a new String
- Autoboxing creates objects — `Integer a = 128; Integer b = 128; a == b` is false
- `ConcurrentModificationException` — don't modify a collection while iterating with for-each
- `Collections.unmodifiableList()` is a view, not a copy — original changes reflect

## Related
- java/stdlib/generics-wildcards.md
- java/stdlib/optional-deep-dive.md
- java/build/maven/patterns.md
