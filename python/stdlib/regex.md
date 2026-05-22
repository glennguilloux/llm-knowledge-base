---
id: "python-stdlib-regex"
title: "Regular Expressions with re Module"
language: "python"
category: "stdlib"
tags: ["regex", "re", "pattern", "matching", "string", "parsing"]
version: "3.10+"
retrieval_hint: "regex re match search findall compile pattern regular expression"
last_verified: "2026-05-22"
confidence: "high"
---

# Regular Expressions with re Module

## When to Use
- Pattern matching in strings (email, phone, URL validation)
- Text extraction from unstructured data
- String transformation beyond simple replace
- Parsing log files or structured text formats

## Standard Pattern

```python
import re

# Basic matching
text = "Order #12345 shipped on 2024-01-15"

# re.search — find first match anywhere in string
match = re.search(r"#(\d+)", text)
if match:
    order_id = match.group(1)  # "12345"

# re.findall — find all matches
dates = re.findall(r"\d{4}-\d{2}-\d{2}", text)  # ["2024-01-15"]

# re.match — match only at start of string
m = re.match(r"Order", text)  # Matches
m = re.match(r"shipped", text)  # None — not at start

# Named groups
pattern = r"(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})"
match = re.search(pattern, text)
if match:
    print(match.group("year"))   # "2024"
    print(match.groupdict())     # {'year': '2024', 'month': '01', 'day': '15'}

# Compile for reuse (performance)
EMAIL_PATTERN = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.]+$")
EMAIL_PATTERN.match("user@example.com")  # True

# Substitution
text = "Call 555-1234 or 555-5678"
masked = re.sub(r"\d{3}-\d{4}", "XXX-XXXX", text)
# "Call XXX-XXXX or XXX-XXXX"

# Split
parts = re.split(r"[,;]\s*", "apple, banana; cherry")  # ["apple", "banana", "cherry"]

# Flags
re.search(r"^line", "First\nLine", re.MULTILINE | re.IGNORECASE)

# Greedy vs lazy
text = "<b>bold</b> and <i>italic</i>"
greedy = re.findall(r"<.*>", text)    # ["<b>bold</b> and <i>italic</i>"]
lazy = re.findall(r"<.*?>", text)     # ["<b>", "</b>", "<i>", "</i>"]

# Lookahead and lookbehind
text = "price: $100, qty: 5"
amounts = re.findall(r"\$(\d+)", text)  # ["100"]

# Positive lookbehind
prices = re.findall(r"(?<=\$)\d+", text)  # ["100"]

# Common patterns
PHONE = re.compile(r"^\+?1?\d{9,15}$")
URL = re.compile(r"https?://[\w.-]+(?:/[\w./-]*)?")
IPV4 = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")
```

## Common Mistakes

```python
# WRONG: Using re.match when you mean re.search
result = re.match(r"\d+", "Order 123")  # None — match only checks start

# CORRECT: Use re.search for anywhere in string
result = re.search(r"\d+", "Order 123")  # Match object

# WRONG: Forgetting raw string
pattern = "\d+"  # \d is just 'd' in regular string

# CORRECT: Use raw string for regex
pattern = r"\d+"  # \d is regex digit class

# WRONG: Not escaping special characters
re.search(f"user.{name}", input)  # . matches any character

# CORRECT: Escape user input
re.search(f"user\\.{re.escape(name)}", input)

# WRONG: Greedy match capturing too much
html = "<p>hello</p><p>world</p>"
re.findall(r"<p>.*</p>", html)  # ["<p>hello</p><p>world</p>"]

# CORRECT: Use lazy quantifier
re.findall(r"<p>.*?</p>", html)  # ["<p>hello</p>", "<p>world</p>"]

# WRONG: Using regex for simple string operations
if re.search("hello", text):  # Overkill for literal matching

# CORRECT: Use string methods for simple cases
if "hello" in text:
    pass

# WRONG: Not using compiled pattern in loop
for line in lines:
    if re.search(r"\d{4}-\d{2}-\d{2}", line):  # Recompiles every iteration

# CORRECT: Compile once
DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
for line in lines:
    if DATE_PATTERN.search(line):
        pass
```

## Gotchas
- `re.match` only matches at the START of the string — use `re.search` for anywhere
- `.` matches any character EXCEPT newline by default — use `re.DOTALL` flag for newlines
- `*` and `+` are greedy by default — add `?` for lazy matching (`.*?`)
- `\d` matches `[0-9]` only — not Unicode digits unless `re.ASCII` flag is used
- `re.findall` with groups returns the group content, not the full match
- `re.compile` patterns are cached by Python, but explicit compile is clearer for reuse
- Raw strings (`r""`) are essential — `\n` in a regular string is a newline, not `\n` regex
- Capturing groups change `re.findall` return type — from full match to group only
- `^` and `$` match start/end of string by default — `re.MULTILINE` makes them match line boundaries

## Related
- python/stdlib/file-io.md
- python/stdlib/decorators.md
- python/web/fastapi/request-validation.md
