---
name: garmin-sleep
description: Use when fetching Garmin sleep data with `garmin sleep get` — covers the wake-date convention, the unwrapped dailySleepDTO envelope, and the "no confirmed sleep" case.
---

# garmin-sleep

```bash
garmin sleep get --date 2026-05-11
```

## Quirks not obvious from --help

- **`--date` is the WAKE date.** A night's sleep is keyed by the morning you woke
  up, not the evening you went to bed. Sleep from the night of May 10 → 11 is
  `--date 2026-05-11`.
- **Envelope is unwrapped.** Garmin returns `{"dailySleepDTO": {...}, ...}`. The
  CLI emits the inner `dailySleepDTO` directly. So field masks are
  `--fields sleepStartTimestampGMT`, NOT `dailySleepDTO.sleepStartTimestampGMT`.
  Sibling keys (e.g. `sleepLevels`) are dropped.
- **Timestamps are epoch milliseconds, GMT.** `sleepStartTimestampGMT` /
  `sleepEndTimestampGMT` are ms since epoch in UTC. Convert before comparing to
  local wall-clock times.
- **Unconfirmed / missing sleep → exit 1.** If Garmin has no confirmed sleep
  window for the date (watch not worn, nap-only, not yet synced), the CLI exits
  **1 (API error)** with a hint, not an empty success. Don't treat exit 1 here as
  a crash — it means "no data for that night".

## Useful fields

`sleepStartTimestampGMT`, `sleepEndTimestampGMT`, `sleepWindowConfirmed`,
`calendarDate`, plus many duration/score fields. Run:

```bash
garmin sleep get --date 2026-05-11 \
  --fields sleepStartTimestampGMT,sleepEndTimestampGMT,sleepWindowConfirmed
```
