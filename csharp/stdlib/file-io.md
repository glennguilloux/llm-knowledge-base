---
id: "csharp-stdlib-file-io"
title: "C# File I/O: File, Stream, Async Operations, and Path"
language: "csharp"
category: "stdlib"
tags: ["csharp", "file-io", "File", "StreamReader", "async", "Path", "DirectoryInfo"]
version: ".NET 8+"
retrieval_hint: "csharp File class StreamReader Writer async file operations Path class DirectoryInfo FileInfo"
last_verified: "2026-05-24"
confidence: "high"
---

# C# File I/O: File, Stream, Async Operations, and Path

## When to Use
- Reading and writing files in C#
- Working with file streams for large files
- Using async file operations for responsiveness
- Manipulating file paths and directory information

## Standard Pattern

```csharp
using System;
using System.IO;
using System.Threading.Tasks;

// Simple file read/write
string content = File.ReadAllText("config.json");
File.WriteAllText("output.txt", "Hello, World!");
File.AppendAllText("log.txt", "New entry
");

// Read all lines
string[] lines = File.ReadAllLines("data.csv");
File.WriteAllLines("output.txt", lines);

// Async file operations (preferred for I/O-bound work)
async Task<string> ReadConfigAsync()
{
    return await File.ReadAllTextAsync("config.json");
}

async Task WriteLogAsync(string message)
{
    await File.AppendAllTextAsync("log.txt", $"{DateTime.Now}: {message}
");
}

// StreamReader/Writer for line-by-line processing
async Task ProcessLargeFileAsync(string path)
{
    using var reader = new StreamReader(path);
    string? line;
    while ((line = await reader.ReadLineAsync()) != null)
    {
        ProcessLine(line);
    }
}

// StreamWriter for writing
async Task WriteResultsAsync(string path, IEnumerable<string> results)
{
    await using var writer = new StreamWriter(path);
    foreach (var result in results)
    {
        await writer.WriteLineAsync(result);
    }
}

// FileStream for binary data
async Task<byte[]> ReadBinaryFileAsync(string path)
{
    await using var stream = new FileStream(path, FileMode.Open, FileAccess.Read);
    var buffer = new byte[stream.Length];
    await stream.ReadAsync(buffer);
    return buffer;
}

// Path class — manipulate file paths safely
string fullPath = Path.Combine("data", "users", "config.json");
// "data/users/config.json" (OS-appropriate separator)

string extension = Path.GetExtension("file.txt");     // ".txt"
string filename = Path.GetFileName("/path/to/file.txt"); // "file.txt"
string nameNoExt = Path.GetFileNameWithoutExtension("file.txt"); // "file.txt"
string directory = Path.GetDirectoryName("/path/to/file.txt");   // "/path/to"
string tempFile = Path.GetTempFileName();  // Creates a temp file
string tempPath = Path.GetTempPath();     // Temp directory path

// Path.ChangeExtension
string newPath = Path.ChangeExtension("file.txt", ".json");  // "file.json"

// Directory operations
if (!Directory.Exists("cache"))
    Directory.CreateDirectory("cache");

string[] files = Directory.GetFiles("data/", "*.json");
string[] allFiles = Directory.GetFiles("data/", "*.*", SearchOption.AllDirectories);

// DirectoryInfo and FileInfo
var dirInfo = new DirectoryInfo("data/");
foreach (var file in dirInfo.GetFiles("*.json"))
{
    Console.WriteLine($"{file.Name} — {file.Length} bytes — {file.LastWriteTime}");
}

var fileInfo = new FileInfo("config.json");
if (fileInfo.Exists)
{
    Console.WriteLine($"Size: {fileInfo.Length}");
    Console.WriteLine($"Created: {fileInfo.CreationTime}");
    Console.WriteLine($"Modified: {fileInfo.LastWriteTime}");
}

// File attributes
File.SetAttributes("config.json", FileAttributes.Normal);
var attributes = File.GetAttributes("config.json");
bool isReadOnly = (attributes & FileAttributes.ReadOnly) == FileAttributes.ReadOnly;

// Copy, move, delete
File.Copy("source.txt", "dest.txt", overwrite: true);
File.Move("old.txt", "new.txt");
File.Delete("temp.txt");

// Check if file exists
if (File.Exists("config.json"))
{
    var content = File.ReadAllText("config.json");
}
```

## Common Mistakes

```csharp
// WRONG: Not using using statement for file streams
var stream = new FileStream("file.txt", FileMode.Open);
var reader = new StreamReader(stream);
// If exception occurs, stream is not disposed — resource leak!

// CORRECT: Use using statement for automatic disposal
using var stream = new FileStream("file.txt", FileMode.Open);
using var reader = new StreamReader(stream);
// Both disposed automatically at end of scope

// WRONG: Using synchronous I/O in async methods
async Task<string> ReadFileAsync(string path)
{
    return File.ReadAllText(path);  // Blocks the thread!
}

// CORRECT: Use async I/O methods
async Task<string> ReadFileAsync(string path)
{
    return await File.ReadAllTextAsync(path);  // Non-blocking
}

// WRONG: Not handling file not found
var content = File.ReadAllText("missing.txt");  // FileNotFoundException!

// CORRECT: Check existence or handle exception
if (File.Exists("config.json"))
{
    var content = File.ReadAllText("config.json");
}
// Or:
try
{
    var content = File.ReadAllText("config.json");
}
catch (FileNotFoundException)
{
    // Handle missing file
}

// WRONG: Using string concatenation for paths
string path = baseDir + "/" + subDir + "/" + filename;  // OS-dependent!

// CORRECT: Use Path.Combine
string path = Path.Combine(baseDir, subDir, filename);  // OS-appropriate

// WRONG: Not using await using for IAsyncDisposable
var writer = new StreamWriter("file.txt");
// StreamWriter implements IAsyncDisposable — should use await using

// CORRECT: Use await using for IAsyncDisposable
await using var writer = new StreamWriter("file.txt");
```

## Gotchas
- Always use `using` statement with file streams to ensure proper disposal.
- Prefer async I/O methods (`ReadAllTextAsync`, `ReadLineAsync`) in async code.
- `Path.Combine` is OS-aware. Don't concatenate paths with `/` or `\`.
- `File.Exists()` + `File.ReadAllText()` has a race condition. Use try/catch instead.
- `StreamReader` and `StreamWriter` implement `IAsyncDisposable`. Use `await using`.
- `File.SetAttributes` replaces ALL attributes. Read current attributes first if you need to preserve some.
- `Directory.GetFiles()` with `SearchOption.AllDirectories` throws if any subdirectory is inaccessible.
- `Path.GetTempFileName()` creates the file. You must delete it yourself.
- `FileInfo` and `DirectoryInfo` cache their data. Call `Refresh()` to get updated info.

## Related
- csharp/stdlib/async-advanced.md
- csharp/stdlib/error-handling.md
- csharp/stdlib/json-serialization.md
