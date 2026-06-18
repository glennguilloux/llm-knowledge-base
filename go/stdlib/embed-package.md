---
id: "go-stdlib-embed-package"
title: "Go embed Package — Embedding Static Files and Assets"
language: "go"
category: "stdlib"
subcategory: "file-io"
tags: ["go", "embed", "static-files", "assets", "go1.16", "http"]
version: "1.21+"
retrieval_hint: "Go embed directive static files assets embed.FS HTTP server template"
last_verified: "2026-05-25"
confidence: "high"
---

# Go embed Package — Embedding Static Files and Assets

## When to Use
- Bundling static assets (HTML, CSS, JS) into a single Go binary
- Embedding configuration files, SQL migrations, or default data files
- Shipping template files that you don't want to distribute separately
- Replacing file system reads for deployment artifacts

## Standard Pattern

```go
package main

import (
	"embed"
	"io/fs"
	"log"
	"net/http"
	"text/template"
)

//go:embed static/*
var staticFiles embed.FS

//go:embed templates/*.html
var templateFiles embed.FS

//go:embed config/default.yaml
var defaultConfig []byte

//go:embed sql/migrations/*.sql
var migrations embed.FS

// --- Serve embedded static files via HTTP ---
func main() {
	// Subdirectory from embed.FS (strip the "static" prefix)
	staticFS, err := fs.Sub(staticFiles, "static")
	if err != nil {
		log.Fatal(err)
	}

	http.Handle("/static/", http.StripPrefix("/static/", http.FileServer(http.FS(staticFS))))

	// Parse embedded templates
	tmpl := template.Must(template.ParseFS(templateFiles, "templates/*.html"))

	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		tmpl.Execute(w, map[string]string{"Title": "Hello from embedded assets!"})
	})

	// Use embedded default config
	log.Println("Default config:", string(defaultConfig))

	log.Fatal(http.ListenAndServe(":8080", nil))
}

// --- Helper: list embedded files in a directory ---
func ListEmbedded(fs embed.FS, dir string) ([]string, error) {
	entries, err := fs.ReadDir(dir)
	if err != nil {
		return nil, err
	}
	var names []string
	for _, e := range entries {
		names = append(names, e.Name())
	}
	return names, nil
}

// --- Helper: read a single embedded file ---
func ReadEmbedded(fs embed.FS, path string) (string, error) {
	data, err := fs.ReadFile(path)
	if err != nil {
		return "", err
	}
	return string(data), nil
}
```

## Common Mistakes

```go
// WRONG: Forgetting to import "embed" — the directive won't compile
//go:embed data.txt
var data []byte  // ERROR: "embed" imported but not used (if that's the only use)

// CORRECT: Use blank import for embed when not using it directly
import _ "embed"

//go:embed data.txt
var data []byte  // Now it works

// WRONG: Using relative paths like "../" — embed only allows relative within the module
//go:embed ../outside/file.txt  // ERROR: pattern ../outside/file.txt: invalid pattern syntax

// WRONG: Using go:embed on a variable inside a function
func main() {
    //go:embed file.txt  // ERROR: go:embed only allowed at package level
    //var data []byte
}

// CORRECT: Embed at package level
//go:embed file.txt
var data []byte

func main() {
    fmt.Println(string(data))
}

// WRONG: Expecting embed to follow symlinks
// embed does NOT follow symlinks — it reads the symlink file itself as the pattern,
// not the target. If foo -> bar.txt, //go:embed foo embeds "foo" (the symlink name).

// WRONG: Using embed.FS with http.FileServer without subdirectory
//go:embed static
var files embed.FS

// This serves from the root — URLs like /static/style.css won't match
// because the file is at "static/style.css", not "/style.css"
http.Handle("/", http.FileServer(http.FS(files)))

// CORRECT: Use fs.Sub to strip the prefix
staticFS, _ := fs.Sub(files, "static")
http.Handle("/static/", http.StripPrefix("/static/", http.FileServer(http.FS(staticFS))))
```

## Gotchas
- **`//go:embed` is a compiler directive, not a runtime function:** The files are embedded AT COMPILE TIME. If the source files don't exist at compile time, the build fails. There's no fallback or lazy loading.
- **Pattern syntax is limited:** `embed` uses a restricted glob syntax. `*` matches any non-separator characters, `...` matches any path. You cannot use regex, `?`, or character classes. Double-check the [embed pattern docs](https://pkg.go.dev/embed).
- **Binary size implications:** All embedded files are included in the compiled binary, uncompressed. A 10MB SQLite migration folder adds 10MB to your binary. For large assets, consider compression at build time or streaming from external storage.
- **`embed.FS` is read-only:** You cannot modify embedded files at runtime. If you need dynamic content alongside static assets, use `os.DirFS()` or a custom `fs.FS` wrapper that falls back to embedded for defaults.
- **Testing with embedded files:** In tests, `embed.FS` reads from the test's working directory, not the module root. Use `os.DirFS("testdata")` alongside embedded for test-specific overrides.

## Related
- go/stdlib/file-io.md
- go/web/http-server.md
