---
id: "go-stdlib-file-io"
title: "File I/O"
language: "go"
category: "stdlib"
tags: ["go", "file", "io", "os", "bufio", "read", "write", "scanner", "directory", "walk"]
version: "1.21+"
retrieval_hint: "os.Open os.Create bufio.Scanner os.ReadFile os.WriteFile filepath.WalkDir ioutil replacement"
last_verified: "2026-05-24"
confidence: "high"
---

# File I/O

## When to Use
- Reading or writing entire files at once (`os.ReadFile`, `os.WriteFile`)
- Streaming file contents line by line (`bufio.Scanner`)
- Working with file handles for fine-grained control (`os.Open`, `os.Create`)
- Walking directory trees (`filepath.WalkDir`)
- Replacing deprecated `ioutil` functions (Go 1.16+)

## Standard Pattern

```go
package main

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
)

func main() {
	// --- Read entire file at once ---
	data, err := os.ReadFile("input.txt")
	if err != nil {
		fmt.Fprintf(os.Stderr, "read error: %v\n", err)
		os.Exit(1)
	}
	fmt.Printf("File contents (%d bytes):\n%s\n", len(data), data)

	// --- Write entire file at once ---
	content := []byte("Hello, World!\n")
	err = os.WriteFile("output.txt", content, 0644)
	if err != nil {
		fmt.Fprintf(os.Stderr, "write error: %v\n", err)
		os.Exit(1)
	}

	// --- Streaming read with bufio.Scanner ---
	file, err := os.Open("input.txt")
	if err != nil {
		fmt.Fprintf(os.Stderr, "open error: %v\n", err)
		os.Exit(1)
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	lineNum := 0
	for scanner.Scan() {
		lineNum++
		fmt.Printf("Line %d: %s\n", lineNum, scanner.Text())
	}
	if err := scanner.Err(); err != nil {
		fmt.Fprintf(os.Stderr, "scan error: %v\n", err)
	}

	// --- Create and write with os.Create ---
	out, err := os.Create("created.txt")
	if err != nil {
		fmt.Fprintf(os.Stderr, "create error: %v\n", err)
		os.Exit(1)
	}
	defer out.Close()

	writer := bufio.NewWriter(out)
	fmt.Fprintln(writer, "Line 1")
	fmt.Fprintln(writer, "Line 2")
	writer.Flush() // must flush buffered writer

	// --- Walk directory tree ---
	root := "."
	err = filepath.WalkDir(root, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return err // propagate walk errors
		}
		if d.IsDir() {
			fmt.Printf("[dir]  %s\n", path)
		} else {
			info, _ := d.Info()
			fmt.Printf("[file] %s (%d bytes)\n", path, info.Size())
		}
		return nil
	})
	if err != nil {
		fmt.Fprintf(os.Stderr, "walk error: %v\n", err)
	}
}
```

## Common Mistakes

```go
// WRONG: forgetting to close a file handle
file, _ := os.Open("data.txt")
data, _ := io.ReadAll(file)
// file never closed — resource leak

// CORRECT: always defer file.Close()
file, err := os.Open("data.txt")
if err != nil {
	log.Fatal(err)
}
defer file.Close()
data, err := io.ReadAll(file)
if err != nil {
	log.Fatal(err)
}

// WRONG: using deprecated ioutil functions (Go 1.16+)
// data, err := ioutil.ReadFile("file.txt")     // deprecated
// err = ioutil.WriteFile("file.txt", data, 0644) // deprecated

// CORRECT: use os.ReadFile and os.WriteFile
data, err := os.ReadFile("file.txt")
if err != nil {
	log.Fatal(err)
}
err = os.WriteFile("file.txt", data, 0644)
if err != nil {
	log.Fatal(err)
}

// WRONG: not checking scanner.Err() after scanning
scanner := bufio.NewScanner(file)
for scanner.Scan() {
	process(scanner.Text())
}
// I/O errors during scanning are silently lost

// CORRECT: always check scanner.Err()
scanner := bufio.NewScanner(file)
for scanner.Scan() {
	process(scanner.Text())
}
if err := scanner.Err(); err != nil {
	log.Printf("scan error: %v", err)
}

// WRONG: forgetting to flush a buffered writer
writer := bufio.NewWriter(file)
writer.WriteString("data")
// data may still be in buffer, not written to file

// CORRECT: flush before closing
writer := bufio.NewWriter(file)
writer.WriteString("data")
writer.Flush() // or defer writer.Flush() before file.Close()

// WRONG: using filepath.Walk (deprecated in Go 1.16+)
// filepath.Walk(root, walkFunc) — less efficient, calls os.Lstat on every file

// CORRECT: use filepath.WalkDir (Go 1.16+)
filepath.WalkDir(root, func(path string, d os.DirEntry, err error) error {
	// d.Info() is cheaper than os.Lstat when you need file info
	return nil
})

// WRONG: not handling errors from filepath.WalkDir callback
filepath.WalkDir(".", func(path string, d os.DirEntry, err error) error {
	// if err is non-nil, the walk couldn't access this path
	// ignoring it silently skips the error
	fmt.Println(path)
	return nil
})

// CORRECT: handle walk errors in callback
filepath.WalkDir(".", func(path string, d os.DirEntry, err error) error {
	if err != nil {
		log.Printf("error accessing %s: %v", path, err)
		return nil // continue walking, or return err to stop
	}
	fmt.Println(path)
	return nil
})
```

## Gotchas
- `os.ReadFile` reads the entire file into memory — unsuitable for very large files. Use `bufio.Scanner` or `io.Reader` for streaming.
- `os.WriteFile` truncates the file if it exists, or creates it if it doesn't. It does NOT append. Use `os.OpenFile` with `os.O_APPEND|os.O_CREATE|os.O_WRONLY` to append.
- `bufio.Scanner` has a default max line length of 64KB (`bufio.MaxScanTokenSize`). For longer lines, increase the buffer: `scanner.Buffer(make([]bufio.MaxScanTokenSize, 4096), 1024*1024)`.
- `filepath.WalkDir` is preferred over `filepath.Walk` because it avoids calling `os.Lstat` on every file, which is significantly faster on large directory trees.
- File permissions in `os.WriteFile` are affected by the process `umask`. `0644` typically results in `0644 & ~umask`.
- `os.Create` truncates existing files. If you accidentally `os.Create("important.txt")`, the file is emptied immediately.
- `defer file.Close()` should come AFTER the error check for `os.Open`. If `os.Open` returns an error, `file` is nil and `file.Close()` will panic.
- `os.DirEntry.Info()` returns `os.FileInfo` — it's cached from the directory read and is cheaper than calling `os.Lstat` separately.

## Related
- go/stdlib/command-line.md
- go/stdlib/slices-maps.md
- go/stdlib/error-handling.md
