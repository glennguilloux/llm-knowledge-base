---
id: "go-stdlib-time-dates"
title: "Time and Dates"
language: "go"
category: "stdlib"
tags: ["go", "time", "date", "duration", "timer", "ticker", "timezone", "format", "parse"]
version: "1.21+"
retrieval_hint: "time.Now time.Format time.Parse duration timer ticker timezone reference date 2006"
last_verified: "2026-05-24"
confidence: "high"
---

# Time and Dates

## When to Use
- Getting the current time (`time.Now`)
- Formatting time for display or serialization (`time.Format`)
- Parsing time strings from user input or APIs (`time.Parse`)
- Measuring elapsed time and sleeping (`time.Since`, `time.Sleep`)
- Scheduling one-shot or repeated actions (`time.Timer`, `time.Ticker`)
- Working with time zones (`time.LoadLocation`, `time.FixedZone`)

## Standard Pattern

```go
package main

import (
	"fmt"
	"time"
)

func main() {
	// Current time
	now := time.Now()
	fmt.Println("Now:", now)

	// Formatting — Go's reference date: Mon Jan 2 15:04:05 MST 2006
	// The reference time is: 1 2 3 4 5 6 7 (Mon=1, Jan=2, 03=15h, 04=min, 05=sec, 2006=year)
	fmt.Println(now.Format("2006-01-02"))                // 2026-07-23
	fmt.Println(now.Format("2006-01-02 15:04:05"))      // 2026-07-23 14:30:00
	fmt.Println(now.Format(time.RFC3339))                // 2026-07-23T14:30:00Z
	fmt.Println(now.Format("January 2, 2006"))           // July 23, 2026

	// Parsing — must use reference date in layout string
	t, err := time.Parse("2006-01-02", "2026-07-23")
	if err != nil {
		panic(err)
	}
	fmt.Println("Parsed:", t)

	// Duration
	d := 2 * time.Hour
	fmt.Println("Duration:", d)           // 2h0m0s
	fmt.Println("Minutes:", d.Minutes())  // 120

	// Elapsed time
	start := time.Now()
	time.Sleep(100 * time.Millisecond)
	elapsed := time.Since(start)
	fmt.Println("Elapsed:", elapsed)

	// Timer — fires once after duration
	timer := time.NewTimer(200 * time.Millisecond)
	<-timer.C // blocks until fired
	fmt.Println("Timer fired")

	// Ticker — fires repeatedly
	ticker := time.NewTicker(100 * time.Millisecond)
	defer ticker.Stop()
	for i := 0; i < 3; i++ {
		<-ticker.C
		fmt.Println("Tick", i+1)
	}

	// Time zones
	loc, err := time.LoadLocation("America/New_York")
	if err != nil {
		panic(err)
	}
	nyTime := now.In(loc)
	fmt.Println("New York:", nyTime.Format("15:04 MST"))

	// Fixed offset timezone
	fixed := time.FixedZone("EST", -5*60*60)
	estTime := now.In(fixed)
	fmt.Println("EST:", estTime.Format("15:04 MST"))

	// Comparing times
	a := time.Date(2026, 1, 1, 0, 0, 0, 0, time.UTC)
	b := time.Date(2026, 6, 1, 0, 0, 0, 0, time.UTC)
	fmt.Println("a before b:", a.Before(b)) // true
	fmt.Println("a after b:", a.After(b))   // false
	fmt.Println("a equal b:", a.Equal(b))   // false

	// Adding/subtracting
	future := now.Add(24 * time.Hour)
	past := now.Add(-7 * 24 * time.Hour)
	fmt.Println("Tomorrow:", future.Format("2006-01-02"))
	fmt.Println("Last week:", past.Format("2006-01-02"))
}
```

## Common Mistakes

```go
// WRONG: using arbitrary format strings (not Go's reference date)
t, _ := time.Parse("01-02-2006", "07-23-2026") // works but confusing
// Many models try: time.Parse("yyyy-MM-dd", "2026-07-23") — WRONG, Go doesn't use yyyy/MM/dd

// CORRECT: always use the reference date Mon Jan 2 15:04:05 MST 2006
t, err := time.Parse("2006-01-02", "2026-07-23")
if err != nil {
	// handle parse error
}

// WRONG: forgetting that time.Parse returns time in UTC by default
t, _ := time.Parse("2006-01-02 15:04:05", "2026-07-23 10:00:00")
// t.Location() is UTC — may not be what you want

// CORRECT: use time.ParseInLocation for a specific timezone
loc, _ := time.LoadLocation("America/Chicago")
t, err := time.ParseInLocation("2006-01-02 15:04:05", "2026-07-23 10:00:00", loc)
if err != nil {
	// handle error
}

// WRONG: using time.After in a loop (leaks timers)
for {
	select {
	case <-time.After(5 * time.Second): // creates a new timer each iteration!
		fmt.Println("timeout")
	}
}

// CORRECT: create timer outside the loop
timer := time.NewTimer(5 * time.Second)
defer timer.Stop()
for {
	select {
	case <-timer.C:
		fmt.Println("timeout")
		return
	}

	// WRONG: not stopping a ticker (goroutine leak)
ticker := time.NewTicker(time.Second)
// ... use ticker but never call ticker.Stop()

// CORRECT: always defer ticker.Stop()
ticker := time.NewTicker(time.Second)
defer ticker.Stop()

// WRONG: comparing time.Time with == (works but includes monotonic clock reading)
t1 := time.Now()
t2 := t1
// t1 == t2 may be unreliable due to monotonic readings

// CORRECT: use t1.Equal(t2) for reliable comparison
if t1.Equal(t2) {
	fmt.Println("same time")
}
```

## Gotchas
- Go's reference date is **Mon Jan 2 15:04:05 MST 2006** (Unix time 1136239445). The numbers 1-2-3-4-5-6-7 correspond to month-day-hour-minute-second-year. This is NOT arbitrary — it's a mnemonic.
- `time.Parse` returns a `time.Time` in **UTC** by default. Use `time.ParseInLocation` to parse into a specific timezone.
- `time.Now()` includes a monotonic clock reading. When comparing two `time.Time` values with `==`, the monotonic reading is included, which can cause unexpected results. Use `.Equal()` instead.
- `time.After` creates a new timer on every call. In a loop, this leaks timers. Use `time.NewTimer` and `defer timer.Stop()` instead.
- `time.Ticker` must be stopped with `ticker.Stop()` to release resources. Failing to stop a ticker leaks a goroutine.
- `time.Duration` is in nanoseconds. `1 * time.Second` = 1,000,000,000 nanoseconds. Passing a plain integer to `time.Sleep` (e.g., `time.Sleep(1)`) sleeps for 1 nanosecond, not 1 second.
- `time.LoadLocation` depends on the system's timezone database. In containers, you may need to install `tzdata` or embed it with `import _ "time/tzdata"`.
- Formatting with `time.Format("12:00")` gives 24-hour time. Use `time.Format("03:00 PM")` for 12-hour time with AM/PM.
- `time.Since(t)` is equivalent to `time.Now().Sub(t)` — both return a `time.Duration`.

## Related
- go/stdlib/command-line.md
- go/stdlib/file-io.md
