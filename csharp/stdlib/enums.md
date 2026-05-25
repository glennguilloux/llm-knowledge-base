---
id: "csharp-stdlib-enums"
title: "Enums and Conversions in C#"
language: "csharp"
category: "stdlib"
tags: ["csharp", "dotnet", "enum", "flags", "tryparse", "switch", "enum-conversion"]
version: ".NET 8+"
retrieval_hint: "C# enum definition Enum.TryParse Flags attribute switch on enum conversion"
last_verified: "2026-05-24"
confidence: "high"
---

# Enums and Conversions in C#

## When to Use
- `enum` for a closed set of named constants (status codes, directions, categories)
- `Enum.TryParse` for safely converting user input or config strings to enum values
- `[Flags]` attribute for enums that represent combinable bit flags
- `switch` expressions on enums for exhaustive branching
- Extension methods on enums for adding display names, descriptions, or behavior

## Standard Pattern

```csharp
using System;
using System.ComponentModel;

// Standard enum definition
public enum OrderStatus
{
    Pending = 0,
    Processing = 1,
    Shipped = 2,
    Delivered = 3,
    Cancelled = 4
}

// Flags enum — powers of 2 for bitwise combination
[Flags]
public enum FilePermissions
{
    None = 0,
    Read = 1,           // 0b0001
    Write = 2,          // 0b0010
    Execute = 4,        // 0b0100
    ReadWrite = Read | Write,  // Combinable: 0b0011
}

public static class EnumExamples
{
    // Enum.TryParse with case-insensitive parsing
    public static bool TrySetStatus(string? input, out OrderStatus status)
    {
        if (string.IsNullOrWhiteSpace(input))
        {
            status = OrderStatus.Pending;
            return false;
        }
        return Enum.TryParse(input, ignoreCase: true, out status);
    }

    // Switch expression on enum — compiler checks exhaustiveness
    public static string GetStatusLabel(OrderStatus status) => status switch
    {
        OrderStatus.Pending => "Awaiting processing",
        OrderStatus.Processing => "Being prepared",
        OrderStatus.Shipped => "In transit",
        OrderStatus.Delivered => "Completed",
        OrderStatus.Cancelled => "Cancelled",
        _ => throw new ArgumentOutOfRangeException(nameof(status), $"Unknown: {status}")
    };

    // Switch statement for more complex logic
    public static bool CanTransition(OrderStatus from, OrderStatus to) => (from, to) switch
    {
        (OrderStatus.Pending, OrderStatus.Processing) => true,
        (OrderStatus.Pending, OrderStatus.Cancelled) => true,
        (OrderStatus.Processing, OrderStatus.Shipped) => true,
        (OrderStatus.Processing, OrderStatus.Cancelled) => true,
        (OrderStatus.Shipped, OrderStatus.Delivered) => true,
        _ => false
    };

    // Enum to string and back
    public static void EnumConversionRoundTrip()
    {
        // Enum to string
        string label = OrderStatus.Shipped.ToString();  // "Shipped"

        // String back to enum
        var parsed = Enum.Parse(typeof(OrderStatus), "Shipped");

        // From integer
        var fromInt = (OrderStatus)2;  // OrderStatus.Shipped
    }

    // Flags enum operations
    public static FilePermissions GrantPermission(FilePermissions current, FilePermissions grant) =>
        current | grant;

    public static FilePermissions RevokePermission(FilePermissions current, FilePermissions revoke) =>
        current & ~revoke;

    public static bool HasPermission(FilePermissions current, FilePermissions check) =>
        (current & check) == check;
}

// Extension methods on enums
public static class OrderStatusExtensions
{
    // Description attribute approach for display names
    public static bool IsTerminal(this OrderStatus status) =>
        status is OrderStatus.Delivered or OrderStatus.Cancelled;

#if false // Using DescriptionAttribute example
    public static string GetDescription(this OrderStatus status)
    {
        var field = status.GetType().GetField(status.ToString());
        var attr = field?.GetCustomAttributes(typeof(DescriptionAttribute), false)
            .FirstOrDefault() as DescriptionAttribute;
        return attr?.Description ?? status.ToString();
    }
#endif

    // Simple mapping without attributes
    public static ConsoleColor ToConsoleColor(this OrderStatus status) => status switch
    {
        OrderStatus.Pending => ConsoleColor.Yellow,
        OrderStatus.Processing => ConsoleColor.Cyan,
        OrderStatus.Shipped => ConsoleColor.Blue,
        OrderStatus.Delivered => ConsoleColor.Green,
        OrderStatus.Cancelled => ConsoleColor.Red,
        _ => ConsoleColor.White
    };
}
```

## Common Mistakes

```csharp
// WRONG: Enum.Parse without try/catch — throws on invalid input
var status = (OrderStatus)Enum.Parse(typeof(orderStatus), userInput);  // Throws ArgumentException

// CORRECT: Use Enum.TryParse for safe conversion
if (Enum.TryParse<OrderStatus>(userInput, ignoreCase: true, out var status))
{
    // Use status
}

// WRONG: Using [Flags] without powers of 2
[Flags]
public enum BadFlags
{
    Read = 1,
    Write = 2,
    ReadWrite = 3  // 3 is not a power of 2 — breaks bitwise logic
}

// CORRECT: Use powers of 2 (or bit shifts)
[Flags]
public enum GoodFlags
{
    None = 0,
    Read = 1 << 0,   // 1
    Write = 1 << 1,  // 2
    Execute = 1 << 2 // 4
}

// WRONG: Checking flags with == instead of HasFlag or bitwise AND
if (permissions == FilePermissions.Read) { } // Fails if other flags are also set

// CORRECT: Use HasFlag or bitwise AND
if (permissions.HasFlag(FilePermissions.Read)) { }
// Or for hot paths (no allocation):
if ((permissions & FilePermissions.Read) == FilePermissions.Read) { }

// WRONG: Casting an undefined integer to enum silently succeeds
var invalid = (OrderStatus)999;  // Compiles and runs — value is 990, not a defined member

// CORRECT: Validate with Enum.IsDefined before using
if (Enum.IsDefined(typeof(OrderStatus), value))
{
    var status = (OrderStatus)value;
}

// WRONG: Switch on enum without a default case (small models forget exhaustiveness)
string label = status switch   // Compiler warning: not all cases handled
{
    OrderStatus.Pending => "Pending",
    OrderStatus.Shipped => "Shipped"
};

// CORRECT: Include a default/discard case
string label = status switch
{
    OrderStatus.Pending => "Pending",
    OrderStatus.Shipped => "Shipped",
    _ => status.ToString()
};
```

## Gotchas
- `Enum.Parse` throws `ArgumentException` on invalid input; always use `Enum.TryParse` for external data
- `(MyEnum)42` will succeed at runtime even if 42 is not a defined enum value — `Enum.IsDefined` can catch this
- `[Flags]` enums should use powers of 2; the `[Flags]` attribute itself doesn't enforce correct values — it only changes `ToString()` output
- `Enum.ToString()` returns the defined member name for single values but comma-separated names for combined flags: `"Read, Write"`
- Switch expressions on enums trigger compiler warnings for non-exhaustive matches, but regular switch statements do not — prefer switch expressions for safety
- Enum backing type defaults to `int` but can be changed: `enum Small : byte { A, B, C }` — be explicit when serializing
- `Enum.GetValues()` returns an `Array`, not a typed collection — cast or use `.Cast<T>()` for LINQ: `Enum.GetValues(typeof(OrderStatus)).Cast<OrderStatus>()`
- The default value of any enum is `0`, so always define a `None = 0` member to represent "unset"

## Related
- csharp/stdlib/pattern-matching.md
- csharp/stdlib/collections.md
- csharp/stdlib/records.md
