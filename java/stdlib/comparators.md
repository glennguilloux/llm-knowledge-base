---
id: "java-stdlib-comparators"
title: "Java Comparators and Sorting"
language: "java"
category: "stdlib"
subcategory: "collections"
tags: ["comparator", "comparing", "sorting", "nulls-first", "then-comparing", "natural-order"]
version: "17+"
retrieval_hint: "Java Comparator comparing thenComparing reversed naturalOrder nullsFirst nullsLast sorting"
last_verified: "2026-05-24"
confidence: "high"
---

# Java Comparators and Sorting

## When to Use
- Sorting collections with custom ordering
- Multi-field sorting (primary, secondary, tertiary)
- Handling null values in sorted data
- Defining sort order at API boundaries or configuration
- Building reusable, composable comparison logic

## Standard Pattern

```java
import java.util.*;
import java.util.stream.Collectors;

public record Employee(String name, String department, Integer salary, LocalDate hired) {}

public class ComparatorExamples {

    // Single-field comparison: sort by name
    public static List<String> sortByName(List<String> names) {
        return names.stream()
                .sorted(Comparator.comparing(String::toLowerCase))
                .collect(Collectors.toList());
    }

    // Multi-field sorting: department first, then salary descending
    public static List<Employee> sortByDeptThenSalary(List<Employee> employees) {
        return employees.stream()
                .sorted(Comparator.comparing(Employee::department)
                        .thenComparing(Employee::salary, Comparator.reverseOrder()))
                .collect(Collectors.toList());
    }

    // Null-safe sorting: null departments last
    public static List<Employee> sortWithNullsLast(List<Employee> employees) {
        return employees.stream()
                .sorted(Comparator.comparing(
                        Employee::department,
                        Comparator.nullsLast(Comparator.naturalOrder())))
                .collect(Collectors.toList());
    }

    // Null-safe with multiple fields, both handling nulls
    public static List<Employee> robustSort(List<Employee> employees) {
        return employees.stream()
                .sorted(Comparator.comparing(
                            (Employee e) -> e.department(),
                            Comparator.nullsFirst(Comparator.naturalOrder()))
                        .thenComparing(
                            e -> e.salary(),
                            Comparator.nullsLast(Comparator.reverseOrder())))
                .collect(Collectors.toList());
    }

    // Reversed natural order
    public static List<Integer> sortDescending(List<Integer> numbers) {
        return numbers.stream()
                .sorted(Comparator.reverseOrder())
                .collect(Collectors.toList());
    }

    // Custom comparator with method reference for complex extraction
    public static List<Employee> sortByHireDate(List<Employee> employees) {
        return employees.stream()
                .sorted(Comparator.comparing(Employee::hired))
                .collect(Collectors.toList());
    }

    // Inline anonymous comparator (for cases that don't fit method references)
    public static List<String> sortByLengthThenAlpha(List<String> words) {
        return words.stream()
                .sorted(Comparator.comparingInt(String::length)
                        .thenComparing(Comparator.naturalOrder()))
                .collect(Collectors.toList());
    }

    // Sort a mutable list in-place
    public static void sortInPlace(List<Employee> employees) {
        employees.sort(Comparator.comparing(Employee::name));
    }

    public static void main(String[] args) {
        List<Employee> staff = List.of(
            new Employee("Alice", "Eng", 120000, LocalDate.of(2020, 3, 15)),
            new Employee("Bob", "Eng", 150000, LocalDate.of(2019, 6, 1)),
            new Employee("Charlie", null, 90000, LocalDate.of(2021, 1, 10)),
            new Employee("Diana", "Sales", null, LocalDate.of(2022, 8, 20)),
            new Employee("Eve", "Eng", 120000, LocalDate.of(2018, 11, 5))
        );

        System.out.println("By dept asc, salary desc:");
        sortByDeptThenSalary(staff).forEach(System.out::println);

        System.out.println("\nWith null depts last:");
        sortWithNullsLast(staff).forEach(System.out::println);

        System.out.println("\nRobust sort (null depts first, null salary last):");
        robustSort(staff).forEach(System.out::println);

        System.out.println("\nDescending ints: " + sortDescending(List.of(3, 1, 4, 1, 5)));
        System.out.println("By length then alpha: " + sortByLengthThenAlpha(List.of("banana", "cat", "apple", "be")));
    }
}
```

## Common Mistakes

```java
// WRONG: Using comparing() without handling nulls - throws NPE if field is null
staff.sort(Comparator.comparing(Employee::department));  // NPE if any department is null!

// CORRECT: Wrap with nullsFirst or nullsLast
staff.sort(Comparator.comparing(
    Employee::department,
    Comparator.nullsLast(Comparator.naturalOrder())));

// WRONG: Using .reversed() on the wrong scope - reverses the ENTIRE comparator
Comparator<Employee> cmp = Comparator.comparing(Employee::department)
        .thenComparing(Employee::salary)
        .reversed();  // Reverses BOTH department AND salary!

// CORRECT: Reverse only the specific field
Comparator<Employee> cmp = Comparator.comparing(Employee::department)
        .thenComparing(Employee::salary, Comparator.reverseOrder());

// WRONG: Using comparing() with a primitive-returning method - causes autoboxing overhead
Comparator<String> c = Comparator.comparing(String::length);  // Autoboxes int to Integer

// CORRECT: Use comparingInt, comparingLong, comparingDouble to avoid boxing
Comparator<String> c = Comparator.comparingInt(String::length);

// WRONG: Forgetting that sort() on List is in-place and returns void
List<String> sorted = names.sort(Comparator.naturalOrder());  // Compile error! sort() is void

// CORRECT: sort() mutates the list; use stream().sorted() for a new list
names.sort(Comparator.naturalOrder());  // Mutates names
List<String> sorted = names.stream().sorted(Comparator.naturalOrder()).toList();  // New list

// WRONG: Using naturalOrder() on a type that doesn't implement Comparable
Comparator<Thread> c = Comparator.naturalOrder();  // Compile error! Thread doesn't implement Comparable

// CORRECT: Use naturalOrder() only on Comparable types, or provide a comparator
Comparator<String> c = Comparator.naturalOrder();  // String implements Comparable
```

## Gotchas
- `Comparator.nullsFirst(nullComparator)` - the second argument is the comparator used for **non-null** values; `nullsFirst` only controls where nulls go
- `Comparator.comparing(Function)` uses the extracted key's natural ordering - the key **must** implement `Comparable` or you get a compile error
- `Comparator.thenComparing` is a default method on the `Comparator` interface - you can chain arbitrarily: `.comparing(...).thenComparing(...).thenComparing(...)`
- `List.sort(Comparator)` replaces the old `Collections.sort(List, Comparator)` - it's the same operation but called directly on the list
- `Comparator.reverseOrder()` returns a comparator for `Comparable` types in reverse natural order; `Comparator.reversed()` reverses an existing comparator
- When using `Comparator.comparing` with a lambda that returns a primitive (e.g., `e -> e.age()` where age is `int`), use `comparingInt` to avoid autoboxing - the compiler won't warn you about the boxing overhead
- `TreeSet` and `TreeMap` use the comparator for **equality** - two elements where `compare(a, b) == 0` are considered equal, even if `.equals()` would return false

## Related
- java/stdlib/collections.md
- java/stdlib/streams.md
