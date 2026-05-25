---
id: "rust-stdlib-file-io"
title: "Rust File I/O: Reading, Writing, and Directory Operations"
language: "rust"
category: "stdlib"
subcategory: "io"
tags: ["rust", "file", "fs", "read", "write", "bufreader", "bufwriter", "directory", "path"]
version: "1.75+"
retrieval_hint: "Rust file io read write BufReader BufWriter create_dir_all walk directory File open error"
last_verified: "2026-05-24"
confidence: "high"
---

# Rust File I/O: Reading, Writing, and Directory Operations

## When to Use

- `std::fs::read_to_string`: Quickly read an entire small file into a `String`
- `std::fs::write`: Quickly write raw bytes or a string to a file
- `File::open`: Open an existing file for reading with full error handling
- `File::create`: Create/truncate a file for writing
- `BufReader`: Buffered reading for line-by-line or频繁 small reads
- `BufWriter`: Buffered writing for many small writes (flushes on drop)
- `std::fs::create_dir_all`: Recursively create directories
- `std::fs::read_dir`: Iterate directory entries (non-recursive)
- Walkdir (crate) or manual recursion: Walking a directory tree

## Standard Pattern

```rust
use std::fs::{self, File, OpenOptions};
use std::io::{self, BufRead, BufReader, BufWriter, Write};
use std::path::Path;

/// Read an entire file into a String, with proper error handling
fn read_config(path: &Path) -> Result<String, io::Error> {
    fs::read_to_string(path)
}

/// Write a string to a file, creating parent directories if needed
fn save_output(path: &Path, content: &str) -> Result<(), io::Error> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }
    fs::write(path, content)?;
    Ok(())
}

/// Read a file line by line using a buffered reader (efficient for large files)
fn count_non_empty_lines(path: &Path) -> Result<usize, io::Error> {
    let file = File::open(path)?;
    let reader = BufReader::new(file);
    let mut count = 0;
    for line in reader.lines() {
        let line = line?; // Propagate read errors
        if !line.trim().is_empty() {
            count += 1;
        }
    }
    Ok(count)
}

/// Write multiple lines efficiently using a buffered writer
fn write_lines(path: &Path, lines: &[&str]) -> Result<(), io::Error> {
    let file = File::create(path)?;
    let mut writer = BufWriter::new(file);
    for line in lines {
        writeln!(writer, "{}", line)?;
    }
    // BufWriter flushes automatically on drop, but explicit flush
    // catches errors that would otherwise be lost
    writer.flush()?;
    Ok(())
}

/// Read a file with OpenOptions for fine-grained control
fn append_to_log(path: &Path, message: &str) -> Result<(), io::Error> {
    let mut file = OpenOptions::new()
        .create(true)    // Create if it doesn't exist
        .append(true)    // Append, don't truncate
        .open(path)?;

    writeln!(file, "{}", message)?;
    Ok(())
}

/// Walk a directory recursively (non-recursive base shown; recursive pattern included)
fn list_rust_files(dir: &Path) -> Result<Vec<std::path::PathBuf>, io::Error> {
    let mut results = Vec::new();
    let entries = fs::read_dir(dir)?;

    for entry in entries {
        let entry = entry?;
        let path = entry.path();
        if path.is_dir() {
            // Recurse into subdirectories
            let mut sub = list_rust_files(&path)?;
            results.append(&mut sub);
        } else if path.extension().map_or(false, |ext| ext == "rs") {
            results.push(path);
        }
    }
    Ok(results)
}

/// Check if a file exists and read it, with idiomatic error handling
fn read_or_default(path: &Path, default: &str) -> String {
    match fs::read_to_string(path) {
        Ok(content) => content,
        Err(e) if e.kind() == io::ErrorKind::NotFound => default.to_string(),
        Err(e) => {
            eprintln!("Warning: failed to read {}: {}", path.display(), e);
            default.to_string()
        }
    }
}

fn main() -> Result<(), io::Error> {
    let output_path = Path::new("/tmp/myapp/output/data.txt");

    // Ensure parent dirs exist and write a file
    save_output(output_path, "Hello, world!")?;

    // Read it back
    let content = read_config(output_path)?;
    println!("Read: {}", content);

    // Append to a log file
    let log_path = Path::new("/tmp/myapp/log.txt");
    append_to_log(log_path, "Application started")?;

    // List Rust files in the current directory
    let rust_files = list_rust_files(Path::new("."))?;
    for f in &rust_files {
        println!("Found: {}", f.display());
    }

    Ok(())
}
```

## Common Mistakes

```rust
// WRONG: Using unwrap() on File::open without handling the error
let file = File::open("config.toml").unwrap(); // Panics if file doesn't exist

// CORRECT: Propagate or handle the error properly
let file = File::open("config.toml").map_err(|e| {
    format!("Failed to open config.toml: {}", e)
})?;
// Or with context from a crate like anyhow:
// let file = File::open("config.toml").context("Failed to open config.toml")?;


// WRONG: Forgetting to flush BufWriter (data may be lost)
let file = File::create("out.txt")?;
let mut writer = BufWriter::new(file);
writeln!(writer, "important data")?;
// writer dropped here but drop's flush error is silently lost

// CORRECT: Explicitly flush to catch write errors
let file = File::create("out.txt")?;
let mut writer = BufWriter::new(file);
writeln!(writer, "important data")?;
writer.flush()?; // Propagates any write error


// WRONG: Using read_to_string for very large files (loads entire file into memory)
let content = fs::read_to_string("huge_10gb_log.txt")?; // OutOfMemory risk

// CORRECT: Use BufReader for line-by-line or chunked processing
let file = File::open("huge_10gb_log.txt")?;
let reader = BufReader::new(file);
for line in reader.lines() {
    let line = line?;
    process_line(&line);
}


// WRONG: Not creating parent directories before writing
fs::write("/tmp/nonexistent/dir/file.txt", "data")?; // ERROR: No such file or directory

// CORRECT: Create parent directories first
let path = Path::new("/tmp/nonexistent/dir/file.txt");
if let Some(parent) = path.parent() {
    fs::create_dir_all(parent)?;
}
fs::write(path, "data")?;


// WRONG: Ignoring the Result from fs::write or other I/O operations
fs::write("output.txt", "data"); // WARNING: Result not used, write error silently lost

// CORRECT: Always handle the Result
fs::write("output.txt", "data")?;
// Or at minimum:
if let Err(e) = fs::write("output.txt", "data") {
    eprintln!("Write failed: {}", e);
}


// WRONG: Calling read_dir() without handling the iterator Result items
for entry in fs::read_dir(".")? {
    let path = entry.path(); // ERROR: entry is Result<DirEntry>, not DirEntry
    println!("{}", path.display());
}

// CORRECT: Handle the Result for each directory entry
for entry in fs::read_dir(".")? {
    let entry = entry?;
    println!("{}", entry.path().display());
}
```

## Gotchas
- `fs::write(path, content)` will **truncate** an existing file — if you need to append, use `OpenOptions::new().append(true)` or `File::create` to truncate intentionally
- `BufWriter` drops and flushes on scope exit, but any flush error during drop is **silently ignored** — always call `writer.flush()?` explicitly to catch partial writes
- `fs::read_to_string` includes no newline validation or encoding handling beyond valid UTF-8 — non-UTF-8 bytes will cause an error; use `fs::read(path)` for raw `Vec<u8>`
- `Path::exists()` has a TOCTOU race: the file could be deleted between the check and the next operation — always prefer just attempting the operation and handling the error
- `fs::read_dir` is **not recursive** — it yields only the immediate children; you must manually recurse into subdirectories or use the `walkdir` crate
- `std::io::ErrorKind::NotFound` is the idiomatic way to detect missing files, but the file also could be inaccessible due to permissions (`PermissionDenied`) — handle error kinds specifically when behavior should differ
- `File::create` is equivalent to `OpenOptions::new().write(true).create(true).truncate(true)` — be aware it always truncates existing files
- On Unix, path operations are byte-based; on Windows, they require valid Unicode — use `PathBuf`/`Path` rather than raw `&str` strings for portable code

## Related
- rust/stdlib/error-handling.md
- rust/stdlib/result-option.md
