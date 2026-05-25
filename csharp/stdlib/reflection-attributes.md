---
id: "csharp-stdlib-reflection-attributes"
title: "C# Reflection and Attributes: Type Info, Custom Attributes, and Source Generators"
language: "csharp"
category: "stdlib"
tags: ["csharp", "reflection", "attributes", "Type", "custom-attributes", "source-generators"]
version: ".NET 8+"
retrieval_hint: "csharp reflection getting type info custom attributes reflection for validation source generators overview"
last_verified: "2026-05-24"
confidence: "high"
---

# C# Reflection and Attributes: Type Info, Custom Attributes, and Source Generators

## When to Use
- Inspecting types at runtime with reflection
- Creating and reading custom attributes
- Building validation frameworks
- Understanding source generators as a compile-time alternative to reflection

## Standard Pattern

```csharp
using System;
using System.Linq;
using System.Reflection;

// Getting type information
Type stringType = typeof(string);
Type intType = typeof(int);
Type listType = typeof(List<string>);

Console.WriteLine(stringType.Name);           // "String"
Console.WriteLine(stringType.FullName);       // "System.String"
Console.WriteLine(stringType.IsClass);        // true
Console.WriteLine(intType.IsValueType);       // true
Console.WriteLine(listType.IsGenericType);    // true

// Getting type from instance
object obj = "hello";
Type type = obj.GetType();

// Getting members
var methods = typeof(string).GetMethods(BindingFlags.Public | BindingFlags.Instance);
var props = typeof(User).GetProperties();
var fields = typeof(User).GetFields(BindingFlags.NonPublic | BindingFlags.Instance);

// Custom attributes
[AttributeUsage(AttributeTargets.Class | AttributeTargets.Property, AllowMultiple = false)]
public class TableAttribute : Attribute
{
    public string Name { get; }
    public TableAttribute(string name) => Name = name;
}

[AttributeUsage(AttributeTargets.Property)]
public class RequiredAttribute : Attribute { }

[AttributeUsage(AttributeTargets.Property)]
public class MaxLengthAttribute : Attribute
{
    public int Length { get; }
    public MaxLengthAttribute(int length) => Length = length;
}

// Using custom attributes
[Table("users")]
public class User
{
    public int Id { get; set; }

    [Required]
    [MaxLength(255)]
    public string Name { get; set; } = "";

    [Required]
    [MaxLength(255)]
    public string Email { get; set; } = "";
}

// Reading attributes at runtime
void Validate(object obj)
{
    var type = obj.GetType();
    var tableAttr = type.GetCustomAttribute<TableAttribute>();
    Console.WriteLine($"Table: {tableAttr?.Name}");

    foreach (var prop in type.GetProperties())
    {
        var required = prop.GetCustomAttribute<RequiredAttribute>();
        var maxLength = prop.GetCustomAttribute<MaxLengthAttribute>();
        var value = prop.GetValue(obj);

        if (required != null && value is string str && string.IsNullOrEmpty(str))
            Console.WriteLine($"{prop.Name} is required!");

        if (maxLength != null && value is string s && s.Length > maxLength.Length)
            Console.WriteLine($"{prop.Name} exceeds max length {maxLength.Length}");
    }
}

// Reflection for validation framework
public static class Validator
{
    public static List<string> Validate(object obj)
    {
        var errors = new List<string>();
        var type = obj.GetType();

        foreach (var prop in type.GetProperties())
        {
            var value = prop.GetValue(obj);

            // Required
            if (prop.GetCustomAttribute<RequiredAttribute>() != null)
            {
                if (value is null or "")
                    errors.Add($"{prop.Name} is required");
            }

            // MaxLength
            var maxLen = prop.GetCustomAttribute<MaxLengthAttribute>();
            if (maxLen != null && value is string s && s.Length > maxLen.Length)
                errors.Add($"{prop.Name} must be <= {maxLen.Length} characters");

            // Range
            var range = prop.GetCustomAttribute<RangeAttribute>();
            if (range != null && value is IComparable cmp)
            {
                if (cmp.CompareTo(range.Min) < 0 || cmp.CompareTo(range.Max) > 0)
                    errors.Add($"{prop.Name} must be between {range.Min} and {range.Max}");
            }
        }

        return errors;
    }
}

// Source generators — compile-time alternative to reflection
// Instead of runtime reflection, source generators create code at compile time
// Example: Auto-generating JSON serializers, mapping code, etc.
// [JsonSerializable(typeof(User))]  // System.Text.Json source generator
// public partial class AppJsonContext : JsonSerializerContext { }

// Creating instances with reflection
Type userType = typeof(User);
var user = (User)Activator.CreateInstance(userType)!;
var nameProp = userType.GetProperty("Name");
nameProp?.SetValue(user, "Alice");

// Generic methods with reflection
var listType = typeof(List<>).MakeGenericType(typeof(int));
var list = (IList)Activator.CreateInstance(listType)!;
list.Add(42);
```

## Common Mistakes

```csharp
// WRONG: Using reflection when direct code is possible
// Reflection is slow — avoid in hot paths
var name = typeof(User).GetProperty("Name")?.GetValue(user);

// CORRECT: Use direct property access when type is known at compile time
var name = user.Name;

// WRONG: Not caching reflection results
foreach (var item in largeCollection)
{
    var prop = item.GetType().GetProperty("Name");  // Reflection every iteration!
    var value = prop?.GetValue(item);
}

// CORRECT: Cache reflection results
var prop = typeof(User).GetProperty("Name");
foreach (var item in largeCollection)
{
    var value = prop?.GetValue(item);
}

// WRONG: Using GetType() on null
object? obj = null;
var type = obj.GetType();  // NullReferenceException!

// CORRECT: Use typeof() or null check
if (obj != null)
{
    var type = obj.GetType();
}

// WRONG: Not specifying BindingFlags correctly
var fields = typeof(MyType).GetFields();  // Only returns public fields!

// CORRECT: Specify binding flags
var allFields = typeof(MyType).GetFields(
    BindingFlags.Public | BindingFlags.NonPublic |
    BindingFlags.Instance | BindingFlags.Static);

// WRONG: Using reflection in performance-critical code
// Reflection is 100-1000x slower than direct access

// CORRECT: Use source generators or expression trees for hot paths
// Source generators create typed code at compile time — zero runtime overhead
```

## Gotchas
- Reflection is SLOW. Cache `PropertyInfo`, `MethodInfo`, `FieldInfo` objects when possible.
- `BindingFlags` are essential. Without them, you only get public instance members.
- `Activator.CreateInstance<T>()` is faster than `Activator.CreateInstance(type)`.
- Source generators (C# 9+) are the compile-time alternative to reflection. They generate code during compilation.
- `System.Text.Json` source generators eliminate runtime reflection for JSON serialization.
- Custom attributes are metadata — they don't DO anything by themselves. You need reflection to read them.
- `AttributeUsage` controls where an attribute can be applied (Class, Property, Method, etc.).
- `AllowMultiple = false` means the attribute can only be applied once per target.
- `MakeGenericType` creates a concrete generic type from an open generic type at runtime.

## Related
- csharp/stdlib/linq-advanced.md
- csharp/stdlib/json-serialization.md
- csharp/web/aspnet-basics.md
