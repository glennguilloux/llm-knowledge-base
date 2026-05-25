---
id: "bash-awk-sed-deep"
title: "Advanced awk and sed: Field Processing, In-Place Editing, Multi-Line"
language: "bash"
category: "stdlib"
tags: ["bash", "awk", "sed", "text-processing", "stream-editing"]
version: "n/a"
retrieval_hint: "bash awk sed advanced field processing associative arrays in-place multi-line patterns"
last_verified: "2026-05-24"
confidence: "high"
---

# Advanced awk and sed: Field Processing, In-Place Editing, Multi-Line

## When to Use
- Processing structured text files (CSV, logs, configs)
- Extracting and transforming columns from text
- Performing complex find-and-replace operations
- Multi-line pattern matching and substitution

## Standard Pattern

```bash
# === Advanced awk ===

# --- Field Processing ---
# Print columns 2 and 4 from a CSV (comma-separated)
awk -F',' '{print $2, $4}' data.csv

# Custom output format
awk -F',' '{printf "%-20s %10s\n", $2, $4}' data.csv

# Field calculation
awk '{total += $NF} END {print "Total:", total}' numbers.txt

# --- Associative Arrays ---
# Count occurrences (like a hash map)
awk '{count[$1]++} END {for (key in count) print key, count[key]}' server.log

# Group by category
awk -F',' '{sales[$1] += $3} END {for (cat in sales) print cat, sales[cat]}' sales.csv

# --- Pattern Ranges ---
# Print lines between START and END markers
awk '/START/,/END/' file.txt

# Match lines before/after a pattern
awk '/error/ {print NR-1 ": " prev} {prev = $0}' log.txt

# --- Multi-line Processing ---
# Record separator for paragraph mode (blank-line separated)
awk 'BEGIN {RS=""; FS="\n"} {print "Record:", $1, $2}' contacts.txt

# --- Built-in Variables ---
# NR   — Current record number (line number)
# NF   — Number of fields in current record
# FS   — Field separator (default whitespace)
# OFS  — Output field separator
# RS   — Record separator (default newline)
# ORS  — Output record separator
# FILENAME — Current file name

# --- awk Script File (for complex logic) ---
# analysis.awk
# BEGIN { FS = ","; print "Starting..." }
# /error|warning/ { count[$1]++; total++ }
# END {
#     for (level in count)
#         printf "%s: %d (%.1f%%)\n", level, count[level], count[level]/total*100
# }
# Usage: awk -f analysis.awk log.csv


# === Advanced sed ===

# --- In-Place Editing ---
# GNU sed (Linux)
sed -i 's/foo/bar/g' file.txt

# BSD sed (macOS) — requires backup extension
sed -i '' 's/foo/bar/g' file.txt
# Cross-platform alternative:
sed -i.bak 's/foo/bar/g' file.txt && rm file.txt.bak

# --- Address Ranges ---
# Lines 10-20
sed -n '10,20p' file.txt

# Delete lines 5-10
sed '5,10d' file.txt

# Match range: from line matching START until END
sed -n '/START/,/END/p' file.txt

# --- Multi-Line Operations ---
# Join lines (replace newlines with spaces)
sed ':a;N;$!ba;s/\n/ /g' file.txt

# Replace across lines — match "foo\nbar" and replace
sed '/foo/{N;s/foo\nbar/baz/}' file.txt

# --- Capture Groups ---
# Replace matched group with transformed text
sed -E 's/([0-9]{3})-([0-9]{4})/(\1) \2/' phones.txt

# Uppercase backreference
sed -E 's/\b([a-z])/\u\1/g' file.txt  # Capitalize first letter of each word

# --- Common Recipes ---
# Remove trailing whitespace
sed -i 's/[[:space:]]*$//' file.txt

# Remove blank lines
sed -i '/^$/d' file.txt

# Indent file 4 spaces
sed 's/^/    /' file.txt

# Surround matching lines
sed '/PATTERN/{s/^/<!-- /;s/$/ -->/}' file.html

# Print line numbers before matching lines
sed -n '/error/{=;p}' log.txt | sed 'N;s/\n/: /'
```

## Common Mistakes

```bash
# WRONG: BSD vs GNU sed -i syntax (portability)
sed -i 's/foo/bar/g' file.txt  # Works on GNU, FAILS on macOS

# CORRECT: Handle both
if [[ "$(uname)" == "Darwin" ]]; then
    sed -i '' 's/foo/bar/g' file.txt
else
    sed -i 's/foo/bar/g' file.txt
fi


# WRONG: Not quoting awk scripts (shell expands $ variables)
awk {print $1,$2} file.txt  # Shell interprets $1 as empty!

# CORRECT: Single quotes around awk script
awk '{print $1, $2}' file.txt


# WRONG: Forgetting FS/OFS in awk output
awk -F':' '{print $1,$2}' /etc/passwd
# Default OFS is space, output is "root /bin/bash"
# Issue if you need colon-separated output

# CORRECT: Set OFS explicitly
awk -F':' 'BEGIN {OFS=":"} {print $1, $6}' /etc/passwd


# WRONG: Using sed with regex special characters without escaping
sed -i 's/foo.bar/baz/g' file.txt  # . matches ANY character, not literal dot

# CORRECT: Escape literal characters
sed -i 's/foo\.bar/baz/g' file.txt

# Or use extended regex with -E for cleaner patterns
sed -E 's/foo\.bar/baz/g' file.txt


# WRONG: awk memory with large arrays (accumulating all data)
awk '{data[NR] = $0} END {for (i in data) print data[i]}' huge.log
# Stores entire file in memory!

# CORRECT: Process line by line (or use sort | uniq)
awk '{count[$1]++} END {for (k in count) print k, count[k]}' huge.log
# Stores only unique keys, not all lines
```

## Gotchas
- **GNU vs BSD sed**: GNU sed uses `-i` without argument for in-place. BSD sed (macOS) requires `-i ''` with an empty backup extension. Always check which version you're on.
- **Locale affecting character classes**: `[[:upper:]]` and `[a-z]` behave differently with different locales. Set `LC_ALL=C` for consistent ASCII matching in both awk and sed.
- **awk field separators**: `FS` set to a single character is a literal character. Set to a regex (e.g., `FS=[,\t]`) for complex separators. Multiple-character FS values with `-F` require wrapping in brackets.
- **NR vs FNR**: `NR` is the total record number across all files. `FNR` is the record number within the current file. Use `FNR == 1` to detect the first line of each file.
- **sed branch labels**: GNU sed uses `:label` for branch labels and `b label` for branch. BSD sed has different label syntax. Multi-line sed scripts with branches are not portable without testing.
- **awk associative array order**: When iterating with `for (key in array)`, the order is not guaranteed. Use a separate sort step or `PROCINFO["sorted_in"]` in GNU awk.
- **Backreferences in sed replacement**: Use `\1`, `\2` for capture groups. `\u` (uppercase) and `\l` (lowercase) are GNU extensions. Not available in BSD sed.

## Related
- bash/text-processing.md
- bash/string-manipulation.md
