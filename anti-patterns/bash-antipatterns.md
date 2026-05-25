---
id: "antipatterns-bash"
title: "Bash Anti-Patterns"
language: "bash"
category: "anti-patterns"
tags: ["antipatterns", "bash", "shell", "scripting", "common-mistakes"]
version: "n/a"
retrieval_hint: "bash common mistakes quoting variables ls loop set pipefail backticks exit code"
last_verified: "2026-05-24"
confidence: "high"
---

# Bash Anti-Patterns

## When to Use
- Reviewing shell scripts for common mistakes
- Training small LLMs to avoid frequent Bash errors
- CI/CD pipeline script review
- Onboarding developers new to Bash scripting

## Standard Pattern

```bash
# WRONG: Unquoted variable (word splitting + globbing)
for file in $(ls *.txt); do
    cat $file  # Breaks on filenames with spaces
done

# CORRECT: Quote variables and use glob directly
for file in *.txt; do
    cat "$file"
done

# WRONG: Parsing ls output (fails on special characters)
for file in $(ls /path/to/dir); do
    process "$file"
done

# CORRECT: Use glob or find
for file in /path/to/dir/*; do
    process "$file"
done

# WRONG: cat file | grep (useless use of cat)
cat /var/log/syslog | grep "error"

# CORRECT: grep reads the file directly
grep "error" /var/log/syslog

# WRONG: No set -euo pipefail (errors silently ignored)
#!/bin/bash
cd /nonexistent/path
rm -rf *  # Runs even if cd failed — deletes from wrong directory!

# CORRECT: Use set -euo pipefail
#!/bin/bash
set -euo pipefail
cd /nonexistent/path  # Script exits here — rm never runs
rm -rf *

# WRONG: Using backticks (hard to read, can't nest)
result=`grep -c "error" \`find /var/log -name "*.log"\``

# CORRECT: Use $() (readable, nestable)
result=$(grep -c "error" $(find /var/log -name "*.log"))

# WRONG: Not checking exit codes
cp important_file /backup/
echo "Backup complete"  # Prints even if cp failed

# CORRECT: Check exit codes or use set -e
cp important_file /backup/ || { echo "Backup failed"; exit 1; }

# WRONG: Using [ ] with string variables that might be empty
if [ $filename = "test.txt" ]; then  # Fails if $filename is empty
    echo "match"
fi

# CORRECT: Quote the variable
if [ "$filename" = "test.txt" ]; then
    echo "match"
fi

# WRONG: Temporary file without cleanup
tmpfile=$(mktemp)
process > "$tmpfile"
# tmpfile never cleaned up on error

# CORRECT: Trap for cleanup
tmpfile=$(mktemp)
trap 'rm -f "$tmpfile"' EXIT
process > "$tmpfile"

# WRONG: Array iteration with for-in
for item in ${items[@]}; do
    echo "$item"
done

# CORRECT: Quote the array expansion
for item in "${items[@]}"; do
    echo "$item"
done
```

## Common Mistakes
The most damaging Bash anti-patterns are unquoted variables (word splitting on spaces, glob expansion of `*`), parsing `ls` output (breaks on special characters), and missing `set -euo pipefail` (errors silently ignored, commands run in wrong directory). Using backticks instead of `$()` reduces readability and prevents nesting.

## Gotchas
- Always quote `"$variables"` — unquoted expansion splits on whitespace and expands globs
- `set -e` does NOT catch errors inside pipes — use `set -o pipefail` as well
- `set -u` treats unset variables as errors — safer than silent empty expansion
- `$()` subshells can be nested; backticks `` `\` `` cannot
- `for file in $(ls)` breaks on spaces; `for file in *` does not
- `trap EXIT` runs cleanup even on errors — use it for temp files and locks
- `[ "$var" ]` is safer than `[ $var ]` — empty `$var` without quotes causes syntax error

## Related
- bash/scripting-patterns.md
- bash/testing-debugging.md
- error-handling/structured-errors.md
- devops/ci-cd/github-actions.md
