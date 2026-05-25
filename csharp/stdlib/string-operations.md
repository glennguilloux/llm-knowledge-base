---
id: "csharp-stdlib-string-operations"
title: "String Operations in C#"
language: "csharp"
category: "stdlib"
tags: ["csharp", "dotnet", "string", "stringbuilder", "span", "interpolation", "text"]
version: ".NET 8+"
retrieval_hint: "C# string interpolation StringBuilder Span string operations null empty whitespace"
last_verified: "2026-05-24"
confidence: "high"
---

# String Operations in C#

## When to Use
- String interpolation (`$"..."`) for readable string formatting
- `StringBuilder` when concatenating strings in loops or hot paths
- `Span<char>` for zero-allocation string slicing in performance-critical code
- `string.IsNullOrWhiteSpace` for input validation (preferred over manual checks)
- Understanding `string` (alias) vs `String` (type) for consistent codebase conventions

## Standard Pattern

```csharp
using System;
using System.Text;

public static class StringExamples
{
    // String interpolation — preferred over string.Format or concatenation
    public static string FormatGreeting(string name, int visitCount) =>
        $"Welcome, {name}! This is visit #{visitCount}.";

    // StringBuilder for loop concatenation
    public static string BuildCsvLine(IEnumerable<string> values)
    {
        var sb = new StringBuilder();
        foreach (var value in values)
        {
            if (sb.Length > 0)
                sb.Append(',');
            sb.Append('"');
            sb.Append(value.Replace("\"", "\"\""));
            sb.Append('"');
        }
        return sb.ToString();
    }

    // Span<char> for zero-allocation parsing
    public static bool TryParsePrefix(ReadOnlySpan<char> input, ReadOnlySpan<char> prefix)
    {
        if (input.Length < prefix.Length)
            return false;
        return input.Slice(0, prefix.Length).SequenceEqual(prefix);
    }

    // Null vs empty vs whitespace — use built-in helpers
    public static ValidationStatus ValidateInput(string? input)
    {
        if (input is null)
            return ValidationStatus.Null;
        if (input == string.Empty)
            return ValidationStatus.Empty;
        if (string.IsNullOrWhiteSpace(input))
            return ValidationStatus.WhitespaceOnly;
        return ValidationStatus.Valid;
    }

    // Safe trimming with null check
    public static string SafeTrim(string? input) =>
        string.IsNullOrWhiteSpace(input) ? string.Empty : input.Trim();
}

public enum ValidationStatus { Null, Empty, WhitespaceOnly, Valid }
```

## Common Mistakes

```csharp
// WRONG: Using == "" for null safety — throws if input is null
if (input == "") { }

// CORRECT: Use string.IsNullOrEmpty or string.IsNullOrWhiteSpace
if (string.IsNullOrEmpty(input)) { }
if (string.IsNullOrWhiteSpace(input)) { }

// WRONG: String concatenation in a loop (O(n²) allocations)
string result = "";
foreach (var item in items)
    result += item + ",";  // Allocates a new string every iteration

// CORRECT: Use StringBuilder for loop concatenation
var sb = new StringBuilder();
foreach (var item in items)
    sb.Append(item).Append(',');
string result = sb.ToString();

// WRONG: Confusing string (alias) with different behavior
String s1 = "hello";  // Works, but inconsistent style
String s2 = null;     // Same type as string — both are System.String

// CORRECT: Use the alias 'string' consistently (C# convention)
string s1 = "hello";
string s2 = null;     // 'string' is an alias for System.String

// WRONG: Not checking for null before calling Trim()
var trimmed = input.Trim();  // NullReferenceException if input is null

// CORRECT: Check first or use the null-conditional operator
var trimmed = input?.Trim() ?? string.Empty;

// WRONG: Using Equals with StringComparison the wrong way
if (a.ToLower() == b.ToLower()) { }  // Allocation-heavy, culture-dependent

// CORRECT: Use StringComparison parameter
if (a.Equals(b, StringComparison.OrdinalIgnoreCase)) { }
```

## Gotchas
- `string` and `String` are identical — `string` is a C# alias for `System.String`; pick one and be consistent
- `StringComparison.OrdinalIgnoreCase` should be used for case-insensitive comparisons on identifiers/keys; `CurrentCultureIgnoreCase` for display text
- `string.Empty` is preferred over `""` in modern C# for readability and to avoid confusion
- `Span<char>` cannot be used as a field in a class or in async methods — it is stack-only; use `ReadOnlySpan<char>` for parameters instead
- `StringBuilder` has an internal buffer that grows by doubling — if you know the approximate size, pass capacity to the constructor
- `string.IsNullOrWhiteSpace` returns `true` for strings containing only whitespace characters (spaces, tabs, newlines, etc.), not just empty strings
- Interpolated strings (`$"..."`) are compiled to `string.Format` calls under the hood — complex formatting can hurt readability; consider extracting to named methods

## Related
- csharp/stdlib/collections.md
- csharp/stdlib/linq.md
- csharp/stdlib/async-await.md
