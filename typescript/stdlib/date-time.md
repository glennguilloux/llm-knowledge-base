---
id: "typescript-stdlib-date-time"
title: "TypeScript Date and Time Handling"
language: "typescript"
category: "stdlib"
subcategory: "date-time"
tags: ["date", "date-fns", "timezone", "iso-8601", "temporal", "formatting"]
version: "5.0+"
retrieval_hint: "TypeScript date time date-fns timezone ISO 8601 Temporal API"
last_verified: "2026-05-24"
confidence: "high"
---

# TypeScript Date and Time Handling

## When to Use
- Parsing and formatting dates from APIs (ISO 8601 strings)
- Date arithmetic (add/subtract days, compare dates)
- Timezone-aware date handling
- User-facing date/time display with `Intl.DateTimeFormat`
- Prefer `date-fns` over `moment` for new projects (tree-shakable, immutable)

## Standard Pattern

```typescript
import {
  addDays,
  subDays,
  differenceInDays,
  format,
  parseISO,
  isValid,
  startOfDay,
  endOfDay,
  isBefore,
  isAfter,
} from "date-fns";
import { zonedTimeToUtc, utcToZonedTime, format as formatTz } from "date-fns-tz";

// Parsing ISO 8601 strings (most common from APIs)
const isoString = "2026-07-23T14:30:00Z";
const date: Date = parseISO(isoString);

if (!isValid(date)) {
  throw new Error(`Invalid date: ${isoString}`);
}

// Formatting for display
const display: string = format(date, "yyyy-MM-dd HH:mm:ss");
// "2026-07-23 14:30:00"

const humanReadable: string = format(date, "MMMM do, yyyy 'at' h:mm a");
// "July 23rd, 2026 at 2:30 PM"

// Date arithmetic (date-fns functions return NEW Date objects — immutable)
const tomorrow: Date = addDays(date, 1);
const lastWeek: Date = subDays(date, 7);
const daysDiff: number = differenceInDays(tomorrow, lastWeek);
// 8

// Comparisons
const start: Date = startOfDay(date); // 00:00:00.000
const end: Date = endOfDay(date);     // 23:59:59.999
const isPast: boolean = isBefore(date, new Date());

// Timezone handling with date-fns-tz
const timeZone = "America/New_York";
const zonedDate: Date = utcToZonedTime(date, timeZone);
const formattedTz: string = formatTz(zonedDate, "yyyy-MM-dd HH:mm:ss zzz", {
  timeZone,
});
// "2026-07-23 10:30:00 EDT"

// Convert local time back to UTC
const localInput = "2026-07-23 10:30:00";
const utcDate: Date = zonedTimeToUtc(localInput, timeZone);

// Using Intl.DateTimeFormat (built-in, no library needed)
const formatter = new Intl.DateTimeFormat("en-US", {
  dateStyle: "full",
  timeStyle: "long",
  timeZone: "America/New_York",
});
const localized: string = formatter.format(date);
// "Thursday, July 23, 2026 at 10:30:00 AM EDT"

// Creating dates safely
// Month is 0-indexed: 0 = January, 6 = July
const specificDate: Date = new Date(2026, 6, 23); // July 23, 2026
const fromIso: Date = new Date("2026-07-23T00:00:00Z"); // Always use ISO 8601

// Date arithmetic with raw Date (mutable — be careful)
function addDaysNative(d: Date, days: number): Date {
  const result = new Date(d); // copy first
  result.setDate(result.getDate() + days);
  return result;
}
```

## Common Mistakes

```typescript
// WRONG: using moment.js in new projects (deprecated, huge bundle)
import moment from "moment";
const now = moment().format("YYYY-MM-DD");

// CORRECT: use date-fns (tree-shakable, immutable)
import { format } from "date-fns";
const now = format(new Date(), "yyyy-MM-dd");

// WRONG: creating Date with ambiguous string format
const d = new Date("07/23/2026");
// Behavior varies by locale and engine — "MM/DD/YYYY" vs "DD/MM/YYYY" ambiguity!

// CORRECT: use ISO 8601 or explicit constructor
const d = new Date("2026-07-23T00:00:00Z"); // ISO 8601 — unambiguous
// or: new Date(2026, 6, 23) — year, monthIndex, day

// WRONG: mutating Date objects directly without copying
function addOneDay(d: Date): Date {
  d.setDate(d.getDate() + 1); // Mutates the original!
  return d;
}
const original = new Date("2026-07-23");
const result = addOneDay(original);
// original is now July 24 too — surprise mutation!

// CORRECT: always create a new Date when modifying
function addOneDay(d: Date): Date {
  const copy = new Date(d.getTime());
  copy.setDate(copy.getDate() + 1);
  return copy;
}
// Or use date-fns: addDays(d, 1)

// WRONG: comparing Date objects with === (compares references, not values)
const a = new Date("2026-07-23");
const b = new Date("2026-07-23");
console.log(a === b); // false — different object references!

// CORRECT: compare using getTime() or valueOf()
const a = new Date("2026-07-23");
const b = new Date("2026-07-23");
console.log(a.getTime() === b.getTime()); // true

// WRONG: assuming getMonth() returns 1-12
const d = new Date(2026, 0, 1); // January 1
console.log(d.getMonth()); // 0 — months are 0-indexed!

// CORRECT: remember months are 0-indexed (0=Jan, 11=Dec)
const monthIndex = d.getMonth(); // 0
const humanMonth = monthIndex + 1; // 1 = January
```

## Gotchas
- `Date` months are **0-indexed** (0 = January, 11 = December), but days are 1-indexed. This is the single most common source of off-by-one date bugs.
- `new Date("2026-07-23")` is interpreted as **local time**, while `new Date("2026-07-23T00:00:00Z")` is **UTC**. The `Z` suffix matters enormously. Always use the full ISO 8601 format with timezone indicator for API data.
- `Date` objects are **mutable** — `setDate`, `setMonth`, `setHours`, etc. modify the original. Always copy with `new Date(original.getTime())` before mutating, or use `date-fns` which returns new objects.
- `Date` comparison with `===` or `==` compares object references, not time values. Use `date.getTime() === other.getTime()` or `date.valueOf() === other.valueOf()`.
- `date-fns` format tokens differ from `moment`: `yyyy` not `YYYY`, `dd` not `DD`, `do` for ordinal. Moment's `YYYY` means ISO week-numbering year, while `date-fns` `yyyy` means calendar year — they differ at year boundaries.
- The Temporal API (TC39 Stage 3) will eventually replace `Date` with proper timezone support, immutability, and a cleaner API. It is not yet available in most runtimes without a polyfill as of 2026.

## Related
- typescript/stdlib/string-operations.md
- typescript/stdlib/error-handling.md
