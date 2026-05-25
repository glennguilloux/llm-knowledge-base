---
id: "csharp-performance"
title: "C# Performance: Span, Memory, Allocation, Benchmarking"
language: "csharp"
category: "stdlib"
tags: ["csharp", "performance", "span", "memory", "benchmark", "allocation", "ref-struct"]
version: "n/a"
retrieval_hint: "csharp performance Span Memory allocation optimization BenchmarkDotNet Span<T> ReadOnlySpan"
last_verified: "2026-05-24"
confidence: "high"
---

# C# Performance: Span, Memory, Allocation, Benchmarking

## When to Use
- Writing high-performance C# code (game servers, processing pipelines)
- Reducing garbage collection pressure in hot paths
- Working with raw memory buffers efficiently
- Measuring and validating performance changes

## Standard Pattern

```csharp
// === Span<T> and ReadOnlySpan<T> (stack-allocated slices) ===

// Creating spans
int[] array = [1, 2, 3, 4, 5, 6, 7, 8];
Span<int> span = array.AsSpan();
Span<int> slice = array.AsSpan(2, 3);  // [3, 4, 5]

// Stack allocation
Span<byte> buffer = stackalloc byte[256];

// Modification without allocation
void ProcessValues(Span<int> values)
{
    for (int i = 0; i < values.Length; i++)
    {
        values[i] *= 2;  // Modifies the original array!
    }
}

// ReadOnlySpan — for read-only access
ReadOnlySpan<char> text = "hello world".AsSpan();
ReadOnlySpan<char> hello = text[..5];  // Slice without allocation


// === Memory<T> — heap-friendly Span ===

// Memory<T> can be stored in fields and used across async
private Memory<byte> _buffer;

async Task ProcessStream(Stream stream)
{
    Memory<byte> buffer = new byte[8192];
    int bytesRead = await stream.ReadAsync(buffer);
    // Use buffer.Span for synchronous operations
    ProcessBytes(buffer.Span[..bytesRead]);
}

void ProcessBytes(Span<byte> data)
{
    // Zero-allocation processing
}


// === ref struct (stack-only type) ===

// Cannot be boxed, used in async, or stored on heap
ref struct FastParser
{
    private ReadOnlySpan<char> _text;

    public FastParser(ReadOnlySpan<char> text)
    {
        _text = text;
    }

    public int ParseNextInt()
    {
        // Parse without allocations
        int end = _text.IndexOf(',');
        if (end < 0) end = _text.Length;

        int result = 0;
        for (int i = 0; i < end; i++)
        {
            result = result * 10 + (_text[i] - '0');
        }

        _text = _text[(end + 1)..];
        return result;
    }
}


// === struct vs class (avoid heap allocation) ===

// Use readonly struct for small, immutable data
readonly struct Point
{
    public int X { get; }
    public int Y { get; }

    public Point(int x, int y) => (X, Y) = (x, y);
}


// === StringBuilder for string concatenation ===

// Bad: creates N intermediate strings
string result = "";
for (int i = 0; i < 1000; i++)
    result += i.ToString();  // 1000 allocations!

// Good: single buffer
var sb = new StringBuilder(capacity: 4000);
for (int i = 0; i < 1000; i++)
    sb.Append(i);
string result = sb.ToString();


// === ArrayPool — reuse temporary arrays ===

using System.Buffers;

byte[]? rented = null;
try
{
    rented = ArrayPool<byte>.Shared.Rent(4096);

    // Use the array
    int length = await stream.ReadAsync(rented);
    ProcessBytes(rented.AsSpan(0, length));
}
finally
{
    if (rented != null)
        ArrayPool<byte>.Shared.Return(rented);
}

// Or better: use using pattern with a helper
using var owner = MemoryPool<byte>.Shared.Rent(4096);
// owner.Memory.Span


// === BenchmarkDotNet ===

// Install: dotnet add package BenchmarkDotNet

// [MemoryDiagnoser]  // Track allocations
// [SimpleJob(RunStrategy.ColdStart, iterationCount: 5)]
public class StringBenchmarks
{
    private readonly string[] _data =
        Enumerable.Range(0, 1000).Select(i => $"value_{i}").ToArray();

    [Benchmark(Baseline = true)]
    public string StringBuilder()
    {
        var sb = new StringBuilder();
        foreach (var item in _data)
            sb.Append(item).Append(',');
        return sb.ToString();
    }

    [Benchmark]
    public string StringJoin()
    {
        return string.Join(",", _data);
    }
}

// Run: BenchmarkRunner.Run<StringBenchmarks>();
```

## Common Mistakes

```csharp
// WRONG: Allocation in hot path (string concat in loop)
string csv = "";
foreach (var item in items)
    csv += item + ",";  // O(n²) allocations!

// CORRECT: Use StringBuilder or string.Join
string csv = string.Join(",", items);


// WRONG: LINQ allocations in hot code
var filtered = items
    .Where(x => x.IsActive)
    .Select(x => x.Name)
    .ToList();

// CORRECT: Use for-loop for hot paths (no iterator allocations)
var names = new List<string>(items.Count);
for (int i = 0; i < items.Count; i++)
{
    if (items[i].IsActive)
        names.Add(items[i].Name);
}


// WRONG: Boxing value types in hot code
interface IProcessor { void Process(); }
struct FastProcessor : IProcessor { public void Process() { } }
// ((IProcessor)processor).Process();  // Boxes the struct!

// CORRECT: Use generic constraints
void Process<T>(T processor) where T : IProcessor
{
    processor.Process();  // No boxing
}


// WRONG: async over sync (allocates state machine)
public async Task<int> GetValueAsync() => Compute();  // Unnecessary async

// CORRECT: Return Task directly
public Task<int> GetValueAsync() => Task.FromResult(Compute());
// Or use ValueTask for hot paths
public ValueTask<int> GetValueAsync() => new(Compute());


// WRONG: Not using ArrayPool for large temporary arrays
byte[] buffer = new byte[65536];  // LOH allocation!
// CORRECT: Rent from pool
byte[] buffer = ArrayPool<byte>.Shared.Rent(65536);
```

## Gotchas
- **Span<T> limitations**: `Span<T>` is a `ref struct` — it cannot be used as a field in a class, in async methods, in iterators (yield), or as a generic type argument. Use `Memory<T>` when you need these capabilities.
- **struct copy semantics**: Passing a large `readonly struct` by value copies all fields. Use `in` parameter modifier for read-only reference: `void Process(in LargeStruct data)`. Add `readonly` to struct methods to avoid defensive copies.
- **GC latency**: In high-throughput servers, allocation rate directly affects GC pauses. Use `ArrayPool`, object pooling, and value types to reduce Gen 2 collections. Monitor with `dotnet-counters` and ETW events.
- **JIT intrinsics and SIMD**: `System.Numerics.Vector<T>` and `System.Runtime.Intrinsics` provide hardware-accelerated operations. Use `Vector.IsHardwareAccelerated` to check support at runtime.
- **StringComparison ordinal**: Default string comparisons use culture-sensitive rules (slower). Use `StringComparison.Ordinal` or `StringComparison.OrdinalIgnoreCase` for internal/programmatic comparisons.
- **ConcurrentDictionary overhead**: `ConcurrentDictionary` has significant overhead for single-writer scenarios. Use `Dictionary<TKey, TValue>` with locking for read-heavy, single-writer patterns.
- **dotnet-counters vs BenchmarkDotNet**: Use `dotnet-counters` for production profiling (allocation rate, GC heap) and BenchmarkDotNet for microbenchmarks. Never guess about performance — always measure with realistic data.

## Related
- csharp/stdlib/memory-management.md
- csharp/stdlib/async-await.md
- csharp/stdlib/collections.md
