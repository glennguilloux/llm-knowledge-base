---
id: "antipatterns-csharp"
title: "C# Anti-Patterns"
language: "csharp"
category: "anti-patterns"
tags: ["antipatterns", "csharp", "dotnet", "async", "common-mistakes"]
version: "n/a"
retrieval_hint: "csharp common mistakes async void deadlock IDisposable LINQ side effects"
last_verified: "2026-05-22"
confidence: "high"
---

# C# Anti-Patterns

## When to Use
- Reviewing C# code for common mistakes
- Training small LLMs to avoid frequent C# errors
- Code review checklists for .NET applications
- Onboarding developers new to C# or .NET

## Standard Pattern

```csharp
// WRONG: async void (exceptions crash the process, can't await)
public async void SaveData()
{
    await File.WriteAllTextAsync("data.txt", content);  // Unhandled exception kills app
}

// CORRECT: async Task (exceptions propagate to caller)
public async Task SaveDataAsync()
{
    await File.WriteAllTextAsync("data.txt", content);
}

// WRONG: .Result on Task (deadlocks in ASP.NET/WinForms)
var user = GetUserAsync().Result;  // Blocks thread, can deadlock

// CORRECT: await the task
var user = await GetUserAsync();

// WRONG: Catching generic Exception (hides bugs)
try
{
    ProcessOrder(order);
}
catch (Exception ex)
{
    // Swallows ArgumentException, NullReferenceException, everything
    Log(ex);
}

// CORRECT: Catch specific exceptions
try
{
    ProcessOrder(order);
}
catch (OrderNotFoundException ex)
{
    return NotFound(ex.Message);
}
catch (InsufficientInventoryException ex)
{
    return BadRequest(ex.Message);
}

// WRONG: String concatenation in loop (allocates new string each iteration)
string result = "";
foreach (var item in items)
{
    result += item.Name + ", ";  // O(n^2) allocations
}

// CORRECT: Use StringBuilder
var sb = new StringBuilder();
foreach (var item in items)
{
    sb.Append(item.Name).Append(", ");
}
string result = sb.ToString();

// WRONG: LINQ for side effects (creates unused list)
items.Select(x => { Console.WriteLine(x); return x; }).ToList();

// CORRECT: Use foreach for side effects
foreach (var item in items)
{
    Console.WriteLine(item);
}

// WRONG: Not disposing IDisposable (resource leak)
var stream = new FileStream("data.txt", FileMode.Open);
var bytes = new byte[stream.Length];
stream.Read(bytes, 0, bytes.Length);
// stream never closed — file handle leaked

// CORRECT: Use using statement
using var stream = new FileStream("data.txt", FileMode.Open);
var bytes = new byte[stream.Length];
stream.Read(bytes, 0, bytes.Length);

// WRONG: God class with 20+ responsibilities
public class OrderManager
{
    public void CreateOrder() { }
    public void CancelOrder() { }
    public void SendEmail() { }
    public void GenerateInvoice() { }
    public void UpdateInventory() { }
    public void ProcessPayment() { }
    public void LogActivity() { }
    // ... 15 more methods
}

// CORRECT: Single Responsibility Principle
public class OrderService { public void Create() { } }
public class EmailService { public void Send() { } }
public class InvoiceService { public void Generate() { } }

// WRONG: Null reference without check
string name = user.Profile.Name;  // NullReferenceException if Profile is null

// CORRECT: Null-conditional operator
string name = user?.Profile?.Name ?? "Unknown";
```

## Common Mistakes
The most damaging C# anti-patterns are `async void` (unhandled exceptions crash the process), `.Result` on Tasks (deadlocks UI and ASP.NET contexts), and catching generic `Exception` (hides real bugs). String concatenation in loops causes O(n^2) memory allocations. Not disposing `IDisposable` resources leaks file handles and database connections.

## Gotchas
- `async void` is only acceptable for event handlers — everywhere else use `async Task`
- `.Result` and `.Wait()` block the calling thread and can deadlock if a synchronization context exists
- `catch (Exception)` catches `OutOfMemoryException` and `StackOverflowException` — always catch specific types
- LINQ is for transformations, not side effects — use `foreach` when you don't need the return value
- `StringBuilder` is only faster for 3+ concatenations — for 2-3, `+` is fine
- `using var` (C# 8+) auto-disposes at end of scope — no need for explicit `Dispose()` call
- Record types are immutable by default; classes are mutable — prefer records for DTOs

## Related
- csharp/web/aspnet-middleware.md
- csharp/stdlib/async-await.md
- error-handling/structured-errors.md
- anti-patterns/performance-antipatterns.md
