---
id: "csharp-stdlib-async-await"
title: "Async/Await Patterns in C#"
language: "csharp"
category: "stdlib"
tags: ["csharp", "dotnet", "async", "await", "task", "concurrency"]
version: ".NET 8+"
retrieval_hint: "C# async await Task concurrency parallel cancellation"
last_verified: "2026-05-22"
confidence: "high"
---

# Async/Await Patterns in C#

## When to Use
- I/O-bound operations (HTTP requests, database queries, file I/O)
- Keeping UI responsive in desktop/mobile apps
- Building scalable web services (ASP.NET Core)
- Long-running operations that should not block the calling thread

## Standard Pattern

```csharp
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;

// Basic async method
public async Task<User> GetUserAsync(int id, CancellationToken ct = default)
{
    var response = await _httpClient.GetAsync($"/api/users/{id}", ct);
    response.EnsureSuccessStatusCode();
    var json = await response.Content.ReadAsStringAsync(ct);
    return JsonSerializer.Deserialize<User>(json)!;
}

// Parallel execution with Task.WhenAll
public async Task<List<User>> GetUsersAsync(IEnumerable<int> ids, CancellationToken ct)
{
    var tasks = ids.Select(id => GetUserAsync(id, ct));
    var users = await Task.WhenAll(tasks);
    return users.ToList();
}

// WhenAny for first-completed
public async Task<string> GetFastestResponseAsync(IEnumerable<string> urls, CancellationToken ct)
{
    var tasks = urls.Select(url => _httpClient.GetStringAsync(url, ct));
    var first = await await Task.WhenAny(tasks);
    return first;
}

// ValueTask for hot-path synchronous completion
public async ValueTask<int> GetValueAsync(int key)
{
    if (_cache.TryGetValue(key, out var cached))
        return cached;  // Synchronous path — no Task allocation

    return await FetchFromDatabaseAsync(key);
}

// Cancellation token propagation
public async Task ProcessItemsAsync(IAsyncEnumerable<Item> items, CancellationToken ct)
{
    await foreach (var item in items.WithCancellation(ct))
    {
        ct.ThrowIfCancellationRequested();
        await ProcessItemAsync(item, ct);
    }
}

// ConfigureAwait for library code
public async Task<string> GetDataAsync()
{
    var data = await _httpClient.GetStringAsync("/api/data").ConfigureAwait(false);
    // No synchronization context captured — safe for library code
    return data.ToUpper();
}

public class User { public int Id { get; set; } public string Name { get; set; } = ""; }
public class Item { }
```

## Common Mistakes

```csharp
// WRONG: async void (exceptions crash the process)
public async void HandleClick()  // Fire-and-forget — unobserved exceptions
{
    await SaveDataAsync();
}

// CORRECT: async Task (exceptions are observable)
public async Task HandleClickAsync()
{
    await SaveDataAsync();
}

// WRONG: .Result or .Wait() (deadlock in UI/ASP.NET contexts)
var data = GetDataAsync().Result;  // Blocks thread — deadlock risk

// CORRECT: await all the way
var data = await GetDataAsync();

// WRONG: Not propagating CancellationToken
public async Task ProcessAsync()  // No way to cancel
{
    await _httpClient.GetAsync("/api/data");
}

// CORRECT: Accept and propagate CancellationToken
public async Task ProcessAsync(CancellationToken ct = default)
{
    await _httpClient.GetAsync("/api/data", ct);
}

// WRONG: Task.Run for I/O-bound work
var data = await Task.Run(() => _httpClient.GetStringAsync(url));  // Wastes thread pool thread

// CORRECT: Just await directly
var data = await _httpClient.GetStringAsync(url);

// WRONG: Not disposing HttpClient
public async Task GetDataAsync()
{
    var client = new HttpClient();  // Socket exhaustion
    return await client.GetStringAsync("https://api.example.com");
}

// CORRECT: Use IHttpClientFactory
public async Task GetDataAsync()
{
    var client = _httpClientFactory.CreateClient("api");
    return await client.GetStringAsync("https://api.example.com");
}
```

## Gotchas
- `async void` is only valid for event handlers — always use `async Task` otherwise
- `.Result` and `.Wait()` block the calling thread and can deadlock with synchronization contexts
- `ConfigureAwait(false)` is recommended in library code to avoid capturing the sync context
- `Task.WhenAll` runs tasks concurrently, not in parallel — use `Parallel.ForEachAsync` for CPU-bound work
- `ValueTask` avoids `Task` allocation when the result is often available synchronously
- `CancellationToken` must be passed through every async call for effective cancellation
- Unobserved `Task` exceptions are silently swallowed by default — use `TaskScheduler.UnobservedTaskException`
- `IAsyncDisposable` is needed for async cleanup — use `await using` pattern
- Always use the async overload of HTTP/DB methods — sync versions block threads

## Related
- csharp/stdlib/dependency-injection.md
- csharp/web/aspnet-basics.md
- csharp/testing/testing.md
