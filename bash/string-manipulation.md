---
id: "bash-string-manipulation"
title: "String Manipulation in Bash"
language: "bash"
category: "stdlib"
tags: ["bash", "shell", "strings", "text-processing", "sed", "awk"]
version: "n/a"
retrieval_hint: "bash string manipulation sed awk grep cut tr"
last_verified: "2026-05-24"
confidence: "high"
---

# String Manipulation in Bash

## When to Use
- Parsing and transforming text data
- Processing log files and CSV data
- Extracting substrings from variables
- Text substitution and replacement

## Standard Pattern

```bash
#!/usr/bin/env bash
set -euo pipefail

# Parameter expansion
name="Hello World"

echo "${name^^}"          # HELLO WORLD (uppercase)
echo "${name,,}"          # hello world (lowercase)
echo "${name^}"           # Hello World (capitalize first)
echo "${#name}"           # 11 (length)

# Substring extraction
path="/home/user/documents/file.txt"
echo "${path##*/}"        # file.txt (basename — remove longest prefix matching */)
echo "${path%/*}"         # /home/user/documents (dirname — remove shortest suffix matching /*)
echo "${path%%.*}"        # /home/user/documents/file (remove longest suffix matching .*)
echo "${path#*.}"         # txt (remove shortest prefix matching *.)

# Substitution
text="foo bar foo baz"
echo "${text/foo/FOO}"    # FOO bar foo baz (first occurrence)
echo "${text//foo/FOO}"   # FOO bar FOO baz (all occurrences)
echo "${text#foo }"       # bar foo baz (remove shortest prefix)
echo "${text##foo }"      # bar foo baz (remove longest prefix)

# Default values
echo "${var:-default}"    # Use "default" if var is unset or empty
echo "${var:=default}"    # Assign "default" to var if unset or empty
echo "${var:?error msg}"  # Exit with error if var is unset or empty
echo "${var:+alternate}"  # Use "alternate" if var IS set

# sed: stream editor
echo "Hello World" | sed 's/World/Bash/'        # Hello Bash
echo "Hello World" | sed 's/world/Bash/I'       # Hello Bash (case-insensitive)
echo "  spaces  " | sed 's/^[[:space:]]*//;s/[[:space:]]*$//'  # Trim
echo "line1 line2 line3" | sed 's/ /\n/g'       # Replace space with newline
sed -i 's/old/new/g' file.txt                    # In-place edit
sed -n '5,10p' file.txt                          # Print lines 5-10
sed '/^#/d' file.txt                             # Delete comment lines

# awk: pattern scanning and processing
echo "Alice 30 Engineer" | awk '{print $1}'      # Alice (first field)
echo "Alice 30 Engineer" | awk -F: '{print $2}'  # Custom delimiter
awk '{sum += $2} END {print sum}' data.txt       # Sum column 2
awk 'NR >= 5 && NR <= 10' file.txt               # Lines 5-10
awk '$3 > 100' data.txt                          # Filter rows where col3 > 100

# cut: extract columns
echo "a:b:c:d" | cut -d: -f2                     # b
echo "abcdefgh" | cut -c1-4                       # abcd
echo "a,b,c,d" | cut -d, -f1,3                   # a,c

# tr: translate or delete characters
echo "Hello World" | tr '[:lower:]' '[:upper:]'  # HELLO WORLD
echo "hello   world" | tr -s ' '                 # hello world (squeeze spaces)
echo "abc123" | tr -d '0-9'                       # abc (delete digits)
echo "hello" | tr 'a-z' 'n-za-m'                 # rot13

# read: parse input
IFS=: read -r user _ uid gid _ home shell <<< "root:x:0:0:root:/root:/bin/bash"
echo "$user $uid $home"
```

## Common Mistakes

```bash
# WRONG: Using external commands for simple string ops
echo "$name" | tr '[:lower:]' '[:upper:]'  # Spawns a subprocess

# CORRECT: Use parameter expansion (built-in, faster)
echo "${name^^}"

# WRONG: Greedy pattern matching when non-greedy needed
path="/home/user/file.txt"
echo "${path##*/}"   # file.txt (correct for basename)
echo "${path#*/}"    # home/user/file.txt (removes only first /)

# CORRECT: Understand ## vs # and %% vs %
# ## = longest prefix match, # = shortest prefix match
# %% = longest suffix match, % = shortest suffix match

# WRONG: sed without quotes (shell globbing)
sed s/old/new/g file.txt  # Dangerous if patterns contain spaces

# CORRECT: Always quote sed expressions
sed 's/old/new/g' file.txt

# WRONG: Using sed for simple replacements in variables
result=$(echo "$text" | sed 's/foo/bar/')

# CORRECT: Use parameter expansion for variables
result="${text/foo/bar}"

# WRONG: awk field separator without -F
echo "a:b:c" | awk '{print $2}'  # Uses whitespace by default

# CORRECT: Specify delimiter
echo "a:b:c" | awk -F: '{print $2}'  # b

# WRONG: Forgetting regex special characters in sed
sed 's/file.txt/output.txt/' file.txt  # . matches any char

# CORRECT: Escape special characters
sed 's/file\.txt/output\.txt/' file.txt
```

## Gotchas
- Parameter expansion is built-in — no subprocess, faster than external commands
- `##` removes the longest match from the front; `#` removes the shortest
- `%%` removes the longest match from the end; `%` removes the shortest
- `${var:-default}` does NOT assign to var; `${var:=default}` DOES assign
- `sed -i` edits in place — on macOS, `sed -i ''` is required (no backup extension)
- `awk` fields are 1-indexed (`$1`, `$2`), not 0-indexed
- `$0` in awk is the entire line
- `tr` operates on characters, not strings — use `sed` for string replacement
- `read` splits on `$IFS` — default is space/tab/newline
- `read -r` disables backslash interpretation — always use it
- Here strings (`<<<`) are bash-specific — not POSIX sh
- `cut` cannot reorder fields; `awk` can (`{print $3, $1}`)

## Related
- bash/scripting-patterns.md
- bash/error-handling.md
- python/stdlib/regex.md
