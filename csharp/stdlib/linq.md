---
id: "csharp-stdlib-linq"
title: "LINQ Patterns and Best Practices"
language: "csharp"
category: "stdlib"
tags: ["csharp", "dotnet", "linq", "query", "collections", "enumerable"]
version: ".NET 8+"
retrieval_hint: "C# LINQ query lambda Select Where GroupBy OrderBy IEnumerable"
last_verified: "2026-05-22"
confidence: "high"
---

# LINQ Patterns and Best Practices

## When to Use
- Querying and transforming collections
- Filtering, sorting, and grouping data
- Joining multiple data sources
- Aggregating data (sum, count, average)

## Standard Pattern

```csharp
using System;
using System.Collections.Generic;
using System.Linq;

// Method syntax (preferred for simple queries)
var activeUsers = users
    .Where(u => u.IsActive)
    .OrderBy(u => u.LastName)
    .ThenBy(u => u.FirstName)
    .Select(u => new { u.Id, FullName = $"{u.FirstName} {u.LastName}" })
    .ToList();

// Query syntax (better for joins)
var query = from u in users
            join o in orders on u.Id equals o.UserId
            where u.IsActive
            orderby o.OrderDate descending
            select new { u.Name, o.OrderDate, o.Total };

// GroupBy
var usersByDepartment = users
    .GroupBy(u => u.Department)
    .Select(g => new { Department = g.Key, Count = g.Count(), Users = g.ToList() })
    .OrderByDescending(g => g.Count);

// Aggregate operations
var totalRevenue = orders.Sum(o => o.Total);
var averageAge = users.Average(u => u.Age);
var hasAdmin = users.Any(u => u.Role == "Admin");
var allActive = users.All(u => u.IsActive);
var userCount = users.Count(u => u.IsActive);

// First/Single with safety
var user = users.FirstOrDefault(u => u.Id == id);  // null if not found
var exact = users.SingleOrDefault(u => u.Email == email);  // null or throws if multiple

// ToDictionary / ToLookup
var userDict = users.ToDictionary(u => u.Id);
var usersByDept = users.ToLookup(u => u.Department);  // ILookup — groups

// SelectMany (flatten nested collections)
var allTags = posts.SelectMany(p => p.Tags).Distinct().OrderBy(t => t);

// Zip (combine two sequences)
var names = new[] { "Alice", "Bob" };
var ages = new[] { 30, 25 };
var people = names.Zip(ages, (name, age) => new { Name = name, Age = age });

// Chunk (batch processing)
foreach (var batch in items.Chunk(100))
{
    await BulkInsertAsync(batch);
}

public class User
{
    public int Id { get; set; }
    public string FirstName { get; set; } = "";
    public string LastName { get; set; } = "";
    public string Department { get; set; } = "";
    public bool IsActive { get; set; }
    public int Age { get; set; }
    public string Email { get; set; } = "";
    public string Role { get; set; } = "";
}
public class Order { public int UserId { get; set; } public DateTime OrderDate { get; set; } public decimal Total { get; set; } }
public class Post { public List<string> Tags { get; set; } = new(); }
```

## Common Mistakes

```csharp
// WRONG: Multiple enumeration (expensive query executed twice)
var expensive = users.Where(u => u.IsActive).ToList();
var count = expensive.Count();  // OK — already materialized

var expensive2 = db.Users.Where(u => u.IsActive);  // IQueryable — not yet executed
var count2 = expensive2.Count();  // Hits DB
var list2 = expensive2.ToList();  // Hits DB AGAIN

// CORRECT: Materialize once if reusing
var activeUsers = db.Users.Where(u => u.IsActive).ToList();  // Single DB call

// WRONG: Using == for sequence comparison
if (list1 == list2)  // Reference equality, not content

// CORRECT: Use SequenceEqual
if (list1.SequenceEqual(list2))

// WRONG: .ToList() unnecessarily (materializes into memory)
var names = users.Select(u => u.Name).ToList();  // If only iterating once
foreach (var name in names) { }

// CORRECT: Keep as IEnumerable if only iterating once
var names = users.Select(u => u.Name);  // Deferred execution
foreach (var name in names) { }

// WRONG: Catching exceptions in LINQ predicates
users.Where(u => { try { return u.IsActive; } catch { return false; } })

// CORRECT: Handle errors outside LINQ
var safeUsers = users.Where(u => u.IsActive);

// WRONG: Modifying collection during LINQ query
var results = list.Where(x => { list.Add(x * 2); return true; });  // Undefined behavior

// CORRECT: Materialize first, then modify
var filtered = list.Where(x => x > 5).ToList();
```

## Gotchas
- LINQ uses deferred execution — queries are not evaluated until enumerated
- `IEnumerable<T>` is lazy; `IList<T>` and `List<T>` are eager (already evaluated)
- `IQueryable<T>` translates to SQL (Entity Framework); `IEnumerable<T>` runs in memory
- Each enumeration of `IEnumerable` re-evaluates the query — materialize with `.ToList()` if reusing
- `First()` throws if empty; `FirstOrDefault()` returns `default(T)` — prefer `FirstOrDefault` for safety
- `Single()` throws if zero or multiple matches; `SingleOrDefault()` returns null if empty
- `OrderBy` + `ThenBy` for multi-key sorting; `OrderByDescending` for descending
- `SelectMany` flattens nested collections; `Select` preserves structure
- `Any()` is more efficient than `Count() > 0` for existence checks (short-circuits)
- `Concat` joins sequences; `Union` joins and deduplicates

## Related
- csharp/stdlib/async-await.md
- csharp/db/entity-framework.md
- csharp/stdlib/dependency-injection.md
