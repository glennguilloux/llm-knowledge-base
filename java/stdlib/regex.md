---
id: "java-stdlib-regex"
title: "Regex with Pattern and Matcher"
language: "java"
category: "stdlib"
tags: ["regex", "Pattern", "Matcher", "regular-expression", "matching", "groups"]
version: "17+"
retrieval_hint: "regex Pattern Matcher regular expression matching groups compile find"
last_verified: "2026-05-24"
confidence: "high"
---

# Regex with Pattern and Matcher

## When to Use
- Validating structured strings (emails, phone numbers, IPs)
- Extracting data from text (log parsing, data extraction)
- Search and replace in strings with complex patterns
- Splitting strings on complex delimiters

## Standard Pattern

```java
import java.util.regex.Pattern;
import java.util.regex.Matcher;
import java.util.List;
import java.util.ArrayList;

public class RegexUtils {

    // --- Compile pattern once, reuse many times ---
    private static final Pattern EMAIL_PATTERN = Pattern.compile(
        "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"
    );

    private static final Pattern DATE_PATTERN = Pattern.compile(
        "(?<year>\\d{4})-(?<month>\\d{2})-(?<day>\\d{2})"
    );

    // --- Basic matching ---
    public static boolean isValidEmail(String email) {
        return EMAIL_PATTERN.matcher(email).matches();
    }

    // --- Finding all matches ---
    public static List<String> extractEmails(String text) {
        List<String> emails = new ArrayList<>();
        Matcher matcher = EMAIL_PATTERN.matcher(text);
        while (matcher.find()) {
            emails.add(matcher.group());
        }
        return emails;
    }

    // --- Named groups ---
    public static DateParts parseDate(String text) {
        Matcher matcher = DATE_PATTERN.matcher(text);
        if (matcher.find()) {
            return new DateParts(
                matcher.group("year"),
                matcher.group("month"),
                matcher.group("day")
            );
        }
        return null;
    }

    record DateParts(String year, String month, String day) {}

    // --- Replace ---
    public static String redactEmails(String text) {
        return EMAIL_PATTERN.matcher(text).replaceAll("[REDACTED]");
    }

    // --- Split ---
    public static List<String> splitOnDelimiters(String text) {
        return List.of(Pattern.compile("[,;|]").split(text));
    }

    // --- Case-insensitive matching ---
    private static final Pattern KEYWORD = Pattern.compile(
        "error", Pattern.CASE_INSENSITIVE | Pattern.MULTILINE
    );

    public static List<String> findErrors(String log) {
        List<String> matches = new ArrayList<>();
        Matcher matcher = KEYWORD.matcher(log);
        while (matcher.find()) {
            matches.add(matcher.group());
        }
        return matches;
    }

    // --- Greedy vs lazy ---
    public static String extractFirstTag(String html) {
        // Greedy: .* matches as much as possible
        Pattern greedy = Pattern.compile("<p>.*</p>");
        // Lazy: .*? matches as little as possible
        Pattern lazy = Pattern.compile("<p>(.*?)</p>");
        Matcher matcher = lazy.matcher(html);
        return matcher.find() ? matcher.group(1) : null;
    }
}
```

## Common Mistakes

```java
// WRONG: Compiling pattern inside loop (recompiles every iteration)
for (String line : lines) {
    if (Pattern.compile("\\d{4}-\\d{2}-\\d{2}").matcher(line).find()) {
        process(line);
    }
}

// CORRECT: Compile once, reuse
private static final Pattern DATE = Pattern.compile("\\d{4}-\\d{2}-\\d{2}");
for (String line : lines) {
    if (DATE.matcher(line).find()) {
        process(line);
    }
}

// WRONG: Using matches() when you mean find()
Pattern.compile("\\d+").matcher("Order 123").matches();  // false! matches() requires full string match

// CORRECT: Use find() for partial match
Pattern.compile("\\d+").matcher("Order 123").find();  // true

// WRONG: Not escaping backslashes
Pattern.compile("\d+");  // Compile error! \d is not a valid Java escape

// CORRECT: Double-escape or use text block
Pattern.compile("\\d+");
// Or Java 15+:
Pattern.compile("""\d+""");  // Text block — single backslash works

// WRONG: Using String.split() without escaping
"file.txt".split(".");  // Splits on any character! . is regex wildcard

// CORRECT: Escape special characters
"file.txt".split("\\.");  // Splits on literal dot

// WRONG: Using regex for simple string operations
if (Pattern.compile("hello").matcher(text).find()) { ... }

// CORRECT: Use String methods for simple cases
if (text.contains("hello")) { ... }
```

## Gotchas
- `Pattern.compile()` is expensive — compile once and store as a `static final` field
- `matches()` requires the ENTIRE string to match; `find()` searches for a match anywhere
- Java string literals require double backslashes: `\\d` for regex `\d`
- `Matcher.find()` advances an internal cursor — call `matcher.reset()` to reuse
- `Pattern.MULTILINE` makes `^` and `$` match line boundaries, not just string boundaries
- Named groups use `(?<name>...)` syntax — access with `matcher.group("name")`
- `Pattern.CASE_INSENSITIVE` only works for ASCII; use `Pattern.UNICODE_CASE` for Unicode

## Related
- java/stdlib/file-io.md
- java/stdlib/exception-handling.md
