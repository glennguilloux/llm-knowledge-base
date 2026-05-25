---
id: "csharp-stdlib-collections"
title: "Collections and LINQ in C#"
language: "csharp"
category: "stdlib"
tags: ["csharp", "dotnet", "collections", "list", "dictionary", "linq", "ienumerable"]
version: ".NET 8+"
retrieval_hint: "C# List Dictionary HashSet LINQ Where Select ToList collection initialization"
last_verified: "2026-05-24"
confidence: "high"
---

# Collections and LINQ in C#

## When to Use
- `List<T>` for mutable collections with index access (most common collection)
- `Dictionary<K,V>` for key-value lookups by unique key
- `HashSet<T>` for uniqueness guarantees and set operations (union, intersect)
- LINQ (`Where`, `Select`, `OrderBy`, etc.) for declarative data transformation
- `IReadOnlyList<T>` for exposing collections that callers should not modify
- Collection initializers (`new List<T> { a, b }`) for concise inline initialization

## Standard Pattern

```csharp
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;

public static class CollectionExamples
{
    // List<T> — the default mutable collection
    public static List<int> FilterAndTransform(IEnumerable<int> source)
    {
        // LINQ with deferred execution — nothing runs until enumerated
        var query = source
            .Where(x => x > 0)
            .Select(x => x * 2);
        // Force evaluation with ToList
        return query.ToList();
    }

    // Dictionary<K,V> — key-value lookup
    public static Dictionary<string, int> CountWords(IEnumerable<string> words)
    {
        var counts = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);
        foreach (var word in words)
        {
            if (word is null) continue;
            counts.TryGetValue(word, out int current);
            counts[word] = current + 1;
        }
        return counts;
    }

    // HashSet<T> — uniqueness and set operations
    public static HashSet<T> GetCommonItems<T>(IEnumerable<T> a, IEnumerable<T> b)
    {
        var setA = new HashSet<T>(a);
        var setA.IntersectWith(b);  // Mutates setA in place
        return setA;
    }

    // IReadOnlyList<T> — expose without allowing modification
    public class ProductCatalog
    {
        private readonly List<Product> _products = new();

        // Expose as read-only to callers
        public IReadOnlyList<Product> Products => _products.AsReadOnly();

        public void AddProduct(Product product) => _products.Add(product);
    }

    // Collection initializer syntax
    public static List<string> GetDefaultTags() =>
        new() { "csharp", "dotnet", "stdlib" };

    // Manual LINQ-style loop (when LINQ overhead matters)
    public static List<int> ManualFilter(int[] source)
    {
        var result = new List<int>();
        foreach (var item in source)
        {
            if (item > 10)
                result.Add(item);
        }
        return result;
    }
}

public class Product { public int Id { get; set; } public string Name { get; set; } = ""; }
```

## Common Mistakes

```csharp
// WRONG: Modifying a collection during foreach iteration
foreach (var item in list)
{
    if (item.IsDeprecated)
        list.Remove(item);  // InvalidOperationException: Collection was modified
}

// CORRECT: Use RemoveAll or collect items first, then remove
list.RemoveAll(item => item.IsDeprecated);
// Or: iterate a copy
foreach (var item in list.ToList())
{
    if (item.IsDeprecated)
        list.Remove(item);
}

// WRONG: Accessing a missing dictionary key throws KeyNotFoundException
var value = dict["missingKey"];

// CORRECT: Use TryGetValue or TryAdd
if (dict.TryGetValue("key", out var value)) { /* use value */ }
// Or for .NET 6+ additions:
dict.TryAdd("key", defaultValue);

// WRONG: Enumerating a LINQ query multiple times (deferred execution)
var query = items.Where(x => x > 0);
int count = query.Count();  // Enumerates all items
var list = query.ToList();  // Enumerates all items again

// CORRECT: Materialize once with ToList
var results = items.Where(x => x > 0).ToList();
int count = results.Count;  // Uses List.Count property — no re-enumeration
var list = results;         // Same list, no extra work

// WRONG: Using FindAll on IEnumerable (it's a List<T> method, not LINQ)
IEnumerable<int> data = GetItems();
var found = data.FindAll(x => x > 10);  // Compile error

// CORRECT: Use Where for IEnumerable, FindAll for List<T>
var found = data.Where(x => x > 10).ToList();

// WRONG: Assuming Dictionary preserves insertion order (pre-.NET 6)
// In older .NET, iteration order is undefined

// CORRECT: In .NET 6+ Dictionary preserves insertion order, but use SortedDictionary
// if you need guaranteed ordering — don't rely on it as a contract in shared code
```

## Gotchas
- LINQ uses deferred execution — `Where(...)` doesn't run until you iterate; calling `ToList()` or `Count()` forces evaluation
- `IReadOnlyList<T>` is NOT a guarantee of immutability — the underlying collection can still be modified by the owner; use `ImmutableList<T>` for true immutability
- `Dictionary<K,V>` uses the default `IEqualityComparer<K>`; for string keys, explicitly pass `StringComparer.OrdinalIgnoreCase` to avoid case-sensitive surprises
- `HashSet<T>.RemoveWhere`, `IntersectWith`, and `ExceptWith` mutate the set in place — they do not return a new `HashSet<T>`
- `AddRange` on `List<T>` is more efficient than adding items one-by-one in a loop because it can resize the internal array once
- LINQ queries capture variables by reference — changing a variable after defining a query changes the query results (closure behavior)
- `AsReadOnly()` returns a `ReadOnlyCollection<T>` wrapper that reflects live changes to the underlying list — it is a view, not a snapshot

## Related
- csharp/stdlib/linq.md
- csharp/stdlib/string-operations.md
- csharp/stdlib/enums.md
