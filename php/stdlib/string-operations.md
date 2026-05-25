---
id: "php-stdlib-string-operations"
title: "PHP String Operations: Interpolation, Multibyte, and Common Methods"
language: "php"
category: "stdlib"
tags: ["php", "strings", "interpolation", "heredoc", "mbstring", "sprintf", "utf-8"]
version: "8.2+"
retrieval_hint: "php string interpolation heredoc nowdoc mb_ functions UTF-8 common string methods sprintf concatenation"
last_verified: "2026-05-24"
confidence: "high"
---

# PHP String Operations: Interpolation, Multibyte, and Common Methods

## When to Use
- Building strings with variables and expressions
- Handling multibyte/UTF-8 text correctly
- Choosing between string concatenation, interpolation, and sprintf
- Trimming, searching, and replacing text

## Standard Pattern

```php
<?php

// Double-quoted strings support variable interpolation
$name = 'Alice';
$greeting = "Hello, $name!";          // "Hello, Alice!"
$detail = "Name length: {strlen($name)}";  // Use {} for expressions
$item = "Value: {$array['key']}";    // Use {} for array access

// Single-quoted strings do NOT interpolate
$literal = 'Hello, $name';            // Literally: "$name"

// Heredoc — multiline string with interpolation (like double-quoted)
$html = <<<HTML
<!DOCTYPE html>
<html>
<head><title>{$pageTitle}</title></head>
<body>
    <h1>Hello, {$name}!</h1>
    <p>Welcome to our site.</p>
</body>
</html>
HTML;

// Nowdoc — multiline string WITHOUT interpolation (like single-quoted)
$code = <<<'PHP'
<?php
$variable = "This is NOT interpolated";
echo $variable;
PHP;

// Multibyte string functions (mb_*) for UTF-8
$text = "こんにちは世界";  // Japanese text

// WRONG: strlen counts BYTES, not characters
$wrong = strlen($text);  // 21 bytes, not 7 characters

// CORRECT: Use mb_strlen for character count
$correct = mb_strlen($text);  // 7 characters

// Other mb_ functions for UTF-8
$sub = mb_substr($text, 0, 3);     // "こんに"  (first 3 characters)
$pos = mb_strpos($text, '世界');    // 5
$lower = mb_strtolower('CAFE');     // "cafe"
$upper = mb_strtoupper('cafe');    // "CAFE"

// Common string methods
$text = "  Hello, World!  ";

$trimmed = trim($text);              // "Hello, World!"
$ltrim = ltrim($text);              // "Hello, World!  "
$rtrim = rtrim($text);              // "  Hello, World!"

$lower = strtolower($text);         // "  hello, world!  "
$upper = strtoupper($text);         // "  HELLO, WORLD!  "
$ucfirst = ucfirst('hello');        // "Hello"
$lcfirst = lcfirst('Hello');        // "hello"
$ucwords = ucwords('hello world');  // "Hello World"

$replaced = str_replace('World', 'PHP', "Hello, World!");  // "Hello, PHP!"
$insensitive = str_ireplace('world', 'PHP', "Hello, World!");  // Case-insensitive
$contains = str_contains('Hello World', 'World');  // true (PHP 8.0+)
$startsWith = str_starts_with('Hello World', 'Hello');  // true (PHP 8.0+)
$endsWith = str_ends_with('Hello World', 'World');  // true (PHP 8.0+)

$repeated = str_repeat('-', 10);     // "----------"
$reversed = str_rev('hello');       // "olleh"
$shuffled = str_shuffle('hello');    // Random shuffle

// sprintf for formatted strings
$formatted = sprintf('User: %s (ID: %d)', $name, 42);
// "User: Alice (ID: 42)"

$price = sprintf('$%.2f', 19.99);  // "$19.99"
$padded = sprintf('%05d', 42);      // "00042"

// Concatenation with . operator
$fullName = $firstName . ' ' . $lastName;

// Explode and implode
$tags = 'php,kotlin,python';
$tagArray = explode(',', $tags);     // ['php', 'kotlin', 'python']
$backToString = implode(', ', $tagArray);  // "php, python, kotlin"

// str_contains, str_starts_with, str_ends_with (PHP 8.0+) — preferred over strpos
if (str_contains($text, 'World')) {  // Clear intent
    // ...
}

// vs old way (PHP 7.x and earlier)
if (strpos($text, 'World') !== false) {  // Must use !== false (returns 0 for position 0!)
    // ...
}
```

## Common Mistakes

```php
<?php

// WRONG: Using strlen for multibyte strings
$utf8 = "café";
$len = strlen($utf8);  // 5 bytes (é is 2 bytes in UTF-8)

// CORRECT: Use mb_strlen for character count
$len = mb_strlen($utf8);  // 4 characters

// WRONG: Using strpos without strict comparison
if (strpos('Hello World', 'Hello')) {
    // This is FALSE! 'Hello' is at position 0, which is falsy
}

// CORRECT: Use strict comparison
if (strpos('Hello World', 'Hello') !== false) {
    // TRUE — found at position 0
}

// WRONG: For mb_strpos also needs strict comparison
if (mb_strpos($utf8, 'caf')) {
    // FALSE — found at position 0, which is falsy
}

// CORRECT: Strict comparison for all position functions
if (mb_strpos($utf8, 'caf') !== false) {
    // TRUE
}

// PHP 8.0+ preferred way:
if (str_contains($utf8, 'caf')) {
    // TRUE — no position confusion
}

// WRONG: Using concatenation when interpolation is cleaner
$greeting = "Hello, " . $name . "! You have " . $count . " new messages.";

// CORRECT: Use double-quoted string interpolation
$greeting = "Hello, $name! You have $count new messages.";

// WRONG: Setting wrong internal encoding
// mb_ functions use internal encoding — set it explicitly

// CORRECT: Set UTF-8 encoding
mb_internal_encoding('UTF-8');
mb_http_output('UTF-8');

// WRONG: Not escaping output in HTML context
echo "Hello, $name";  // XSS vulnerability if $name contains <script>!

// CORRECT: Always escape output
echo "Hello, " . htmlspecialchars($name, ENT_QUOTES, 'UTF-8');
```

## Gotchas
- `strlen()` counts **bytes**, not **characters**. For UTF-8 text, always use `mb_strlen()`.
- `strpos()` returns `0` when the needle is at position 0, which is falsy. Use `!== false` to check.
- PHP 8.0 added `str_contains()`, `str_starts_with()`, `str_ends_with()` — these are clearer than `strpos()`.
- Double-quoted strings interpolate variables. Single-quoted strings do not.
- Heredoc (`<<<EOT`) interpolates, Nowdoc (`<<<'EOT'`) does not.
- Set `mb_internal_encoding('UTF-8')` at application startup for consistent mb_ behavior.
- `htmlspecialchars()` with `ENT_QUOTES` and `UTF-8` is essential for preventing XSS.
- `explode()` with an empty delimiter throws `ValueError` in PHP 8.0+ (was `warning` before).
- String concatenation with `.` is fine for small strings. For large strings, use `implode()` or output buffering.

## Related
- php/stdlib/basics.md
- php/stdlib/arrays.md
- php/security/common-vulnerabilities.md
