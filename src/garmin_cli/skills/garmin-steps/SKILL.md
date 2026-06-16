---
name: garmin-steps
description: Use when fetching step counts with `garmin steps get` — covers Garmin's native 15-minute buckets, client-side --bucket aggregation, and the primaryActivityLevel ranking.
---

# garmin-steps

```bash
garmin steps get --date 2026-05-11            # native 15-min buckets
garmin steps get --date 2026-05-11 --bucket 30m
```

## Quirks not obvious from --help

- **Garmin's native granularity is 15 minutes.** The API always returns 15-min
  buckets. `--bucket` rolls them up **client-side** — the network payload is the
  same regardless.
- **`--bucket` must be a multiple of 15 minutes**, from `15m` to `1440m` (24h).
  Accepts `15`, `15m`, `30min`, `1h`, `90m`. A non-multiple → exit 3 (validation).
- **Aggregation rules** when combining 15-min buckets into a larger one:
  - `steps` are **summed**.
  - `primaryActivityLevel` takes the **most-active** level across constituents,
    ranked: `none < sleeping < sedentary < active < highlyActive`.
  - `startGMT` = first constituent's start; `endGMT` = last constituent's end.
- **Each bucket object** is `{startGMT, endGMT, steps, primaryActivityLevel}`.
  Returned as a plain array (no envelope).
- **`startGMT`/`endGMT` are UTC.** Convert your local window to UTC before
  selecting buckets.

## Pattern: was a time window active?

```bash
garmin steps get --date 2026-05-11 --bucket 30m \
  | jq '.[] | select(.startGMT | startswith("2026-05-11T07:00"))'
```

Sustained `primaryActivityLevel == "active"`/`"highlyActive"` across buckets is a
strong signal of movement even when no discrete activity was auto-detected.
