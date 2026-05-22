---
id: "bash-error-handling"
title: "Error Handling in Shell Scripts"
language: "bash"
category: "stdlib"
tags: ["bash", "shell", "error-handling", "trap", "exit-codes"]
version: "n/a"
retrieval_hint: "bash trap ERR exit code error handling set -e"
last_verified: "2026-05-22"
confidence: "high"
---

# Error Handling in Shell Scripts

## When to Use
- Writing reliable scripts that handle failures gracefully
- Ensuring cleanup runs even when errors occur
- Implementing retry logic for transient failures
- Building robust CI/CD pipelines

## Standard Pattern

```bash
#!/usr/bin/env bash
set -euo pipefail

# Error handler function
error_handler() {
    local lineno="$1"
    local command="$2"
    local code="$3"
    echo "Error in script at line $lineno: command '$command' exited with code $code" >&2
    exit "$code"
}
trap 'error_handler ${LINENO} "$BASH_COMMAND" $?' ERR

# Cleanup pattern
tmp_dir=$(mktemp -d)
cleanup() {
    local exit_code=$?
    rm -rf "$tmp_dir"
    exit "$exit_code"
}
trap cleanup EXIT

# Retry with exponential backoff
retry() {
    local max_attempts="${1:?max_attempts required}"
    local delay="${2:?delay required}"
    shift 2
    local attempt=1
    while (( attempt <= max_attempts )); do
        if "$@"; then
            return 0
        fi
        echo "Attempt $attempt/$max_attempts failed, retrying in ${delay}s..." >&2
        sleep "$delay"
        delay=$(( delay * 2 ))
        (( attempt++ ))
    done
    echo "All $max_attempts attempts failed" >&2
    return 1
}

# Usage
retry 3 1 curl -s https://api.example.com/data

# Checking exit codes explicitly
if ! command -v git &>/dev/null; then
    echo "git is required but not installed" >&2
    exit 1
fi

# Using PIPESTATUS for pipeline errors
set -o pipefail
grep "error" /var/log/app.log | sort | uniq -c
if [[ ${PIPESTATUS[0]} -ne 0 ]]; then
    echo "grep failed" >&2
    exit 1
fi

# Logging with context
log_error() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $*" >&2
}

log_error "Database connection failed" "host=db.example.com port=5432"

# Return codes convention:
# 0   = success
# 1   = general error
# 2   = misuse of shell command
# 126 = command cannot execute
# 127 = command not found
# 128+N = signal N (e.g., 130 = SIGINT/Ctrl+C)
```

## Common Mistakes

```bash
# WRONG: Ignoring exit codes
set +e
important_command
echo "continuing..."  # Runs even if important_command failed

# CORRECT: Handle errors explicitly
if ! important_command; then
    echo "Command failed" >&2
    exit 1
fi

# WRONG: trap without proper cleanup
trap "rm -f $tmp_file" EXIT
# $tmp_file is expanded at trap definition time, not execution time

# CORRECT: Use single quotes or a function
trap 'rm -f "$tmp_file"' EXIT
# Or: trap cleanup EXIT

# WRONG: Not using set -o pipefail
grep "pattern" file.txt | sort | head -5
# If grep fails (no match), the pipeline still succeeds

# CORRECT: Enable pipefail
set -o pipefail
grep "pattern" file.txt | sort | head -5

# WRONG: Catching errors with || that should abort
mkdir -p /important/dir || echo "dir exists"
# What if mkdir fails for permission reasons?

# CORRECT: Let critical operations fail
mkdir -p /important/dir

# WRONG: Using set -e inside a function (affects entire script)
my_function() {
    set -e  # This affects the whole script!
    ...
}

# CORRECT: Use explicit error checking in functions
my_function() {
    local result
    if ! result=$(some_command); then
        echo "Failed" >&2
        return 1
    fi
}

# WRONG: Ignoring signals
# Script keeps running when user presses Ctrl+C

# CORRECT: Trap signals for graceful shutdown
shutdown_handler() {
    echo "Shutting down..." >&2
    # Cleanup
    exit 130
}
trap shutdown_handler INT TERM
```

## Gotchas
- `set -e` does NOT propagate into subshells, command substitutions, or `if` conditions
- `set -e` is ignored for commands in `if` conditions, `||`, `&&`, or `while` tests
- `trap ERR` fires on non-zero exit (like `set -e`) but also in functions and subshells
- `trap EXIT` always runs on script exit, regardless of how it exits
- `PIPESTATUS` holds exit codes for each command in the pipeline
- `set -o pipefail` makes the pipeline exit with the rightmost non-zero exit code
- `$?` holds the exit code of the last command — capture it immediately
- `local` variables in functions are still visible to called functions
- `return` exits a function; `exit` exits the script
- `||` suppresses errors — use carefully, only for expected failures
- `2>/dev/null` hides stderr — use `2>&1 | grep` if you need to inspect it
- `wait -n` (bash 4.3+) waits for any background job to finish

## Related
- bash/scripting-patterns.md
- bash/process-management.md
- bash/testing-debugging.md
