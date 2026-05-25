---
id: "csharp-stdlib-nullable-reference-types"
title: "Nullable Reference Types in C#"
language: "csharp"
category: "stdlib"
tags: ["csharp", "dotnet", "nullable", "null-safety", "annotations", "null-state", "warning"]
version: ".NET 8+"
retrieval_hint: "C# nullable enable context nullable reference types null state analysis warning suppression"
last_verified: "2026-05-24"
confidence: "high"
---

# Nullable Reference Types in C#

## When to Use
- Enable `<Nullable>enable</Nullable>` in all new projects — nullable reference types are opt-in but should be the default
- `?` annotation on reference types that can legitimately be null (`string?`, `T?`)
- `!` null-forgiveness operator only when you know a value is not null but the compiler can't prove it
- `[MemberNotNull]` and `[NotNullWhen]` annotations for helper methods that establish null state
- `#nullable` directives for per-file control in large codebases migrating to nullable

## Standard Pattern

```csharp
#nullable enable  // Explicit enable (also set via .csproj <Nullable>enable</Nullable>)

using System;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;

public static class NullableExamples
{
    // ? annotates that a parameter can be null
    public static string Normalize(string? input)
    {
        if (string.IsNullOrEmpty(input))
            return string.Empty;
        // After the null check, compiler knows 'input' is not null here
        return input.Trim().ToUpperInvariant();
    }

    // Return type can be null — annotate accordingly
    public static T? FindOrDefault<T>(IReadOnlyList<T> list, Predicate<T> match)
        where T : class
    {
        for (int i = 0; i < list.Count; i++)
        {
            if (list[i] is T item && match(item))
                return item;
        }
        return null;
    }

    // [NotNullWhen] tells the compiler that the out param is not null when method returns true
    public static bool TryGetUser(
        int id,
        [NotNullWhen(true)] out User? user)
    {
        user = _users.Find(u => u.Id == id);
        return user is not null;
    }

    // Helper method to establish null state for the compiler
    [MemberNotNull(nameof(_cache))]
    private static void EnsureCache()
    {
        _cache ??= new Dictionary<int, User>();
    }

    private static Dictionary<int, User>? _cache;
    private static readonly List<User> _users = new();

    // Null-forgiveness operator — use sparingly
    public static string GetDisplayName(User? user)
    {
        // If we know the user was validated before calling this:
        // But still safer to handle null explicitly
        return user?.DisplayName ?? "(unknown)";
    }

    // Pattern matching with null — compiler tracks null state
    public static void ProcessItem(object? item)
    {
        // After 'is string s', the compiler knows 'item' is a non-null string
        if (item is string s)
        {
            Console.WriteLine(s.Length); // No null warning — s is known not null
        }

        // 'is not null' also establishes non-null state
        if (item is not null)
        {
            Console.WriteLine(item.GetType()); // No null warning
        }
    }

    // Null-conditional chaining
    public static string? GetCity(User? user) =>
        user?.Address?.City;

    // Throw helper for null checks
    public static string RequireNonNull(string? value, [CallerArgumentExpression(nameof(value))] string? paramName = null)
    {
        // Value is not null here — method returns but after this line, value is known non-null
        ArgumentNullException.ThrowIfNull(value, paramName);
        return value; // Compiler knows value is not null
    }
}

public class User
{
    public int Id { get; set; }
    public string DisplayName { get; set; } = "";
    public Address? Address { get; set; }
}

public class Address
{
    public string City { get; set; } = "";
}

#nullable restore  // Restore project default
```

## Common Mistakes

```csharp
// WRONG: Using ! everywhere to suppress warnings instead of fixing roots
public string GetName(string? input) => input!.Length; // Silences warning — may throw at runtime

// CORRECT: Handle the null case properly
public string GetName(string? input) => input?.Length.ToString() ?? "unknown";

// WRONG: Forgetting that T? means different things for value vs reference types
public T? GetResult<T>() // For int (value type), T? means Nullable<int>; for string, it means nullable string
{
    // The compiler handles this differently:
    // Value types: returns Nullable<T>
    // Reference types: returns T with nullable annotation
    return default; // For value types: null (default of Nullable<T>); for ref types: null
}

// CORRECT: Constrain if you need specific behavior
public T? GetClassResult<T>() where T : class  // T? always means nullable reference
{
    return default;
}

public T? GetStructResult<T>() where T : struct  // T? means Nullable<T>
{
    return default;
}

// WRONG: Annotating everything with ? and defeating the purpose
public class BadDesign
{
    public string? Name { get; set; }     // Name should probably never be null
    public string? Id { get; set; }       // Id should probably never be null
    public string? TempCache { get; set; } // This one CAN be null
}

// CORRECT: Only annotate what genuinely can be null
public class GoodDesign
{
    public string Name { get; set; } = "";   // Never null — no annotation needed
    public string Id { get; set; } = "";     // Never null — no annotation needed
    public string? TempCache { get; set; }   // Can genuinely be null
}

// WRONG: Not using [NotNullWhen] on Try-pattern methods
public bool TryGetValue(string key, out string? value)
{
    value = _dict.TryGetValue(key, out var v) ? v : null;
    // Compiler doesn't know value is not null when this returns true
    return value is not null;
}
// Caller: if (TryGetValue("key", out var v)) { v.Length; } // Warning: v may be null

// CORRECT: Annotate with [NotNullWhen(true)]
public bool TryGetValue(string key, [NotNullWhen(true)] out string? value)
{
    bool found = _dict.TryGetValue(key, out value);
    return found;
}
// Caller: if (TryGetValue("key", out var v)) { v.Length; } // No warning!

private readonly Dictionary<string, string> _dict = new();

// WRONG: Required member without nullable awareness
public class Config
{
    public required string? ConnectionString { get; init; }
    // required ensures it's initialized, but it can still be set to null!
}

// CORRECT: If a required member should never be null, don't add ?
public class Config
{
    public required string ConnectionString { get; init; }
}
```

## Gotchas
- Nullable reference types are a compile-time feature only — no runtime enforcement; `null` can still flow through reflection, `default`, or interop
- The `!` null-forgiveness operator does NOT perform a runtime null check — it just tells the compiler "trust me"; misuse leads to `NullReferenceException` at runtime
- `[NotNullWhen(true)]` on `out` parameters changes caller-site null analysis — the `out` variable is known non-null when the method returns `true`
- `#nullable enable` / `#nullable disable` can be used per-file in the source; mismatches between files cause inconsistent warnings
- `T?` is ambiguous without constraints — on unconstrained generics, it means "defaultable" (null for classes, `Nullable<T>` for structs, default for unconstrained generic); use `where T : class` or `where T : struct` for clarity
- Collection initializers on non-nullable properties suppress warnings but don't guarantee non-null at runtime if the initializer uses a method that could return null
- The compiler's null-flow analysis tracks state across `if`, `is`, `switch`, and logical operators (`&&`, `||`) — but it doesn't track across method calls unless annotated with `[NotNull]`, `[NotNullWhen]`, `[MemberNotNull]`, or `[DoesNotReturn]`
- `required` properties guarantee initialization at object creation time but do NOT guarantee non-null — `required string?` can explicitly receive `null` via an initializer
- Legacy codebases can use `<Nullable>warnings</Nullable>` as a migration step — nullable is enabled but warnings-only, not errors

## Related
- csharp/stdlib/pattern-matching.md
- csharp/stdlib/records.md
- csharp/stdlib/string-operations.md
