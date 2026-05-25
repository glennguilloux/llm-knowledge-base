---
id: "php-stdlib-datetime"
title: "Date and Time: DateTime, DateTimeImmutable, Time Zones"
language: "php"
category: "stdlib"
tags: ["php", "datetime", "timezone", "dateinterval", "carbon"]
version: "8.1+"
retrieval_hint: "php DateTime DateTimeImmutable DateInterval time zone Carbon immutability"
last_verified: "2026-05-24"
confidence: "high"
---

# Date and Time: DateTime, DateTimeImmutable, Time Zones

## When to Use
- Working with dates and times in PHP
- Performing date arithmetic and formatting
- Handling time zone conversions
- Storing and retrieving timestamps

## Standard Pattern

```php
<?php

// --- DateTimeImmutable (preferred — immutable, no side effects) ---
$now = new DateTimeImmutable('now', new DateTimeZone('UTC'));
echo $now->format('Y-m-d H:i:s');  // 2024-01-15 10:30:00

// --- Creating DateTimeImmutable ---
// From string
$date = new DateTimeImmutable('2024-01-15 10:30:00', new DateTimeZone('America/New_York'));

// From timestamp
$date = (new DateTimeImmutable())->setTimestamp(1705312200);

// From format
$date = DateTimeImmutable::createFromFormat('Y/m/d', '2024/01/15');
// Handle parse errors:
if (!$date) {
    $errors = DateTimeImmutable::getLastErrors();
    // handle error
}

// --- Formatting ---
$date = new DateTimeImmutable('2024-01-15 10:30:00');
echo $date->format('Y-m-d');            // 2024-01-15
echo $date->format('c');                // 2024-01-15T10:30:00+00:00 (ISO 8601)
echo $date->format(DATE_ATOM);          // 2024-01-15T10:30:00+00:00 (RFC 3339)
echo $date->format('l, F jS Y');       // Monday, January 15th 2024

// --- Time Zone Conversion ---
$utc = new DateTimeImmutable('now', new DateTimeZone('UTC'));
$nyc = $utc->setTimezone(new DateTimeZone('America/New_York'));
$tokyo = $utc->setTimezone(new DateTimeZone('Asia/Tokyo'));

echo $nyc->format('Y-m-d H:i:s T');    // 2024-01-15 05:30:00 EST
echo $tokyo->format('Y-m-d H:i:s T');  // 2024-01-15 19:30:00 JST

// --- Date Arithmetic ---
$date = new DateTimeImmutable('2024-01-15');

$nextWeek = $date->add(new DateInterval('P7D'));
$lastMonth = $date->sub(new DateInterval('P1M'));
$nextYear = $date->modify('+1 year');

// Difference between dates
$start = new DateTimeImmutable('2024-01-01');
$end = new DateTimeImmutable('2024-12-31');
$diff = $start->diff($end);

echo $diff->days;       // 365
echo $diff->m;          // 11 months
echo $diff->format('%y years, %m months, %d days');  // 0 years, 11 months, 30 days

// --- Comparison ---
$date1 = new DateTimeImmutable('2024-01-15');
$date2 = new DateTimeImmutable('2024-06-15');

var_dump($date1 < $date2);   // bool(true)
var_dump($date1 == $date2);  // bool(false)

// --- Carbon (Popular Third-Party Library) ---
// composer require nesbot/carbon
// use Carbon\CarbonImmutable;

// $now = CarbonImmutable::now();
// echo $now->addDays(7)->format('Y-m-d');
// echo $now->diffForHumans();  // "4 hours ago"
// echo CarbonImmutable::parse('first day of January 2024')->format('Y-m-d');

// --- ISO Week Calculation ---
$date = new DateTimeImmutable('2024-01-15');
echo $date->format('o-W');  // 2024-03 (ISO year and week number)
```

## Common Mistakes

```php
<?php

// WRONG: Using mutable DateTime (side effects)
$date = new DateTime('2024-01-15');
$modified = $date->modify('+1 month');  // Modifies BOTH variables!
// $date is now 2024-02-15 — unexpected mutation

// CORRECT: Use DateTimeImmutable
$date = new DateTimeImmutable('2024-01-15');
$modified = $date->modify('+1 month');  // $date is unchanged
// $date = 2024-01-15, $modified = 2024-02-15


// WRONG: Ignoring timezone when creating dates
$date = new DateTimeImmutable('2024-01-15 14:00:00');
// Uses default timezone (php.ini: date.timezone), which may be wrong

// CORRECT: Always specify timezone
$date = new DateTimeImmutable('2024-01-15 14:00:00', new DateTimeZone('America/New_York'));
// Or set globally:
date_default_timezone_set('UTC');


// WRONG: Incorrect date format string
$date = DateTimeImmutable::createFromFormat('d/m/Y', '2024/01/15');
// Fails — expected "15/01/2024" (day/month/year), got "2024/01/15"

// CORRECT: Match the format to the input
$date = DateTimeImmutable::createFromFormat('Y/m/d', '2024/01/15');


// WRONG: Using string comparison for dates
$date1 = '2024-01-15';
$date2 = '2024-02-01';
var_dump($date1 < $date2);  // true (works for Y-m-d, but not all formats!)

// CORRECT: Always compare DateTime objects
$d1 = new DateTimeImmutable($date1);
$d2 = new DateTimeImmutable($date2);
var_dump($d1 < $d2);
```

## Gotchas
- **DST transitions**: `DateTime` (mutable) can behave unpredictably during DST transitions (spring forward / fall back). `DateTimeImmutable` avoids state-based bugs. Dates at 2:30 AM on DST change day may not exist.
- **2038 problem**: On 32-bit PHP installations, timestamps after 2038-01-19 03:14:07 UTC will overflow. Use 64-bit PHP or avoid raw timestamps for future dates.
- **`strtotime()` edge cases**: `strtotime('next Monday')` gives the next Monday from today. `strtotime('+1 month')` on January 31 returns March 3 (not Feb 28/29) — PHP overflows months.
- **`DateTimeImmutable` availability**: Available since PHP 5.5. Always prefer it over `DateTime` for new code. Both share the same interface.
- **`createFromFormat` strictness**: By default, `createFromFormat` is strict. Use `DateTimeImmutable::getLastErrors()` to check for parsing warnings (e.g., trailing data after the date).
- **JSON serialization**: `DateTimeImmutable` doesn't implement `JsonSerializable` by default. Use `$date->format('c')` before JSON encoding, or use Carbon which does implement it.
- **Unix timestamps**: `$date->getTimestamp()` returns int (seconds since epoch). For milliseconds, multiply by 1000 and cast to int.

## Related
- php/stdlib/basics.md
- php/stdlib/error-handling.md
