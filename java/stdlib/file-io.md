---
id: "java-stdlib-file-io"
title: "File I/O with NIO and BufferedReader"
language: "java"
category: "stdlib"
tags: ["file-io", "nio", "Files", "BufferedReader", "Path", "streams", "reading", "writing"]
version: "17+"
retrieval_hint: "file IO NIO Files BufferedReader Path read write lines stream"
last_verified: "2026-05-24"
confidence: "high"
---

# File I/O with NIO and BufferedReader

## When to Use
- Reading and writing text or binary files
- Processing large files line by line
- Listing, creating, and deleting files/directories
- Working with file paths across platforms

## Standard Pattern

```java
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.List;
import java.util.stream.Stream;

public class FileIO {

    // --- Reading entire file as string (small files) ---
    public static String readAllText(Path path) throws IOException {
        return Files.readString(path, StandardCharsets.UTF_8);
    }

    // --- Writing string to file ---
    public static void writeText(Path path, String content) throws IOException {
        Files.createDirectories(path.getParent());
        Files.writeString(path, content, StandardCharsets.UTF_8,
            StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING);
    }

    // --- Reading lines (memory-efficient for large files) ---
    public static List<String> readLines(Path path) throws IOException {
        return Files.readAllLines(path, StandardCharsets.UTF_8);
    }

    // --- Stream lines (lazy, for very large files) ---
    public static long countLines(Path path) throws IOException {
        try (Stream<String> lines = Files.lines(path, StandardCharsets.UTF_8)) {
            return lines.count();
        }
    }

    // --- BufferedReader for manual control ---
    public static String readFirstNLines(Path path, int n) throws IOException {
        try (var reader = Files.newBufferedReader(path, StandardCharsets.UTF_8)) {
            var sb = new StringBuilder();
            for (int i = 0; i < n; i++) {
                String line = reader.readLine();
                if (line == null) break;
                sb.append(line).append("\n");
            }
            return sb.toString();
        }
    }

    // --- Appending to file ---
    public static void appendLine(Path path, String line) throws IOException {
        Files.writeString(path, line + "\n", StandardCharsets.UTF_8,
            StandardOpenOption.CREATE, StandardOpenOption.APPEND);
    }

    // --- Binary file copy ---
    public static void copyFile(Path source, Path target) throws IOException {
        Files.createDirectories(target.getParent());
        Files.copy(source, target, StandardCopyOption.REPLACE_EXISTING);
    }

    // --- Listing directory contents ---
    public static List<Path> listFiles(Path dir, String glob) throws IOException {
        try (Stream<Path> paths = Files.list(dir)) {
            return paths
                .filter(p -> p.getFileName().toString().matches(glob))
                .toList();
        }
    }

    // --- Walking directory tree ---
    public static List<Path> findJavaFiles(Path root) throws IOException {
        try (Stream<Path> paths = Files.walk(root)) {
            return paths
                .filter(p -> p.toString().endsWith(".java"))
                .toList();
        }
    }
}
```

## Common Mistakes

```java
// WRONG: Reading large file entirely into memory
byte[] data = Files.readAllBytes(hugeFile);  // OOM on large files!

// CORRECT: Stream lines for large files
try (Stream<String> lines = Files.lines(hugeFile)) {
    lines.filter(line -> line.contains("ERROR"))
         .forEach(System.out::println);
}

// WRONG: Not closing resources (file handle leak)
BufferedReader reader = new BufferedReader(new FileReader("data.txt"));
String line = reader.readLine();  // If this throws, reader is never closed

// CORRECT: Use try-with-resources
try (var reader = Files.newBufferedReader(Path.of("data.txt"))) {
    String line = reader.readLine();
}

// WRONG: Hardcoded file separator
String path = "src" + "\\" + "main" + "\\" + "java";  // Windows only!

// CORRECT: Use Path API
Path path = Path.of("src", "main", "java");

// WRONG: Not specifying charset
Files.readString(path)  // Uses default charset (platform-dependent!)

// CORRECT: Always specify charset
Files.readString(path, StandardCharsets.UTF_8)

// WRONG: Ignoring return value of Files.createDirectories
Files.createDirectories(dir);  // Returns path, but ignores if it failed

// WRONG: Using File instead of Path
File file = new File("data.txt");  // Old API, less functional

// CORRECT: Use Path (NIO)
Path path = Path.of("data.txt");
```

## Gotchas
- `Files.readAllLines()` loads all lines into memory — use `Files.lines()` stream for large files
- `Files.lines()` returns a `Stream<String>` that must be closed (try-with-resources)
- `StandardCharsets.UTF_8` is preferred over `Charset.forName("UTF-8")` — no checked exception
- `Path.of("a", "b", "c")` joins paths — no manual separator needed
- `Files.copy()` fails if target exists unless `REPLACE_EXISTING` is specified
- `Files.walk()` does not follow symlinks by default — use `FOLLOW_LINKS` option
- `BufferedReader.readLine()` returns null at EOF — always check for null

## Related
- java/stdlib/streams.md
- java/stdlib/exception-handling.md
