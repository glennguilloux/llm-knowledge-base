---
id: "bash-text-processing"
title: "Bash Text Processing: awk, sed, grep, and Column Formatting"
language: "bash"
category: "stdlib"
tags: ["bash", "awk", "sed", "grep", "cut", "sort", "uniq", "column", "csv"]
version: "n/a"
retrieval_hint: "bash awk one-liners sed common patterns grep Extended cut sort uniq tee column formatting CSV handling"
last_verified: "2026-05-24"
confidence: "high"
---

# Bash Text Processing: awk, sed, grep, and Column Formatting

## When to Use
- Processing and transforming text in shell scripts
- Parsing log files and CSV data
- Extracting specific fields from structured text
- Searching and replacing text patterns

## Standard Pattern

```bash
#!/bin/bash
set -euo pipefail

# grep — search for patterns
grep "error" /var/log/app.log           # Basic search
grep -i "warning" /var/log/app.log      # Case-insensitive
grep -E "error|warning|fatal" /var/log/app.log  # Extended regex
grep -v "^#" config.conf                # Exclude comments
grep -c "error" /var/log/app.log        # Count matches
grep -n "error" /var/log/app.log        # Show line numbers
grep -r "TODO" /src/ --include="*.py"   # Recursive search
grep -C 3 "error" /var/log/app.log      # Context (3 lines before/after)
grep -o "[0-9]\+\.[0-9]\+\.[0-9]\+" versions.txt  # Extract matching part

# sed — stream editor (find and replace)
sed 's/old/new/' file.txt               # Replace first occurrence per line
sed 's/old/new/g' file.txt              # Replace all occurrences (global)
sed -i 's/old/new/g' file.txt           # Replace in-place (modify file)
sed '/^#/d' config.conf                 # Delete comment lines
sed '/^$/d' file.txt                    # Delete empty lines
sed -n '10,20p' file.txt                # Extract lines 10-20

# awk — field processing
awk '{print $1, $3}' file.txt           # Print columns 1 and 3
awk -F',' '{print $1, $3}' data.csv     # Custom field separator (CSV)
awk '$3 > 100 {print $1, $3}' data.txt  # Filter rows by condition
awk '{sum += $2} END {print "Total:", sum}' numbers.txt  # Sum a column
awk '{count[$1]++} END {for (word in count) print count[word], word}' words.txt
awk 'BEGIN {print "Name:Score"} $2 > 80 {print $1":"$2} END {print "Done"}' scores.txt

# cut — extract columns
cut -d',' -f1,3 data.csv                # Columns 1 and 3 from CSV
cut -c1-10 file.txt                     # Characters 1-10 of each line

# sort — sort lines
sort file.txt                           # Alphabetical
sort -n numbers.txt                     # Numeric sort
sort -rn numbers.txt                    # Reverse numeric (highest first)
sort -t',' -k2 -n data.csv              # Sort by column 2 (numeric, CSV)
sort -u file.txt                        # Unique (remove duplicates)
sort file.txt | uniq -c                 # Count occurrences

# column — format output as columns
ls -l | column -t                       # Align columns nicely

# paste — merge lines from multiple files
paste file1.txt file2.txt               # Side by side
paste -d',' file1.txt file2.txt         # CSV-style

# tee — write to file AND stdout
echo "Processing..." | tee -a log.log

# tr — translate characters
echo "hello world" | tr 'a-z' 'A-Z'     # Uppercase
echo "hello   world" | tr -s ' '         # Squeeze multiple spaces to one

# wc — word/line count
wc -l file.txt                          # Line count
wc -w file.txt                          # Word count
```

## Common Mistakes

```bash
# WRONG: Using grep without -E for extended regex
grep "error|warning" file.txt  # Searches for literal "error|warning"!

# CORRECT: Use -E for extended regex
grep -E "error|warning" file.txt

# WRONG: Not escaping + in basic grep
grep "colou?r" file.txt  # ? is literal in basic regex

# CORRECT: Use -E for special characters
grep -E "colou?r" file.txt

# WRONG: Using sed -i on macOS without backup
sed -i 's/old/new/g' file.txt  # macOS requires argument after -i

# CORRECT: macOS: sed -i '' 's/old/new/g' file.txt

# WRONG: Not quoting $ in sed (shell expands it)
sed "s/$var/new/g" file.txt  # Shell expands $var!

# CORRECT: Use single quotes or escape
sed 's/'$var'/new/g' file.txt

# WRONG: Forgetting that awk fields are 1-indexed
awk '{print $0}' file.txt  # $0 is the whole line
awk '{print $1}' file.txt  # First column

# WRONG: Using cat unnecessarily (UUOC)
cat file.txt | grep "pattern"

# CORRECT: grep reads files directly
grep "pattern" file.txt

# WRONG: Not handling header in CSV processing
awk '{sum += $3} END {print sum}' data.csv  # Includes header row!

# CORRECT: Skip header
awk 'NR > 1 {sum += $3} END {print sum}' data.csv
```

## Gotchas
- `grep -E` enables extended regex (supports `+`, `?`, `|`, `()`). Without it, use `egrep`.
- `sed -i` modifies files in-place. On macOS, you must provide an extension argument.
- `awk` fields are 1-indexed (`$1` is first, `$0` is the whole line).
- `awk -F` sets the field separator. For CSV, use `-F','`.
- `sort -n` for numeric sort. Without it, `10` sorts before `2`.
- `uniq` only removes ADJACENT duplicates. Pipe through `sort` first.
- `cut -d` sets the delimiter. `cut -c` extracts by character position.
- `column -t` aligns output into neat columns.
- `tee -a` appends to file while also printing to stdout.
- `tr` only translates single characters, not strings. Use `sed` for string replacement.

## Related
- bash/network-operations.md
- bash/file-operations.md
- bash/git-automation.md
- bash/scripting-patterns.md
