---
id: "csharp-stdlib-records"
title: "Records in C#"
language: "csharp"
category: "stdlib"
tags: ["csharp", "dotnet", "record", "immutable", "with", "equality", "positional"]
version: ".NET 8+"
retrieval_hint: "C# record class struct with expressions equality positional records init-only"
last_verified: "2026-05-24"
confidence: "high"
---

# Records in C#

## When to Use
- `record class` for immutable data carriers (DTOs, value objects, domain events)
- `record struct` for lightweight immutable structs (small data, stack-allocated)
- Positional records (`record(string Name, int Age)`) for concise one-liners
- `with` expressions for creating modified copies of existing records
- Records instead of classes when value equality, immutability, and terse syntax matter

## Standard Pattern

```csharp
using System;

// Record class — immutable by default, value equality
public sealed record Money(decimal Amount, string Currency)
{
    // Adding validation logic
    public Money : this(Amount, Currency.ToUpperInvariant()) { }

    public Money Add(Money other)
    {
        if (Currency != other.Currency)
            throw new InvalidOperationException(
                $"Cannot add {Currency} and {other.Currency}");
        return this with { Amount = Amount + other.Amount };
    }
}

// Record struct — value type record, stack-allocated
public readonly record struct Point2D(double X, double Y);

// with expression — create a modified copy
public static class RecordExamples
{
    public static void DemonstrateWithExpression()
    {
        var original = new Money(100m, "USD");
        var modified = original with { Amount = 150m };
        // original is unchanged — same as immutable data

        Console.WriteLine(original);    // Money { Amount = 100, Currency = USD }
        Console.WriteLine(modified);    // Money { Amount = 150, Currency = USD }
        Console.WriteLine(original == modified); // False — value equality
    }

    // Positional record — constructor and deconstruction built in
    public record Person(string FirstName, string LastName, int Age);

    public static void DemonstratePositionalRecord()
    {
        var person = new Person("Alice", "Smith", 30);

        // Deconstruction
        var (first, last, age) = person;

        // Value equality
        var same = new Person("Alice", "Smith", 30);
        Console.WriteLine(person == same); // True — compares values, not references

        // ToString is auto-generated nicely
        Console.WriteLine(person); // Person { FirstName = Alice, LastName = Smith, Age = 30 }
    }

    // Record with explicit properties and initialization
    public record OrderLine
    {
        public required string ProductId { get; init; }
        public required int Quantity { get; init; }
        public required decimal UnitPrice { get; init; }

        // Computed property — not part of equality comparison
        public decimal LineTotal => Quantity * UnitPrice;
    }

    // Record inheriting from record
    public record Animal(string Name, int Age);
    public record Dog(string Name, int Age, string Breed) : Animal(Name, Age);
}

// Record vs class decision helper
public static class RecordVsClassGuide
{
    // Use record: immutable data carrier, value equality matters
    public record Coordinate(double Lat, double Lon);

    // Use class: mutable state, identity equality, complex behavior
    public class ShoppingCart
    {
        private readonly List<string> _items = new();
        public void AddItem(string item) => _items.Add(item);
        public IReadOnlyList<string> Items => _items.AsReadOnly();
    }
}
```

## Common Mistakes

```csharp
// WRONG: Expecting record equality to work like reference equality
var a = new Person("Alice", "Smith", 30);
var b = new Person("Alice", "Smith", 30);
bool sameRef = ReferenceEquals(a, b); // False — different objects
bool equal = a == b;                  // True — value equality

// If you need reference equality, use a class, not a record

// WRONG: Forgetting that 'with' creates a shallow copy
var person = new Person("Alice", "Smith", 30);
var modified = person with { FirstName = "Bob" };
Console.WriteLine(person.FirstName); // "Alice" — original is untouched

// But if the record contained mutable reference types, they'd be shared:
public record Team(string Name, List<string> Members);
var team1 = new Team("Alpha", new List<string> { "Alice" });
var team2 = team1 with { Name = "Beta" };
team2.Members.Add("Bob");
Console.WriteLine(team1.Members.Count); // 2! — same List reference

// CORRECT: Re-initialize mutable fields in with expressions
var team2 = team1 with { Name = "Beta", Members = new List<string>(team1.Members) };

// WRONG: Using record when you need mutable state
public record Counter(int Value)
{
    // This creates a new record each time — not mutation!
    public Counter Increment() => this with { Value = Value + 1 };
}

// If you need to mutate state frequently, use a class instead:
public class MutableCounter
{
    public int Value { get; set; }
    public void Increment() => Value++;
}

// WRONG: record struct without readonly
public record struct Broken(int X, int Y); // Mutable by default

// CORRECT: Add readonly for immutability
public readonly record struct FixedPoint(int X, int Y);

// WRONG: Expecting inherited records to compare equal across types
var animal = new Animal("Rex", 5);
var dog = new Dog("Rex", 5, "Labrador");
Console.WriteLine(animal == dog); // False — types differ, even with same data

// CORRECT: Records implement equality within their own type hierarchy only
Console.WriteLine(animal.Equals(dog)); // False
```

## Gotchas
- Records generate `ToString()` with all property names and values — useful for debugging but don't rely on the format for production serialization
- `with` expressions create shallow copies — mutable reference type properties (like `List<T>`) are shared between original and copy
- Record equality is structural/value-based, not reference-based: two records with the same property values are `==` even if they are different objects in memory
- `record class` is a reference type (heap-allocated); `record struct` is a value type (stack-allocated when possible) — choose based on size and usage
- `required` properties on records must be initialized at construction via object initializers or the constructor — they cannot be set later with `init` unless done at creation
- Record inheritance is one-directional: a derived record can equal a base record only if the base calls the record’s equality; in practice, `Dog("Rex", 5) != Animal("Rex", 5)` because `Dog` adds extra fields
- Positional records auto-generate `Deconstruct` method — but if you later add explicit properties, you need to manually update `Deconstruct` if you want them included
- Records are sealed by default in C# 12+ (`sealed record`); to allow inheritance, use the `virtual` keyword explicitly

## Related
- csharp/stdlib/records.md (self-reference for discoverability)
- csharp/stdlib/pattern-matching.md
- csharp/stdlib/collections.md
- csharp/stdlib/enums.md
