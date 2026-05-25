---
id: "typescript-stdlib-string-operations"
title: "TypeScript String Operations"
language: "typescript"
category: "stdlib"
subcategory: "text"
tags: ["strings", "template-literals", "regex", "formatting", "parsing", "number-conversion"]
version: "5.0+"
retrieval_hint: "TypeScript string template literals regex match number conversion formatting"
last_verified: "2026-05-24"
confidence: "high"
---

# TypeScript String Operations

## When to Use
- Building strings dynamically with template literals
- Parsing and validating input with regex
- Converting strings to numbers safely
- Formatting numbers, dates, and text for display
- Common string manipulation (trim, split, slice, replace)

## Standard Pattern

```typescript
// Template literals (backticks) — always prefer over concatenation
const name = "World";
const greeting: string = `Hello, ${name}!`;
const multiline: string = `Line 1
Line 2
Line 3`;

// Tagged template literal for custom processing
function highlight(strings: TemplateStringsArray, ...values: string[]): string {
  return strings.reduce((result, str, i) => {
    const value = values[i] ? `**${values[i]}**` : "";
    return result + str + value;
  }, "");
}
const msg = highlight`Hello, ${name}!`; // "Hello, **World**!"

// Common string methods
const raw = "  Hello World  ";
raw.trim();           // "Hello World"
raw.trimStart();      // "Hello World  "
raw.trimEnd();        // "  Hello World"
raw.toLowerCase();    // "  hello world  "
raw.toUpperCase();    // "  HELLO WORLD  "
raw.includes("Hello"); // true
raw.startsWith("  Hello"); // true
raw.indexOf("World"); // 8
raw.slice(2, 7);      // "Hello"
raw.split(" ");       // ["", "", "Hello", "World", "", ""]
raw.replace("Hello", "Goodbye"); // "  Goodbye World  "
raw.replaceAll("l", "L");        // "  HeLLo WorLd  "

// Regex with named capture groups
const dateRegex = /^(?<year>\d{4})-(?<month>\d{2})-(?<day>\d{2})$/;
const match = dateRegex.exec("2026-07-23");
if (match?.groups) {
  const { year, month, day } = match.groups;
  // year = "2026", month = "07", day = "23"
}

// String to number conversion
const str = "42";
Number(str);       // 42 — strict, returns NaN for invalid
parseInt(str, 10); // 42 — parses up to first non-digit, always specify radix
+str;              // 42 — shorthand, same as Number()

// Safe number parsing with validation
function parsePositiveInt(input: string): number | null {
  const parsed = Number(input);
  if (!Number.isInteger(parsed) || parsed <= 0) {
    return null;
  }
  return parsed;
}

// Formatting numbers
const price = 1234.567;
price.toFixed(2);                    // "1234.57"
new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
}).format(price);                    // "$1,234.57"

new Intl.NumberFormat("de-DE", {
  style: "currency",
  currency: "EUR",
}).format(price);                    // "1.234,57 €"

// Formatting dates
const now = new Date("2026-07-23T14:30:00Z");
new Intl.DateTimeFormat("en-US", {
  dateStyle: "long",
  timeStyle: "short",
  timeZone: "America/New_York",
}).format(now);                      // "July 23, 2026 at 10:30 AM"
```

## Common Mistakes

```typescript
// WRONG: using parseInt without a radix (leading zeros cause octal parsing in older engines)
const value = parseInt("08");
// In older JS engines: 0 (parsed as octal). In modern: 8, but still unsafe.

// CORRECT: always specify radix 10
const value = parseInt("08", 10);
// 8 — always correct

// WRONG: using == to compare Number() result with a number (NaN != NaN)
const input = "abc";
if (Number(input) == NaN) {
  console.log("invalid");
}
// Never prints — NaN is not equal to anything, including itself!

// CORRECT: use Number.isNaN() or isNaN()
const input = "abc";
if (Number.isNaN(Number(input))) {
  console.log("invalid");
}
// Prints "invalid"

// WRONG: using string concatenation instead of template literals
const name = "World";
const greeting = "Hello, " + name + "!"; // Works but harder to read

// CORRECT: use template literals
const name = "World";
const greeting = `Hello, ${name}!`;

// WRONG: regex without anchoring matches partial strings
const emailRegex = /\S+@\S+\.\S+/;
emailRegex.test("not-an-email but has@something.com"); // true — partial match!

// CORRECT: anchor with ^ and $ for full-string validation
const emailRegex = /^\S+@\S+\.\S+$/;
emailRegex.test("not-an-email but has@something.com"); // false

// WRONG: using replace() when you need to replace all occurrences
const text = "foo bar foo baz foo";
text.replace("foo", "qux");
// "qux bar foo baz foo" — only first occurrence replaced!

// CORRECT: use replaceAll() or regex with /g flag
const text = "foo bar foo baz foo";
text.replaceAll("foo", "qux");
// "qux bar qux baz qux"
// or: text.replace(/foo/g, "qux")
```

## Gotchas
- `parseInt` stops at the first non-digit character: `parseInt("123abc", 10)` returns `123`, not `NaN`. Use `Number()` for strict parsing that rejects trailing characters.
- `Number("")` returns `0`, not `NaN`. Empty string is falsy but converts to zero. Check for empty strings explicitly before converting.
- `NaN` is the only JavaScript value that is not equal to itself (`NaN === NaN` is `false`). Always use `Number.isNaN()` — note that global `isNaN()` coerces its argument first, so `isNaN("hello")` is `true` (because `Number("hello")` is `NaN`), which is misleading.
- Template literals preserve whitespace exactly — indentation inside backticks appears in the output. Be careful with multiline templates in indented code blocks.
- `String.prototype.replace()` with a string first argument only replaces the **first** occurrence. Use `replaceAll()` (ES2021+) or a regex with the `/g` flag for global replacement.
- `Intl.NumberFormat` and `Intl.DateTimeFormat` are locale-aware and handle formatting correctly for different regions — prefer them over manual string building for user-facing output.

## Related
- typescript/stdlib/date-time.md
- typescript/stdlib/error-handling.md
