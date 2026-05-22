---
id: "python-stdlib-datetime"
title: "Date and Time Handling"
language: "python"
category: "stdlib"
tags: ["datetime", "timezone", "dateutil", "parsing", "formatting", "timedelta"]
version: "3.10+"
retrieval_hint: "datetime timezone timedelta parsing formatting date time UTC"
last_verified: "2026-05-22"
confidence: "high"
---

# Date and Time Handling

## When to Use
- Parsing dates from strings (API responses, user input)
- Formatting dates for display or storage
- Timezone conversions
- Date arithmetic (add/subtract days, hours)
- Scheduling and time-based logic

## Standard Pattern

```python
from datetime import datetime, date, time, timedelta, timezone
from zoneinfo import ZoneInfo  # Python 3.9+

# Current time
now = datetime.now()                          # Naive (local timezone)
now_utc = datetime.now(timezone.utc)          # Aware (UTC)
today = date.today()                          # Date only

# Creating specific dates
dt = datetime(2024, 6, 15, 14, 30, 0)        # Naive
dt_aware = datetime(2024, 6, 15, 14, 30, 0, tzinfo=ZoneInfo("America/New_York"))

# Parsing strings
dt = datetime.strptime("2024-01-15 14:30", "%Y-%m-%d %H:%M")  # From format
dt = datetime.fromisoformat("2024-01-15T14:30:00+00:00")       # ISO 8601

# With dateutil (more flexible parsing)
from dateutil.parser import parse
dt = parse("January 15, 2024 2:30 PM")       # Handles many formats
dt = parse("15/01/2024", dayfirst=True)       # DD/MM/YYYY

# Formatting
formatted = dt.strftime("%Y-%m-%d %H:%M:%S")  # "2024-01-15 14:30:00"
iso = dt.isoformat()                           # "2024-01-15T14:30:00"

# Date arithmetic
tomorrow = date.today() + timedelta(days=1)
next_week = datetime.now(timezone.utc) + timedelta(weeks=1)
diff = datetime(2024, 12, 31) - datetime(2024, 1, 1)
print(diff.days)  # 365

# Timezone conversion
utc_now = datetime.now(timezone.utc)
eastern = utc_now.astimezone(ZoneInfo("America/New_York"))
tokyo = utc_now.astimezone(ZoneInfo("Asia/Tokyo"))

# Comparing aware and naive datetimes
naive = datetime(2024, 1, 1)
aware = datetime(2024, 1, 1, tzinfo=timezone.utc)
# naive < aware  # TypeError: can't compare aware and naive

# Getting epoch timestamp
epoch = datetime.now(timezone.utc).timestamp()  # Float seconds since 1970
from_epoch = datetime.fromtimestamp(epoch, tz=timezone.utc)
```

## Common Mistakes

```python
# WRONG: Using naive datetimes for production code
now = datetime.now()  # What timezone? System local — varies by server

# CORRECT: Always use timezone-aware datetimes
now = datetime.now(timezone.utc)  # Explicit UTC

# WRONG: Comparing aware and naive datetimes
naive = datetime(2024, 1, 1)
aware = datetime(2024, 1, 1, tzinfo=timezone.utc)
if naive == aware:  # TypeError!
    pass

# CORRECT: Make both aware before comparing
naive = datetime(2024, 1, 1, tzinfo=timezone.utc)
aware = datetime(2024, 1, 1, tzinfo=timezone.utc)

# WRONG: Assuming UTC offset is always fixed
# Some timezones have DST — UTC-5 in winter, UTC-4 in summer
eastern = timezone(timedelta(hours=-5))  # Wrong for summer!

# CORRECT: Use zoneinfo for proper timezone handling
from zoneinfo import ZoneInfo
eastern = ZoneInfo("America/New_York")  # Handles DST correctly

# WRONG: Using time.sleep for precise timing
import time
time.sleep(0.001)  # Not precise — OS scheduling delays

# CORRECT: Use monotonic clock for intervals
start = time.monotonic()
# ... work ...
elapsed = time.monotonic() - start

# WRONG: strftime with wrong format
dt.strftime("%d/%m/%y")  # 2-digit year, locale-dependent

# CORRECT: Use ISO 8601 for storage/exchange
dt.isoformat()  # "2024-01-15T14:30:00+00:00"
```

## Gotchas
- `datetime.now()` returns a NAIVE datetime — no timezone info, dangerous for comparison
- `datetime.now(timezone.utc)` returns an AWARE datetime — always prefer this
- Comparing naive and aware datetimes raises `TypeError` — Python won't guess
- `dateutil.parser.parse` is flexible but may misinterpret ambiguous dates (DD/MM vs MM/DD)
- `zoneinfo.ZoneInfo` requires the `tzdata` package on Windows
- `timedelta` does not handle months or years (variable length) — use `dateutil.relativedelta`
- Timestamps from `datetime.timestamp()` depend on the local timezone for naive datetimes
- `datetime.fromisoformat()` before Python 3.11 doesn't handle all ISO 8601 formats
- DST transitions can cause "impossible" or "ambiguous" times

## Related
- python/stdlib/file-io.md
- python/web/fastapi/basics.md
- python/stdlib/env-config.md
