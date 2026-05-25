---
id: "csharp-stdlib-async-advanced"
title: "Advanced C# Async: Task.WhenAll, CancellationToken, and Async Streams"
language: "csharp"
category: "stdlib"
tags: ["csharp", "async", "Task.WhenAll", "CancellationToken", "ValueTask", "IAsyncEnumerable", "deadlocks"]
version: ".NET 8+"
retrieval_hint: "csharp async advanced Task.WhenAll Task.WhenAny CancellationToken ConfigureAwait ValueTask async streams IAsyncEnumerable"
last_verified: "2026-05-24"
confidence: "high"
---

# Advanced C# Async: Task.WhenAll, CancellationToken, and Async Streams

## When to Use
- Running multiple async operations concurrently
- Cancelling long-running operations with CancellationToken
- Using ValueTask for performance-critical paths
- Streaming data with IAsyncEnumerable
- Avoiding async deadlocks

## Standard Pattern

```csharp
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

// Task.WhenAll — run multiple tasks concurrently
async Task<UserData> LoadDashboardAsync(int userId)
{
    var userTask = FetchUserAsync(userId);
    var ordersTask = FetchOrdersAsync(userId);
    var notificationsTask = FetchNotificationsAsync(userId);

    // All three run concurrently
    await Task.WhenAll(userTask, ordersTask, notificationsTask);

    return new UserData
    {
        User = await userTask,
        Orders = await ordersTask,
        Notifications = await notificationsTask
    };
}

// Task.WhenAll with results (simpler)
async Task<UserData> LoadDashboardAsync(int userId)
{
    var users = await FetchUserAsync(userId);
    var orders = await FetchOrdersAsync(userId);
    var notifications = await FetchNotificationsAsync(userId);
    return new UserData { User = users, Orders = orders, Notifications = notifications };
}

// Task.WhenAny — wait for first task to complete
async Task<string> FetchFastestAsync()
{
    var task1 = FetchFromSource1Async();
    var task2 = FetchFromSource2Async();
    var task3 = FetchFromSource3Async();

    var completed = await Task.WhenAny(task1, task2, task3);
    return await completed;
}

// CancellationToken — cancel long-running operations
async Task<List<User>> FetchAllUsersAsync(CancellationToken ct)
{
    var users = new List<User>();
    string? cursor = null;

    do
    {
        ct.ThrowIfCancellationRequested();  // Check before each batch

        var batch = await api.FetchUsersAsync(cursor, ct);  // Pass token to API
        users.AddRange(batch.Items);
        cursor = batch.NextCursor;

    } while (cursor != null);

    return users;
}

// Using CancellationTokenSource
using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(30));
try
{
    var users = await FetchAllUsersAsync(cts.Token);
}
catch (OperationCanceledException)
{
    Console.WriteLine("Operation was cancelled");
}

// ConfigureAwait(false) — avoid deadlocks in library code
async Task<User> FetchUserAsync(int id)
{
    var response = await httpClient.GetAsync($"/users/{id}")
        .ConfigureAwait(false);  // Don't capture SynchronizationContext

    var json = await response.Content.ReadAsStringAsync()
        .ConfigureAwait(false);

    return JsonSerializer.Deserialize<User>(json);
}

// ValueTask — avoid Task allocation for synchronous paths
private static readonly Dictionary<int, User> _cache = new();

async ValueTask<User> GetUserAsync(int id)
{
    if (_cache.TryGetValue(id, out var cached))
        return cached;  // No Task allocation!

    var user = await FetchFromDbAsync(id);
    _cache[id] = user;
    return user;
}

// IAsyncEnumerable — async streams (C# 8.0+)
async IAsyncEnumerable<LogEntry> StreamLogsAsync(
    [EnumeratorCancellation] CancellationToken ct = default)
{
    await foreach (var batch in api.FetchLogBatchesAsync(ct))
    {
        foreach (var entry in batch)
        {
            ct.ThrowIfCancellationRequested();
            yield return entry;
        }
    }
}

// Consuming IAsyncEnumerable
async Task ProcessLogsAsync()
{
    await foreach (var entry in StreamLogsAsync())
    {
        Console.WriteLine(entry.Message);
    }
}

// IAsyncEnumerable with cancellation
async Task ProcessWithTimeoutAsync()
{
    using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(10));
    try
    {
        await foreach (var entry in StreamLogsAsync(cts.Token))
        {
            Process(entry);
        }
    }
    catch (OperationCanceledException)
    {
        Console.WriteLine("Timed out");
    }
}

// Parallel.ForEachAsync (.NET 6+)
async Task ProcessAllUsersAsync(IEnumerable<int> userIds)
{
    await Parallel.ForEachAsync(userIds, new ParallelOptions
    {
        MaxDegreeOfParallelism = 10,
        CancellationToken = CancellationToken.None
    }, async (id, ct) =>
    {
        var user = await FetchUserAsync(id);
        await ProcessUserAsync(user);
    });
}

// Avoiding async deadlocks
// WRONG: .Result or .Wait() on UI thread causes deadlock
// var user = FetchUserAsync(1).Result;  // DEADLOCK!

// CORRECT: Use await all the way
// var user = await FetchUserAsync(1);
```

## Common Mistakes

```csharp
// WRONG: Using .Result or .Wait() — causes deadlocks on UI thread
var user = FetchUserAsync(1).Result;  // DEADLOCK in UI/ASP.NET Classic!

// CORRECT: Use await all the way
var user = await FetchUserAsync(1);

// WRONG: Not passing CancellationToken to async methods
async Task<List<User>> FetchAllUsersAsync()
{
    // No way to cancel this!
    return await db.Users.ToListAsync();
}

// CORRECT: Accept and pass CancellationToken
async Task<List<User>> FetchAllUsersAsync(CancellationToken ct)
{
    return await db.Users.ToListAsync(ct);
}

// WRONG: async void (only use for event handlers)
async void Button_Click(object sender, EventArgs e)
{
    await FetchDataAsync();  // Exceptions are lost!
}

// CORRECT: Use async Task for methods
async Task Button_ClickAsync()
{
    await FetchDataAsync();
}

// WRONG: Not using ConfigureAwait(false) in library code
async Task<User> LibraryMethodAsync()
{
    var response = await httpClient.GetAsync(url);
    // Captures SynchronizationContext — may deadlock in some scenarios
}

// CORRECT: Use ConfigureAwait(false) in library code
async Task<User> LibraryMethodAsync()
{
    var response = await httpClient.GetAsync(url).ConfigureAwait(false);
}

// WRONG: Fire-and-forget without handling exceptions
_ = FetchDataAsync();  // Exception is silently lost!

// CORCORD: Handle exceptions in fire-and-forget
_ = FetchDataAsync().ContinueWith(t =>
{
    if (t.IsFaulted) logger.Error(t.Exception);
}, TaskContinuationOptions.OnlyOnFaulted);
```

## Gotchas
- `Task.WhenAll` waits for ALL tasks. If one fails, the exception is aggregated in `AggregateException`.
- `Task.WhenAny` returns the first completed task (could be faulted or cancelled).
- `CancellationToken` must be passed through the entire call chain. Check `ct.ThrowIfCancellationRequested()` in loops.
- `ConfigureAwait(false)` prevents capturing the SynchronizationContext. Use in library code, NOT in UI event handlers.
- `ValueTask<T>` avoids `Task` allocation when the result is available synchronously. Don't await it multiple times.
- `IAsyncEnumerable<T>` is the async equivalent of `IEnumerable<T>`. Use `await foreach` to consume.
- `async void` should ONLY be used for event handlers. Exceptions in `async void` crash the process.
- `Parallel.ForEachAsync` (.NET 6+) is the async equivalent of `Parallel.ForEach`.
- Never use `.Result` or `.Wait()` on the UI thread — it causes deadlocks.

## Related
- csharp/stdlib/linq-advanced.md
- csharp/stdlib/linq.md
- csharp/stdlib/error-handling.md
