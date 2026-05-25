---
id: "csharp-memory-management"
title: "Memory Management: GC, IDisposable, WeakReference, Object Pooling"
language: "csharp"
category: "stdlib"
tags: ["csharp", "memory", "garbage-collection", "idisposable", "object-pool", "weakreference"]
version: "n/a"
retrieval_hint: "csharp memory management garbage collection IDisposable Dispose pattern finalizer object pooling WeakReference"
last_verified: "2026-05-24"
confidence: "high"
---

# Memory Management: GC, IDisposable, WeakReference, Object Pooling

## When to Use
- Managing unmanaged resources (file handles, sockets, database connections)
- Reducing GC pressure in high-throughput systems
- Implementing custom pooling for expensive objects
- Handling large objects that shouldn't be pinned in memory

## Standard Pattern

```csharp
// === IDisposable Pattern ===

public class ResourceHandler : IDisposable
{
    private IntPtr _nativeResource;  // Unmanaged resource
    private SafeHandle? _managedResource;  // Managed wrapper
    private bool _disposed;

    public ResourceHandler()
    {
        _nativeResource = NativeMethods.AllocateResource();
        _managedResource = new SafeFileHandle(...);
    }

    // Public disposing method
    public void Dispose()
    {
        Dispose(true);
        GC.SuppressFinalize(this);  // Don't run finalizer
    }

    // Protected virtual for inheritance
    protected virtual void Dispose(bool disposing)
    {
        if (_disposed) return;

        if (disposing)
        {
            // Free managed resources (can reference other objects)
            _managedResource?.Dispose();
            _managedResource = null;
        }

        // Free unmanaged resources (can't reference managed objects here)
        if (_nativeResource != IntPtr.Zero)
        {
            NativeMethods.FreeResource(_nativeResource);
            _nativeResource = IntPtr.Zero;
        }

        _disposed = true;
    }

    // Finalizer (only if we have unmanaged resources)
    ~ResourceHandler()
    {
        Dispose(false);  // Only clean up unmanaged resources
    }
}


// === Using Statements ===

// Traditional using block
using (var file = new StreamReader("data.txt"))
{
    string content = file.ReadToEnd();
}  // file.Dispose() called here

// Modern using declaration (C# 8+)
using var reader = new StreamReader("data.txt");
string content = reader.ReadToEnd();
// reader.Dispose() at end of scope


// === WeakReference (avoid preventing GC) ===

// Cache that doesn't prevent collection
public class WeakCache<TKey, TValue>
    where TKey : notnull
    where TValue : class
{
    private readonly Dictionary<TKey, WeakReference<TValue>> _cache = new();

    public void Add(TKey key, TValue value)
    {
        _cache[key] = new WeakReference<TValue>(value);
    }

    public bool TryGet(TKey key, [MaybeNullWhen(false)] out TValue value)
    {
        if (_cache.TryGetValue(key, out var weakRef))
        {
            return weakRef.TryGetTarget(out value);
        }
        value = null;
        return false;
    }

    public void Cleanup()
    {
        // Remove entries where the target was collected
        var dead = _cache
            .Where(kvp => !kvp.Value.TryGetTarget(out _))
            .Select(kvp => kvp.Key)
            .ToList();

        foreach (var key in dead)
            _cache.Remove(key);
    }
}


// === Object Pooling ===

using Microsoft.Extensions.ObjectPool;

public class MyConnection
{
    public string ConnectionId { get; set; } = "";
    public bool IsConnected { get; set; }

    public void Reset()
    {
        // Reset state for reuse
        IsConnected = false;
        ConnectionId = "";
    }
}

public class MyConnectionPooledObjectPolicy : PooledObjectPolicy<MyConnection>
{
    public override MyConnection Create()
    {
        return new MyConnection();
    }

    public override bool Return(MyConnection obj)
    {
        obj.Reset();
        return true;
    }
}

// Registration
// services.AddSingleton<ObjectPool<MyConnection>>(provider =>
// {
//     var policy = new MyConnectionPooledObjectPolicy();
//     return new DefaultObjectPool<MyConnection>(policy);
// });


// === GC Control ===

// Force collection (rarely needed — usually a symptom of poor design)
// GC.Collect();
// GC.WaitForPendingFinalizers();

// Large Object Heap compaction (for LOH fragmentation)
// GCSettings.LargeObjectHeapCompactionMode =
//     GCLargeObjectHeapCompactionMode.CompactOnce;
// GC.Collect();

// Monitor GC stats
// long memoryBefore = GC.GetTotalMemory(false);
// // ... allocate ...
// long memoryAfter = GC.GetTotalMemory(true);  // true = wait for collection

// Gen 0, 1, 2 collection counts
// int gen0 = GC.CollectionCount(0);
// int gen1 = GC.CollectionCount(1);
// int gen2 = GC.CollectionCount(2);
```

## Common Mistakes

```csharp
// WRONG: Not disposing IDisposable objects
var reader = new StreamReader("file.txt");
string line = reader.ReadLine();  // File handle never released!

// CORRECT: Use using
using var reader = new StreamReader("file.txt");
string line = reader.ReadLine();


// WRONG: Finalizer without Dispose (object lives to gen 2)
class BadResource
{
    ~BadResource()
    {
        // Clean up but no Dispose pattern
    }
}

// CORRECT: Implement the full Dispose pattern


// WRONG: SuppressFinalize without calling Dispose
GC.SuppressFinalize(this);  // Should be in Dispose(bool), not constructor!

// CORRECT: Call in Dispose()
public void Dispose()
{
    Dispose(true);
    GC.SuppressFinalize(this);
}


// WRONG: Large object in LOH (> 85KB)
byte[] buffer = new byte[100_000];  // LOH allocation — not compacted!

// CORRECT: Use ArrayPool for temporary large buffers
byte[] buffer = ArrayPool<byte>.Shared.Rent(100_000);
// Return when done
ArrayPool<byte>.Shared.Return(buffer);


// WRONG: Strong references in cache (memory leak)
static List<byte[]> Cache = new();
// Cache.Add(hugeData);  // Never removed — memory leak!

// CORRECT: Use WeakReference or bounded cache with eviction
// e.g., MemoryCache with size limits
// services.AddMemoryCache();


// WRONG: Calling GC.Collect() proactively
GC.Collect();  // Don't! This is a code smell

// CORRECT: Let the GC manage itself
// Profile and fix allocation patterns instead of forcing collections
```

## Gotchas
- **Finalizer thread**: Finalizers run on a dedicated thread. If a finalizer blocks, NO other finalizers will run, and the finalizer queue grows unbounded. Never block in finalizers (no locks, no I/O, no sleeps).
- **LOH fragmentation**: Arrays > 85KB go to the Large Object Heap. The LOH is not compacted by default in .NET Framework (compacted in .NET Core 3+ with `GCSettings.LargeObjectHeapCompactionMode`). Fragmentation can cause OutOfMemory even with free space.
- **GC modes**: Server GC uses one heap per core for better throughput but more memory. Workstation GC is for client apps. Configure in `.csproj`: `<ServerGarbageCollection>true</ServerGarbageCollection>`.
- **Pinning and GC holes**: Pinning an object (via `fixed` or `GCHandle.Alloc(obj, GCHandleType.Pinned)`) prevents the GC from moving it, causing heap fragmentation. Minimize pinning duration and count.
- **Async and GC**: Each `async` method creates a state machine struct. In hot paths, this allocation pressure adds up. Use `ValueTask` instead of `Task` for synchronous-completion hot paths to avoid allocation.
- **ConditionalWeakTable**: Use `ConditionalWeakTable<TKey, TValue>` for attaching data to objects without preventing their collection. Unlike `Dictionary`, keys are weak references with automatic cleanup.
- **GC notifications**: For server applications, use `GC.RegisterForFullGCNotification` to implement proactive load shedding before blocking Gen 2 collections occur.

## Related
- csharp/stdlib/performance.md
- csharp/stdlib/async-await.md
- csharp/stdlib/dependency-injection.md
