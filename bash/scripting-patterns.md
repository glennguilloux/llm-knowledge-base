---
id: "bash-scripting-patterns"
title: "Shell Scripting Patterns"
language: "bash"
category: "stdlib"
tags: ["bash", "shell", "scripting", "automation", "cli"]
version: "n/a"
retrieval_hint: "bash script shebang variables arguments functions"
last_verified: "2026-05-24"
confidence: "high"
---

# Shell Scripting Patterns

## When to Use
- Automating repetitive system tasks
- Building CLI tools and utilities
- Glue code between programs
- Deployment and build scripts
- System administration tasks

## Standard Pattern

```bash
#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# Strict mode explanation:
# -e: exit on error
# -u: error on undefined variables
# -o pipefail: pipeline fails if any command fails
# IFS: safer word splitting

# Variables
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_NAME="$(basename "$0")"
readonly VERSION="1.0.0"

# Functions
log() { echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" >&2; }
error() { log "ERROR: $*"; exit 1; }
warn() { log "WARN: $*"; }

# Argument parsing with getopts
usage() {
    cat <<EOF
Usage: $SCRIPT_NAME [OPTIONS] <file>

Options:
    -v, --verbose    Enable verbose output
    -o, --output     Output file (default: stdout)
    -h, --help       Show this help
EOF
}

verbose=false
output=""
while getopts "vo:h" opt; do
    case $opt in
        v) verbose=true ;;
        o) output="$OPTARG" ;;
        h) usage; exit 0 ;;
        *) usage; exit 1 ;;
    esac
done
shift $((OPTIND - 1))

# Validate arguments
[[ $# -lt 1 ]] && error "Missing required argument: file"
input_file="$1"
[[ -f "$input_file" ]] || error "File not found: $input_file"

# Arrays
files=()
while IFS= read -r -d '' file; do
    files+=("$file")
done < <(find . -name "*.txt" -print0)

# Conditionals
if [[ -f "$output" ]]; then
    warn "Output file exists, overwriting"
fi

# String comparison
[[ "$verbose" == true ]] && log "Verbose mode enabled"

# Numeric comparison
count=${#files[@]}
if (( count > 100 )); then
    warn "Processing $count files"
fi

# Loops
for file in "${files[@]}"; do
    [[ -r "$file" ]] || continue
    process "$file"
done

# Here document
cat <<EOF > config.yaml
name: $SCRIPT_NAME
version: $VERSION
input: $input_file
EOF

# Process substitution
diff <(sort file1.txt) <(sort file2.txt)

# Cleanup trap
cleanup() {
    rm -f "$tmp_file"
}
trap cleanup EXIT
tmp_file=$(mktemp)

log "Processing complete: $count files"
```

## Common Mistakes

```bash
# WRONG: No strict mode
#!/bin/bash
# Undefined variables silently expand to empty string
# Failed commands are ignored
rm $UNDEFINED_VAR/file.txt  # Deletes /file.txt!

# CORRECT: Always use strict mode
#!/usr/bin/env bash
set -euo pipefail

# WRONG: Unquoted variables (word splitting + globbing)
file="my file.txt"
cat $file  # Two arguments: "my" and "file.txt"

# CORRECT: Always quote variables
cat "$file"

# WRONG: Using $() without quotes
files=$(find . -name "*.txt")
for f in $files; do  # Word splitting on spaces in filenames
    echo "$f"
done

# CORRECT: Use read loop or arrays
while IFS= read -r f; do
    echo "$f"
done < <(find . -name "*.txt")

# WRONG: Using [ ] (old syntax, many gotchas)
if [ $count -gt 10 ]; then  # Fails if $count is empty

# CORRECT: Use [[ ]] (safer, more features)
if [[ $count -gt 10 ]]; then

# WRONG: cd without checking
cd /some/dir  # Silently fails if dir doesn't exist
rm *.txt

# CORRECT: cd with error check
cd /some/dir || error "Cannot cd to /some/dir"
# Or: pushd /some/dir; ...; popd

# WRONG: Not using -- for end of options
rm "$file"  # If file starts with -, it's an option

# CORRECT: Use -- to separate options from arguments
rm -- "$file"
```

## Gotchas
- `set -euo pipefail` is the gold standard — always start scripts with it
- `$()` is preferred over backticks — supports nesting and is more readable
- `[[ ]]` is safer than `[ ]` — handles empty variables, supports regex
- Arrays in bash are indexed from 0 — `"${array[@]}"` expands all elements
- `"$@"` preserves individual arguments; `"$*"` concatenates into one string
- `read -r` disables backslash interpretation — always use it
- `<<<` passes a string as stdin; `<()` passes command output as a file
- `trap` ensures cleanup runs on exit, error, or signal
- `local` in functions prevents variable leakage to outer scope
- `${var:-default}` provides a default if var is unset or empty
- `${var:?error}` exits with an error message if var is unset
- `readonly` prevents accidental reassignment of constants
- `PIPESTATUS` array holds exit codes of all commands in a pipeline

## Related
- bash/error-handling.md
- bash/string-manipulation.md
- bash/process-management.md
