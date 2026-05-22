---
id: "java-stdlib-generics-wildcards"
title: "Generics and Wildcards"
language: "java"
category: "stdlib"
tags: ["java", "generics", "wildcards", "type-erasure", "bounded", "generic"]
version: "17+"
retrieval_hint: "Java generics wildcards extends super type erasure bounded"
last_verified: "2026-05-22"
confidence: "high"
---

# Generics and Wildcards

## When to Use
- Writing type-safe collections and data structures
- Creating reusable utility methods
- Building APIs that work with multiple types
- Enforcing type constraints at compile time

## Standard Pattern

```java
// Generic class
public class Repository<T> {
    private final List<T> items = new ArrayList<>();

    public void add(T item) {
        items.add(item);
    }

    public T get(int index) {
        return items.get(index);
    }

    public List<T> getAll() {
        return Collections.unmodifiableList(items);
    }
}

// Bounded type parameter
public class NumberStack<T extends Number> {
    private final List<T> items = new ArrayList<>();

    public void push(T item) { items.add(item); }
    public T pop() { return items.remove(items.size() - 1); }

    public double sum() {
        double total = 0;
        for (T item : items) {
            total += item.doubleValue(); // Number method available
        }
        return total;
    }
}

// Wildcard: upper bounded (read-only, covariant)
public double sumList(List<? extends Number> list) {
    double total = 0;
    for (Number n : list) {
        total += n.doubleValue();
    }
    return total;
}
// Works: sumList(List<Integer>), sumList(List<Double>)

// Wildcard: lower bounded (write-capable, contravariant)
public void addIntegers(List<? super Integer> list) {
    list.add(1);
    list.add(2);
    list.add(3);
}
// Works: addIntegers(List<Number>), addIntegers(List<Object>)

// Unbounded wildcard (any type, read-only)
public void printAll(List<?> list) {
    for (Object item : list) {
        System.out.println(item);
    }
}

// Multiple bounds
public <T extends Comparable<T> & Serializable> T max(T a, T b) {
    return a.compareTo(b) >= 0 ? a : b;
}

// Generic method
public static <T> List<T> filter(List<T> list, Predicate<T> predicate) {
    List<T> result = new ArrayList<>();
    for (T item : list) {
        if (predicate.test(item)) {
            result.add(item);
        }
    }
    return result;
}
```

## Common Mistakes

```java
// WRONG: Using raw type
List list = new ArrayList();  // No type safety
list.add("hello");
list.add(42);  // Compiles but corrupts collection

// CORRECT: Use generics
List<String> list = new ArrayList<>();
list.add("hello");
// list.add(42);  // Compile error

// WRONG: Creating generic array
T[] array = new T[10];  // Compile error — type erasure

// CORRECT: Use Object array with cast
@SuppressWarnings("unchecked")
T[] array = (T[]) new Object[10];

// WRONG: Using instanceof with generic type
if (obj instanceof List<String>) {  // Compile error

// CORRECT: Check raw type
if (obj instanceof List<?> List) {
    // Use pattern matching
}

// WRONG: Static field with type parameter
public class Box<T> {
    private static T value;  // Compile error — T not available statically
}

// CORRECT: Pass type to static method
public class Box {
    public static <T> T getValue(T[] array, int index) {
        return array[index];
    }
}

// WRONG: Mixing extends and super
public <T extends Number & Comparable<T>> void process(List<? extends T> list) {
    // Confusing — prefer simpler bounds
}

// CORRECT: Keep bounds simple
public <T extends Comparable<T>> void process(List<T> list) {
    // Clear intent
}
```

## Gotchas
- Type erasure removes generic type info at runtime — `List<String>` and `List<Integer>` are both `List` at runtime
- `? extends T` (upper bound) is read-only — can't add to the list (compiler doesn't know exact type)
- `? super T` (lower bound) allows adding T instances — producer extends, consumer super (PECS)
- PECS principle: Producer Extends, Consumer Super
- Raw types bypass generics — avoid them entirely
- `new ArrayList<>()` uses diamond operator — type inferred from context
- Generic exceptions and catch clauses are not allowed
- `@SuppressWarnings("unchecked")` silences warnings but doesn't make code safe
- `Class<T>` is the common way to pass generic types at runtime

## Related
- java/stdlib/optional-deep-dive.md
- java/stdlib/functional-interfaces.md
- anti-patterns/java-antipatterns.md
