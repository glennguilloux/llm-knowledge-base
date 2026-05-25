---
id: "java-stdlib-date-time"
title: "Java Date and Time (java.time)"
language: "java"
category: "stdlib"
subcategory: "datetime"
tags: ["date-time", "localdate", "localdatetime", "instant", "duration", "period", "zoneddatetime"]
version: "17+"
retrieval_hint: "Java date time java.time LocalDate LocalDateTime Instant Duration Period formatting parsing"
last_verified: "2026-05-24"
confidence: "high"
---

# Java Date and Time (java.time)

## When to Use
- Any date or time manipulation (use `java.time`, never `java.util.Date`)
- Date-only values like birthdays (LocalDate)
- Timestamps for events (Instant, LocalDateTime)
- Time zone-aware operations (ZonedDateTime)
- Duration vs elapsed time (Duration) vs date-based amounts (Period)
- Parsing and formatting ISO and custom date/time strings

## Standard Pattern

```java
import java.time.*;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.time.temporal.ChronoUnit;

public class DateTimeExamples {

    // LocalDate - date only, no time zone
    public static LocalDate parseDate(String text) {
        try {
            return LocalDate.parse(text);  // Expects ISO-8601: yyyy-MM-dd
        } catch (DateTimeParseException e) {
            throw new IllegalArgumentException("Invalid date: " + text, e);
        }
    }

    public static String formatDate(LocalDate date) {
        return date.format(DateTimeFormatter.ofPattern("MMMM d, yyyy"));
    }

    // Instant - a moment on the UTC timeline
    public static Instant nowTimestamp() {
        return Instant.now();
    }

    // LocalDateTime - date and time without time zone
    public static LocalDateTime scheduleEvent(int year, int month, int day, int hour, int min) {
        return LocalDateTime.of(year, month, day, hour, min);
    }

    public static LocalDate extractDate(LocalDateTime dateTime) {
        return dateTime.toLocalDate();
    }

    // ZonedDateTime - date, time, and zone
    public static ZonedDateTime toZone(Instant instant, String zoneId) {
        ZoneId zone = ZoneId.of(zoneId);
        return instant.atZone(zone);
    }

    public static ZonedDateTime parseZoned(String text) {
        return ZonedDateTime.parse(text);  // ISO-8601 with offset, e.g. 2024-01-15T10:30+01:00[Europe/Paris]
    }

    // Duration - time-based amount (hours, minutes, seconds)
    public static Duration elapsedTime(Instant start, Instant end) {
        return Duration.between(start, end);
    }

    public static Instant addHours(Instant instant, long hours) {
        return instant.plus(Duration.ofHours(hours));
    }

    // Period - date-based amount (years, months, days)
    public static Period age(LocalDate birthDate) {
        return Period.between(birthDate, LocalDate.now());
    }

    public static LocalDate addMonths(LocalDate date, int months) {
        return date.plusMonths(months);
    }

    // Custom formatting
    public static String customFormat(LocalDateTime dateTime) {
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
        return dateTime.format(formatter);
    }

    // Legacy Date migration
    public static Instant fromLegacyDate(java.util.Date legacyDate) {
        return legacyDate.toInstant();
    }

    public static java.util.Date toLegacyDate(Instant instant) {
        return java.util.Date.from(instant);
    }

    public static void main(String[] args) {
        System.out.println("Parsed: " + parseDate("2024-01-15"));
        System.out.println("Formatted: " + formatDate(LocalDate.now()));
        Instant now = nowTimestamp();
        System.out.println("Timestamp: " + now);
        System.out.println("NY time: " + toZone(now, "America/New_York"));
        System.out.println("Tokyo time: " + toZone(now, "Asia/Tokyo"));

        Instant start = Instant.now();
        Instant end = start.plusSeconds(90);
        Duration dur = elapsedTime(start, end);
        System.out.println("Duration: " + dur.toMillis() + "ms, seconds=" + dur.toSeconds());

        LocalDate birthday = LocalDate.of(1990, 6, 15);
        Period p = age(birthday);
        System.out.println("Age: " + p.getYears() + " years, " + p.getMonths() + " months");

        System.out.println("Custom: " + customFormat(LocalDateTime.now()));

        System.out.println("Parsed zoned: " + parseZoned("2024-01-15T10:30:00+01:00[Europe/Paris]"));
    }
}
```

## Common Mistakes

```java
// WRONG: Using java.util.Date or Calendar in new code
java.util.Date date = new java.util.Date();  // Legacy! Not thread-safe, mutable, confusing API

// CORRECT: Use java.time
LocalDate date = LocalDate.now();
Instant timestamp = Instant.now();

// WRONG: Creating LocalDateTime with zone and expecting zone to be stored
LocalDateTime ldt = LocalDateTime.now();  // Captures local time but drops zone info!
// LocalDateTime does NOT contain time zone - it's just date + time without context

// CORRECT: Use ZonedDateTime when zone matters
ZonedDateTime zdt = ZonedDateTime.now(ZoneId.of("America/New_York"));

// WRONG: Using Period for time (hours/minutes) or Duration for date (days/months/years)
Period p = Period.between(start, end);  // If start/end are Instants, throws UnsupportedTemporalTypeException

// CORRECT: Duration for time-based, Period for date-based
Duration d = Duration.between(startInstant, endInstant);
Period p = Period.between(startLocalDate, endLocalDate);

// WRONG: Modifying LocalDateTime directly - it's immutable!
LocalDateTime dt = LocalDateTime.now();
dt.plusHours(2);  // Returns new instance - original is unchanged!
System.out.println(dt);  // Still the original time!

// CORRECT: Capture the return value
LocalDateTime dt = LocalDateTime.now();
dt = dt.plusHours(2);  // Reassign to updated instance

// WRONG: Parsing a date with wrong pattern
LocalDate date = LocalDate.parse("15/01/2024");  // DateTimeParseException! ISO expects yyyy-MM-dd

// CORRECT: Use DateTimeFormatter for non-ISO formats
DateTimeFormatter fmt = DateTimeFormatter.ofPattern("dd/MM/yyyy");
LocalDate date = LocalDate.parse("15/01/2024", fmt);

// WRONG: Assuming LocalDate.plusDays(1) always gives "tomorrow" across daylight saving
// LocalDate has no time/timezone, so DST doesn't apply. But LocalDateTime.plusHours(24)
// may give a different wall-clock time during DST transitions.

// CORRECT: Use ZonedDateTime for wall-clock time arithmetic across DST boundaries
ZonedDateTime now = ZonedDateTime.now(ZoneId.of("America/New_York"));
ZonedDateTime tomorrow = now.plusDays(1);  // Handles DST correctly
```

## Gotchas
- `LocalDateTime.now()` captures the system clock's local date+time **without** a time zone - two systems in different zones calling it at the same instant get different values
- `Period.between(start, end)` uses `LocalDate` arguments - passing `Instant` or `LocalDateTime` throws `UnsupportedTemporalTypeException`
- `Duration.between` works with `Instant` and `LocalDateTime`, but when used with `LocalDateTime` that spans a DST change, it calculates **elapsed time** (not wall-clock difference)
- `DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")` - 'H' is 24-hour, 'h' is 12-hour; 'm' is minute, 'M' is month; 's' is second, 'S' is millisecond
- `ZonedDateTime` automatically handles daylight saving transitions - adding 24 hours during a DST spring-forward may result in 23 or 25 hours of elapsed wall-clock time
- The legacy `java.util.Date.toString()` applies the JVM's default time zone when displaying, making it appear to have a time zone - internally it's just epoch millis (UTC)
- `LocalDate.of(2024, 2, 30)` throws `DateTimeException` - invalid date, unlike `Calendar` which silently overflows

## Related
- java/stdlib/collections.md
- java/stdlib/exception-handling.md
