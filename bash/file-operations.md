---
id: "bash-file-operations"
title: "Bash File Operations: find, xargs, rsync, mktemp, and Log Rotation"
language: "bash"
category: "stdlib"
tags: ["bash", "find", "xargs", "rsync", "mktemp", "log-rotation", "inotifywait"]
version: "n/a"
retrieval_hint: "bash find with exec xargs rsync basics inotifywait checking file age rotating logs temp files mktemp"
last_verified: "2026-05-24"
confidence: "high"
---

# Bash File Operations: find, xargs, rsync, mktemp, and Log Rotation

## When to Use
- Searching for files with `find` and processing results
- Synchronizing files with `rsync`
- Creating safe temporary files with `mktemp`
- Monitoring files with `inotifywait`
- Rotating and archiving log files

## Standard Pattern

```bash
#!/bin/bash
set -euo pipefail

# find — search for files
# Find all .log files modified in the last 7 days
find /var/log -name "*.log" -mtime -7

# Find and execute command on each file (safer than xargs for special chars)
find /path -name "*.txt" -exec gzip {} \;

# Find with -exec + (more efficient — batches files)
find /path -name "*.txt" -exec gzip {} +

# Find and use with xargs (classic pattern)
find /path -name "*.log" -print0 | xargs -0 rm -f
# -print0: null-separated output (handles spaces in filenames)
# -0: null-separated input

# Find by size
find /var/log -size +100M -name "*.log"

# Find empty files/dirs
find /tmp -empty -type f

# Find and delete files older than 30 days
find /tmp/old-files -type f -mtime +30 -delete

# rsync — synchronize files (efficient, incremental)
rsync -av /source/ /destination/
# -a: archive mode (recursive, preserves permissions, symlinks, timestamps)
# -v: verbose

# Sync over SSH
rsync -avz /source/ user@remote:/destination/

# Dry run
rsync -av --dry-run /source/ /destination/

# Delete files in destination that don't exist in source
rsync -av --delete /source/ /destination/

# mktemp — create safe temporary files
tmpfile=$(mktemp)
echo "Working data" > "$tmpfile"
process "$tmpfile"
rm -f "$tmpfile"

# Temp directory
tmpdir=$(mktemp -d)
cd "$tmpdir"
# ... work ...
rm -rf "$tmpdir"

# Ensure temp file is cleaned up on exit
tmpfile=$(mktemp)
trap 'rm -f "$tmpfile"' EXIT

# Check file age
is_file_older_than() {
    local file="$1"
    local minutes="$2"
    if [[ ! -f "$file" ]]; then
        return 0
    fi
    local age_minutes=$(( ($(date +%s) - $(stat -c %Y "$file")) / 60 ))
    [[ $age_minutes -gt $minutes ]]
}

# Rotate logs (simple version)
rotate_log() {
    local logfile="$1"
    local max_size=$((50 * 1024 * 1024))  # 50MB
    if [[ -f "$logfile" ]]; then
        local size=$(stat -c %s "$logfile")
        if [[ $size -gt $max_size ]]; then
            mv "$logfile" "$logfile.$(date +%Y%m%d%H%M%S)"
            touch "$logfile"
            gzip "$logfile".* &
        fi
    fi
}

# inotifywait — watch for file changes (requires inotify-tools)
inotifywait -m -e modify /path/to/watch/ | while read -r directory event filename; do
    echo "File $filename was modified"
    process_file "$directory/$filename"
done
```

## Common Mistakes

```bash
# WRONG: Using find | xargs without -print0/-0 (breaks on spaces)
find /path -name "*.txt" | xargs rm
# File "my document.txt" becomes two arguments!

# CORRECT: Use -print0 and -0
find /path -name "*.txt" -print0 | xargs -0 rm

# WRONG: Not using trap for temp file cleanup
tmpfile=$(mktemp)
process "$tmpfile"
rm "$tmpfile"  # If process fails, temp file is never cleaned up!

# CORRECT: Use trap
tmpfile=$(mktemp)
trap 'rm -f "$tmpfile"' EXIT
process "$tmpfile"

# WRONG: Not checking if file exists before operating
stat -c %s "$file"  # Error if file doesn't exist!

# CORRECT: Check first
if [[ -f "$file" ]]; then
    size=$(stat -c %s "$file")
fi

# WRONG: Using > instead of >> for log rotation (truncates file)
echo "Rotation: $(date)" > /var/log/app.log

# CORRECT: Rename old log, create new one
mv /var/log/app.log /var/log/app.log.old
touch /var/log/app.log
```

## Gotchas
- `find -exec {} +` is more efficient than `find -exec {} \;` because it batches files.
- `find | xargs` without `-print0/-0` breaks on filenames with spaces.
- `rsync -a` preserves permissions, symlinks, timestamps, and is recursive.
- `rsync --dry-run` shows what would happen without actually doing it.
- `mktemp` creates files with restrictive permissions (600) — safer than manual temp files.
- `trap EXIT` ensures cleanup runs even on script errors or interruptions.
- `inotifywait` requires the `inotify-tools` package.
- Log rotation: rename the current log, create a new one, compress old logs in background.

## Related
- bash/network-operations.md
- bash/text-processing.md
- bash/scripting-patterns.md
- bash/git-automation.md
