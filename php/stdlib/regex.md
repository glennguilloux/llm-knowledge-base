---
id: "php-stdlib-regex"
title: "Regular Expressions: preg_match, preg_replace, UTF-8 Patterns"
language: "php"
category: "stdlib"
tags: ["php", "regex", "preg-match", "preg-replace", "utf-8"]
version: "8.1+"
retrieval_hint: "php regex preg_match preg_replace UTF-8 named captures patterns"
last_verified: "2026-05-24"
confidence: "high"
---

# Regular Expressions: preg_match, preg_replace, UTF-8 Patterns

## When to Use
- Validating input formats (email, phone, postal code)
- Extracting structured data from strings
- Complex string replacements with dynamic content
- Pattern matching with UTF-8 content

## Standard Pattern

```php
<?php

// --- preg_match — First Match ---
$email = 'user@example.com';
$pattern = '/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/';

if (preg_match($pattern, $email)) {
    echo "Valid email";
} else {
    echo "Invalid email";
}

// With captured groups
$logLine = 'ERROR 2024-01-15 10:30:00 Database connection failed';
$pattern = '/^(?P<level>ERROR|WARN|INFO)\s+(?P<date>\S+)\s+(?P<time>\S+)\s+(?P<message>.+)$/';

if (preg_match($pattern, $logLine, $matches)) {
    echo $matches['level'];   // ERROR
    echo $matches['message']; // Database connection failed
    echo $matches[0];         // Full match
    echo $matches[1];         // First group by number
}

// --- preg_match_all — All Matches ---
$text = 'Call us at 555-0100 or 555-0200.';
$pattern = '/(\d{3})-(\d{4})/';

preg_match_all($pattern, $text, $matches, PREG_SET_ORDER);
foreach ($matches as $match) {
    echo "Area: {$match[1]}, Number: {$match[2]}\n";
}
// Area: 555, Number: 0100
// Area: 555, Number: 0200

// --- preg_replace — Pattern Replacement ---
$text = 'The event is on 2024-01-15 at the convention center';
$result = preg_replace(
    '/(\d{4})-(\d{2})-(\d{2})/',
    '$3/$2/$1',  // Swap to day/month/year
    $text
);
// "The event is on 15/01/2024 at the convention center"

// Callback replacement
$text = 'Item #42 costs $19.99';
$result = preg_replace_callback(
    '/\$(\d+\.?\d*)/',
    function (array $matches): string {
        return '$' . number_format((float) $matches[1] * 1.1, 2);  // Add 10% tax
    },
    $text
);
// "Item #42 costs $21.99"

// --- preg_split — Split by Pattern ---
$csv = 'apple,banana,cherry';
$fruits = preg_split('/,\s*/', $csv);
// ['apple', 'banana', 'cherry']

// --- Common Patterns ---
$patterns = [
    'email'         => '/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/',
    'phone_us'      => '/^\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$/',
    'url'           => '/^https?:\/\/[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\/?.*$/',
    'ipv4'          => '/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/',
    'postal_code_us' => '/^\d{5}(-\d{4})?$/',
    'hex_color'     => '/^#([a-fA-F0-9]{6}|[a-fA-F0-9]{3})$/',
    'username'      => '/^[a-zA-Z][a-zA-Z0-9_]{2,19}$/',
];

// --- UTF-8 Patterns (use the 'u' modifier) ---
$unicodeText = 'Café München 东京';
$pattern = '/\p{L}+/u';  // Match Unicode letters
preg_match_all($pattern, $unicodeText, $matches);
// ['Café', 'München', '东京']

// Strip non-alphanumeric (preserve Unicode)
$clean = preg_replace('/[^\p{L}\p{N}\s]/u', '', $text);
```

## Common Mistakes

```php
<?php

// WRONG: Missing delimiter
$pattern = '^[a-z]+$';  // No delimiter!
// preg_match treats this as a syntax error

// CORRECT: Use forward slash delimiter
$pattern = '/^[a-z]+$/';

// For patterns containing /, use alternative delimiter:
$pattern = '#^https?://#';


// WRONG: Ignoring preg_match return type
$result = preg_match('/pattern/', $subject);
if ($result) {  // Works, but misses 0 vs false distinction
    // ...
}

// CORRECT: Use strict comparison
$result = preg_match('/pattern/', $subject);
if ($result === 1) {
    // Match found
} elseif ($result === 0) {
    // No match
} elseif ($result === false) {
    // Error occurred!
    throw new RuntimeException('preg_match error: ' . preg_last_error_msg());
}


// WRONG: Forgetting the 'u' modifier for UTF-8
$text = 'Café';
preg_match('/^[a-zA-Z]+$/', $text);  // false! 'é' is multi-byte
preg_match('/^[a-zA-Z]+$/u', $text); // true with 'u' modifier


// WRONG: Not checking preg_last_error() after complex patterns
$pattern = '/^(a+)+b$/';  // Catastrophic backtracking on "aaaaaaaaac"
$result = preg_match($pattern, 'aaaaaaaaac');
// $result is false, preg_last_error() === PREG_BACKTRACK_LIMIT_ERROR

// CORRECT: Check for errors after complex patterns
$result = preg_match($pattern, $subject);
if ($result === false) {
    // Handle PCRE error
    $error = preg_last_error_msg();
    if (preg_last_error() === PREG_BACKTRACK_LIMIT_ERROR) {
        // Simplify the pattern or increase backtrack limit
    }
}
```

## Gotchas
- **Delimiter choice**: The first character of the pattern is the delimiter (usually `/`). If your pattern contains `/`, use `#` or `~` as the delimiter instead of escaping.
- **Backtrack limit (PCRE)**: PCRE has a default backtrack limit (`pcre.backtrack_limit`, default 1M). Complex patterns on large inputs can hit this limit and silently fail (return `false`).
- **UTF-8 modifier `u`**: Without the `u` modifier, PCRE treats the subject as single-byte. This breaks for multi-byte characters like é, 中文, にほんご.
- **`^` and `$` with multiline**: By default, `^` and `$` match the start/end of the string, not lines. Use the `m` modifier to match start/end of each line.
- **Named capture groups**: Use `(?P<name>...)` for named groups. They are accessible via `$matches['name']` and `$matches[1]`. Note: `(?<name>...)` syntax also works (PHP 7+).
- **`preg_replace` with arrays**: Passing arrays for both `$pattern` and `$replacement` applies them sequentially (not simultaneously). Use `preg_replace_callback` for simultaneous replacements.
- **Empty matches**: `preg_match_all` can produce empty string matches for optional groups. Check for empty strings in results to avoid unexpected behavior.

## Related
- php/stdlib/string-operations.md
- php/stdlib/basics.md
