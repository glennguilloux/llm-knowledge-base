---
id: "go-stdlib-modules"
title: "Go Modules and Dependency Management"
language: "go"
category: "stdlib"
tags: ["go", "modules", "dependency", "go.mod", "go.sum", "versioning", "vendor"]
version: "1.21+"
retrieval_hint: "go.mod go.sum version replace vendor workspace go get go install"
last_verified: "2026-05-22"
confidence: "high"
---

# Go Modules and Dependency Management

## When to Use
- Starting a new Go project or library
- Managing third-party dependencies
- Working with private repositories or monorepos
- Reproducing builds across machines (vendoring)
- Developing multiple modules simultaneously (workspaces)

## Standard Pattern

```go
// Initialize a new module (run once)
// go mod init github.com/yourname/project

// go.mod — declares module path, Go version, and dependencies
module github.com/yourname/project

go 1.22

require (
    github.com/gin-gonic/gin v1.9.1
    github.com/lib/pq v1.10.9
    golang.org/x/sync v0.6.0
)

require (
    // indirect dependencies listed here by `go mod tidy`
    github.com/bytedance/sonic v1.9.1 // indirect
)

// Add a dependency
// go get github.com/gin-gonic/gin@v1.9.1

// Update to latest
// go get -u github.com/gin-gonic/gin

// Add specific version
// go get github.com/gin-gonic/gin@v1.10.0

// Tidy — add missing, remove unused
// go mod tidy

// Download all dependencies to local cache
// go mod download

// Verify checksums match go.sum
// go mod verify

// Vendor dependencies into ./vendor directory
// go mod vendor

// Build from vendor
// go build -mod=vendor ./...

// --- Replace directive (local development or fork) ---
// In go.mod:
// replace github.com/original/pkg => ../local-copy
// replace github.com/original/pkg => github.com/fork/pkg v1.2.3

// --- Go Workspaces (Go 1.18+) ---
// go work init ./module-a ./module-b
// go.work file:
// go 1.22
// use (
//     ./module-a
//     ./module-b
// )

// Add module to workspace
// go work use ./new-module

// Sync workspace
// go work sync

// --- Version queries ---
// go list -m -versions github.com/gin-gonic/gin
// go list -m all                    // list all dependencies
// go list -m -json github.com/gin-gonic/gin  // detailed info
```

## Common Mistakes

```go
// WRONG: committing go.sum without running go mod tidy
// stale checksums cause CI failures

// CORRECT: always run tidy before committing
// go mod tidy
// git add go.mod go.sum
// git commit -m "tidy modules"

// WRONG: forgetting go.sum in version control
// .gitignore:
// go.sum    // DO NOT ignore

// CORRECT: always commit go.sum
// go.sum provides reproducible builds — it is the integrity lock file

// WRONG: using replace with absolute path
// replace github.com/pkg => /home/user/dev/pkg  // breaks on other machines

// CORRECT: use relative path or remote fork
// replace github.com/pkg => ../dev/pkg

// WRONG: running go get inside go mod vendor
// Vendor directory is a snapshot — don't modify it

// CORRECT: go get updates go.mod, then re-vendor
// go get github.com/new/pkg@latest
// go mod vendor

// WRONG: mixing Go modules and GOPATH mode
// GO111MODULE=off forces GOPATH — deprecated and confusing

// CORRECT: always use modules (default since Go 1.16)
// go mod init github.com/yourname/project

// WRONG: pinning to master/HEAD with pseudo-versions
// go get github.com/pkg@abc123   // unstable, changes on every push

// CORRECT: pin to a tagged release
// go get github.com/pkg@v1.5.2
```

## Gotchas
- `go get` updates go.mod AND downloads the module; `go install` installs a binary to `$GOPATH/bin`
- `go mod tidy` removes unused dependencies and adds missing ones — run before every commit
- `go.sum` must be committed — it's the integrity check file, not a lock file like package-lock.json
- Replace directives with local paths are for development only — CI needs remote references
- Go workspaces (`go work`) are for multi-module local development — don't commit `go.work` in libraries
- `// indirect` in go.mod means the dependency is transitive (required by another dependency)
- Module proxy: Go downloads modules from `proxy.golang.org` by default — set `GOPROXY=direct` for private repos
- Private repos: set `GOPRIVATE=github.com/yourorg/*` to bypass the module proxy
- `go mod vendor` creates a snapshot of dependencies — use `-mod=vendor` in build commands
- Pseudo-versions (v0.0.0-yyyymmddhhmmss-commit) indicate no tagged release — prefer tagged versions
- `go list -m -versions <module>` shows all available tagged versions
- Minimum version selection: Go uses the minimum version that satisfies all constraints — deterministic builds
- `go.work.sum` exists in workspace mode — don't confuse with `go.sum`

## Related
- go/stdlib/error-handling.md
- go/testing/testing.md
- go/web/http-server.md
