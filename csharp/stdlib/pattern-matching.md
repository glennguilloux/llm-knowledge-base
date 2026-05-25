---
id: "csharp-stdlib-pattern-matching"
title: "Pattern Matching in C#"
language: "csharp"
category: "stdlib"
tags: ["csharp", "dotnet", "pattern-matching", "switch-expression", "deconstruction", "is"]
version: ".NET 8+"
retrieval_hint: "C# switch expression property patterns when guards is pattern deconstruction exhaustiveness"
last_verified: "2026-05-24"
confidence: "high"
---

# Pattern Matching in C#

## When to Use
- `switch` expressions for exhaustive, expression-based branching (preferred over if/else chains)
- Property patterns (`{ Length: > 0 }`) for deep matching on object shapes
- `when` guards for additional conditions inside switch arms
- `is` pattern matching for type checks with variable declaration
- Deconstruction to extract values inline during matching

## Standard Pattern

```csharp
using System;

public static class PatternMatchingExamples
{
    // Switch expression with property patterns — exhaustive
    public static string Describe(object value) => value switch
    {
        null => "null",
        int i when i < 0 => $"negative int: {i}",
        int i when i > 1000 => $"large int: {i}",
        int i => $"int: {i}",
        string { Length: 0 } => "empty string",
        string s when s.Length > 100 => $"long string ({s.Length} chars)",
        string s => $"string: \"{s}\"",
        bool b => b ? "yes" : "no",
        _ => $"something else: {value.GetType().Name}"
    };

    // Property patterns — nested property matching
    public record WeatherInfo(double TemperatureC, double Humidity, string Condition);
    public static string GetWeatherAdvice(WeatherInfo weather) => weather switch
    {
        { Condition: "Thunderstorm" } => "Stay indoors!",
        { TemperatureC: > 35.0 } => "Extreme heat — stay hydrated",
        { TemperatureC: < -10.0 } => "Extreme cold — bundle up",
        { Humidity: > 80.0, Condition: "Rain" } => "High humidity rain — muggy",
        { Condition: "Clear", TemperatureC: >= 18 and <= 28 } => "Perfect weather",
        _ => "Normal conditions"
    };

    // Relational patterns with 'and', 'or', 'not'
    public static string GradeFromScore(int score) => score switch
    {
        >= 90 => "A",
        >= 80 => "B",
        >= 70 => "C",
        >= 60 => "D",
        >= 0 and < 60 => "F",
        _ => throw new ArgumentOutOfRangeException(nameof(score), "Score must be 0-100")
    };

    // Type pattern with variable and property check
    public static double CalculateArea(object shape) => shape switch
    {
        Circle { Radius: var r } => Math.PI * r * r,
        Rectangle { Width: var w, Height: var h } => w * h,
        Triangle { Base: @ var b, Height: var h } => 0.5 * b * h,
        null => throw new ArgumentNullException(nameof(shape)),
        _ => throw new ArgumentException($"Unknown shape: {shape.GetType().Name}")
    };

    // Deconstruction with var discards
    public static void ProcessCoordinate((double X, double Y, double Z) coord)
    {
        var (x, y, _) = coord; // Discard Z — only use X and Y
        Console.WriteLine($"Processing 2D point ({x}, {y})");
    }

    // List pattern matching (C# 11+)
    public static string DescribeArray(int[] arr) => arr switch
    {
        [] => "empty",
        [var single] => $"single element: {single}",
        [var first, .. var middle, var last] => $"first={first}, middle=[{middle.Length} items], last={last}",
        [.. var all] => $"array with {all.Length} elements"
    };

    // Refutable if pattern with declaration
    public static string TryGetMessage(object? obj)
    {
        if (obj is string { Length: > 0 } s)
            return $"Got: {s}";

        if (obj is int i and > 0)
            return $"Positive int: {i}";

        return "Nothing useful";
    }
}

public record Circle(double Radius);
public record Rectangle(double Width, double Height);
public record Triangle(double Base, double Height);
```

## Common Mistakes

```csharp
// WRONG: Using switch statement when switch expression is simpler
string result;
switch (value)
{
    case int i:
        result = $"int: {i}";
        break;
    case string s:
        result = s;
        break;
    default:
        result = "unknown";
        break;
}

// CORRECT: Switch expression is more concise and returns a value
string result = value switch
{
    int i => $"int: {i}",
    string s => s,
    _ => "unknown"
};

// WRONG: Forgetting that switch expressions must be exhaustive (all cases covered)
// This compiles with a warning but may throw at runtime
string label = status switch
{
    OrderStatus.Pending => "pending",
    OrderStatus.Shipped => "shipped"
    // Missing other cases — throws SwitchExpressionException
};

// CORRECT: Add a discard (_) case for exhaustiveness
string label = status switch
{
    OrderStatus.Pending => "pending",
    OrderStatus.Shipped => "shipped",
    _ => status.ToString()
};

// WRONG: Using 'is' pattern matching but forgetting the input is nullable
if (input is string s) { }
// If input is not string, s is unassigned — accessing s outside the if is a compile error

// CORRECT: Pattern variables are only definitely assigned when the pattern matches
if (input is string s && s.Length > 0)
{
    // s is definitely assigned here
    Console.WriteLine(s);
}
// Do NOT use s here — it's not assigned

// WRONG: Confusing 'when' guard with fallthrough (switch expressions DON'T fallthrough)
var result = value switch
{
    int i when i > 0 => "positive",
    int i => "non-positive"  // This is a separate arm, NOT a fallthrough
};

// WRONG: Using list patterns with non-array types incorrectly
// List patterns only work on arrays, spans, and indexable types
if (myList is [var first, ..]) { } // Compile error if myList is List<T>

// CORRECT: Convert to array or use indexer patterns for List<T>
if (myList is [var first, ..]) { } // Only works if myList supports indexer and .Length
// For IEnumerable<T>, use LINQ instead:
if (myList.Count > 0)
{
    var first = myList[0];
}
```

## Gotchas
- Switch expressions are exhaustive by contract — the compiler warns (CS8509) if not all cases are handled; always include a discard `_` case or handle all enum members
- Pattern variables (`var i`, `var s`) are only in scope and definitely assigned when the pattern matches — using them outside the `is`/`when` block is a compile error
- Property patterns can nest: `Person { Address: { City: "London" } }` matches a person whose address city is "London"
- The `and`, `or`, `not` relational patterns are C# 9+; `not null` is preferred over `!= null` for null checks
- List patterns (`[..]`, `[a, b, ..]`) require the type to have a `Length`/`Count` property and an indexer — they work on `T[]`, `Span<T>`, and `IList<T>` but not `IEnumerable<T>`
- Deconstruction patterns call the `Deconstruct` method — if none exists, positional patterns fail at compile time
- Pattern matching with `when` guards are evaluated top-to-bottom — order matters: put more specific guards before general ones
- `var` in a pattern always matches (it's a discard or capture) — `case var x =>` is the same as `case _ =>` but captures the value; use `_` when you don't need the value

## Related
- csharp/stdlib/records.md
- csharp/stdlib/enums.md
- csharp/stdlib/nullable-reference-types.md
