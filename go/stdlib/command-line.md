---
id: "go-stdlib-command-line"
title: "Command-Line Arguments and Flags"
language: "go"
category: "stdlib"
tags: ["go", "command-line", "flag", "args", "env", "signal", "os.Args", "subcommand", "cli"]
version: "1.21+"
retrieval_hint: "os.Args flag package subcommand environment variable signal handling CLI command-line"
last_verified: "2026-05-24"
confidence: "high"
---

# Command-Line Arguments and Flags

## When to Use
- Parsing positional command-line arguments (`os.Args`)
- Parsing named flags with types (`flag` package)
- Building CLI tools with subcommands
- Reading environment variables (`os.Getenv`, `os.LookupEnv`)
- Handling OS signals for graceful shutdown (`os/signal`, `context`)

## Standard Pattern

```go
package main

import (
	"context"
	"flag"
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"
)

func main() {
	// --- os.Args: raw positional arguments ---
	fmt.Println("Program:", os.Args[0])
	fmt.Println("Args:", os.Args[1:])

	// --- flag package: named flags ---
	var (
		name    = flag.String("name", "world", "Name to greet")
		verbose = flag.Bool("verbose", false, "Enable verbose output")
		count   = flag.Int("count", 1, "Number of greetings")
		timeout = flag.Duration("timeout", 5*time.Second, "Timeout duration")
	)
	flag.Parse()

	if *verbose {
		fmt.Printf("Flags: name=%s, count=%d, timeout=%s\n", *name, *count, *timeout)
	}

	for i := 0; i < *count; i++ {
		fmt.Printf("Hello, %s!\n", *name)
	}

	// --- Subcommands with flag.NewFlagSet ---
	if len(flag.Args()) == 0 {
		fmt.Println("Usage: program <serve|fetch> [flags]")
		os.Exit(1)
	}

	switch flag.Arg(0) {
	case "serve":
		serveCmd := flag.NewFlagSet("serve", flag.ExitOnError)
		port := serveCmd.Int("port", 8080, "Port to listen on")
		serveCmd.Parse(flag.Args()[1:])
		fmt.Printf("Serving on port %d\n", *port)

	case "fetch":
		fetchCmd := flag.NewFlagSet("fetch", flag.ExitOnError)
		url := fetchCmd.String("url", "", "URL to fetch (required)")
		fetchCmd.Parse(flag.Args()[1:])
		if *url == "" {
			fmt.Fprintln(os.Stderr, "Error: --url is required")
			fetchCmd.Usage()
			os.Exit(1)
		}
		fmt.Printf("Fetching %s\n", *url)

	default:
		fmt.Fprintf(os.Stderr, "Unknown subcommand: %s\n", flag.Arg(0))
		os.Exit(1)
	}

	// --- Environment variables ---
	apiKey := os.Getenv("API_KEY")
	if apiKey == "" {
		fmt.Fprintln(os.Stderr, "Warning: API_KEY not set")
	}

	// LookupEnv distinguishes between empty and unset
	if path, ok := os.LookupEnv("PATH"); ok {
		fmt.Println("PATH is set:", path[:50], "...")
	} else {
		fmt.Println("PATH is not set")
	}

	// --- Signal handling for graceful shutdown ---
	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	// Simulate work that can be interrupted
	select {
	case <-time.After(30 * time.Second):
		fmt.Println("Work completed")
	case <-ctx.Done():
		fmt.Println("\nReceived signal, shutting down gracefully...")
		// cleanup here
		time.Sleep(100 * time.Millisecond) // simulate cleanup
		fmt.Println("Shutdown complete")
	}
}
```

## Common Mistakes

```go
// WRONG: accessing os.Args without bounds check
arg := os.Args[1] // panic: index out of range if no args provided

// CORRECT: check length first
if len(os.Args) < 2 {
	fmt.Fprintln(os.Stderr, "Usage: program <arg>")
	os.Exit(1)
}
arg := os.Args[1]

// WRONG: defining flags after flag.Parse()
flag.Parse()
name := flag.String("name", "default", "a flag") // too late — already parsed

// CORRECT: define all flags before calling flag.Parse()
name := flag.String("name", "default", "a flag")
flag.Parse()

// WRONG: using flag.Args() before flag.Parse()
args := flag.Args() // returns os.Args[1:] — flags not parsed yet

// CORRECT: call flag.Parse() first
flag.Parse()
args := flag.Args() // returns only non-flag arguments

// WRONG: not handling required flags
// flag package has no concept of "required" — you must check manually
url := flag.String("url", "", "URL")
flag.Parse()
// if --url is omitted, *url is "" — no error from flag package

// CORRECT: validate required flags after parsing
url := flag.String("url", "", "URL (required)")
flag.Parse()
if *url == "" {
	fmt.Fprintln(os.Stderr, "Error: --url is required")
	flag.Usage()
	os.Exit(1)
}

// WRONG: using os.Getenv and treating empty string as "not set"
apiKey := os.Getenv("API_KEY")
if apiKey == "" {
	// is it unset, or set to empty string? can't tell.
}

// CORRECT: use os.LookupEnv to distinguish unset from empty
apiKey, ok := os.LookupEnv("API_KEY")
if !ok {
	fmt.Fprintln(os.Stderr, "API_KEY is not set")
	os.Exit(1)
}
if apiKey == "" {
	fmt.Fprintln(os.Stderr, "API_KEY is set but empty")
	os.Exit(1)
}

// WRONG: not stopping signal.NotifyContext (minor resource leak)
ctx, _ := signal.NotifyContext(context.Background(), syscall.SIGINT)
// stop function is discarded — can't manually cancel

// CORRECT: always call stop when done
ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
defer stop()
```

## Gotchas
- `os.Args[0]` is the program name (or path), not the first argument. Actual arguments start at `os.Args[1]`.
- `flag.Parse()` must be called before using any flag values. It can only be called once per `flag.FlagSet`.
- The `flag` package does NOT support required flags. You must manually check for zero values after parsing.
- `flag.NewFlagSet` with `flag.ExitOnError` calls `os.Exit(1)` on parse errors. Use `flag.ContinueOnError` if you want to handle errors yourself.
- `flag.Args()` returns only non-flag arguments (after `--` or after all flags are consumed). Flags like `--name=value` are not included.
- `signal.NotifyContext` creates a context that is cancelled on the specified signals. Always call the returned `stop()` function to release resources and restore default signal handling.
- `os.Getenv` returns an empty string for unset variables. Use `os.LookupEnv` to distinguish between "not set" and "set to empty string".
- The `flag` package supports `-flag`, `--flag`, and `--flag=value` syntax. All three are equivalent.
- `flag.Usage` prints a usage message to stderr. You can override it: `flag.Usage = func() { fmt.Fprintln(os.Stderr, "custom usage") }`.
- Subcommands are not built into the `flag` package — you manually create `flag.NewFlagSet` for each subcommand and parse the remaining args.

## Related
- go/stdlib/file-io.md
- go/stdlib/error-handling.md
- go/stdlib/context.md
