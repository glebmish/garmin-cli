# garmin-cli

Agent-first CLI for [Garmin Connect](https://connect.garmin.com). Wraps the [`garminconnect`](https://github.com/cyberjunky/python-garminconnect) Python library so it can be driven from a shell or by an AI agent.

**Scope:** sleep, steps, and auto-detected activities. Designed to grow.

## Install

```bash
uv tool install --from /path/to/garmin-cli garmin-cli
# or:
pipx install /path/to/garmin-cli
```

`garmin` is now on your `PATH`.

## Auth (one-time)

Interactive login. Caches OAuth tokens to `~/.garminconnect` (override with `$GARMINTOKENS`).

```bash
garmin auth login
```

Prompts for email, password, and MFA. Re-run only if subsequent calls fail with auth errors (≈ yearly).

For headless hosts (no TTY): run `auth login` on a machine with a terminal, then copy `~/.garminconnect/` to the headless host.

## Quickstart

```bash
# Sleep that ended on 2026-05-11 (Garmin's "wake date" convention)
garmin sleep get --date 2026-05-11

# Steps for a day in 30-min buckets (default is 15m — Garmin's native granularity)
garmin steps get --date 2026-05-11 --bucket 30m

# Walks that Garmin auto-detected on a given day
garmin activities list --date 2026-05-11 --type walking

# All activity types over a date range
garmin activities list --start 2026-05-01 --end 2026-05-11

# Just the timestamps from sleep
garmin sleep get --date 2026-05-11 \
  --fields sleepStartTimestampGMT,sleepEndTimestampGMT,sleepWindowConfirmed

# What operations exist?
garmin schema --list

# What does any operation accept and return?
garmin schema sleep.get
garmin schema steps.get
garmin schema activities.list
```

## Common recipes

**"Was my 09:00–09:30 commute active?"**
Pull steps in 30-min buckets, find the slot that overlaps:

```bash
garmin steps get --date 2026-05-11 --bucket 30m \
  | jq '.[] | select(.startGMT | startswith("2026-05-11T07:00"))'
# (note: startGMT is UTC; convert your local time first)
```

**"Was that empty calendar slot a walk?"**
Check Garmin's auto-detected activities for that day:

```bash
garmin activities list --date 2026-05-11 --type walking \
  --fields startTimeLocal,duration,distance,activityName
```

If nothing comes back, fall back to step buckets and look for sustained `primaryActivityLevel == "active"` runs.

## Output contract

- **stdout**: JSON (default) or one-line text (`--format text`).
- **stderr**: errors as JSON `{"error": ..., "hint": ...}`.
- **`--fields a.b,c.d`**: dotted-path filter, comma-separated. Arrays descend implicitly.
- **Envelope**: `garmin sleep get` peels Garmin's outer `dailySleepDTO` wrapper; you consume the inner object directly. So `--fields sleepStartTimestampGMT` (not `dailySleepDTO.sleepStartTimestampGMT`). `steps get` and `activities list` return arrays as-is.
- **Bucket aggregation (steps)**: Garmin's API returns 15-min buckets. `--bucket` rolls them up client-side; sums `steps` and takes the most-active `primaryActivityLevel` across constituents (`none < sleeping < sedentary < active < highlyActive`). Bucket must be a multiple of 15 minutes.

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | success |
| 1 | API error (no confirmed sleep for date, etc.) |
| 2 | auth error (no cached tokens / expired) |
| 3 | validation error (bad `--date`, etc.) |
| 4 | schema error (unknown op in `schema <op>`) |
| 5 | internal error |

## Tests

```bash
uv run pytest -v
```
