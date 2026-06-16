# garmin-cli

[![CI](https://github.com/glebmish/garmin-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/glebmish/garmin-cli/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/garmin-cli)](https://pypi.org/project/garmin-cli/)
[![Python](https://img.shields.io/pypi/pyversions/garmin-cli)](https://pypi.org/project/garmin-cli/)
[![License](https://img.shields.io/github/license/glebmish/garmin-cli)](LICENSE)

Agent-first CLI for [Garmin Connect](https://connect.garmin.com). Wraps the [`garminconnect`](https://github.com/cyberjunky/python-garminconnect) Python library so it can be driven from a shell or by an AI agent. Every command emits JSON, exits with a typed code, and carries an actionable `hint` on failure.

**Scope:** sleep, steps, and auto-detected activities. Designed to grow.

> Not affiliated with, endorsed by, or sponsored by Garmin Ltd. This tool talks to Garmin Connect through the unofficial, reverse-engineered [`garminconnect`](https://github.com/cyberjunky/python-garminconnect) library, not an official Garmin API; it can break if Garmin changes their endpoints.

## Install

Requires Python 3.12+.

```bash
pipx install garmin-cli
# or:
uv tool install garmin-cli
# or:
pip install garmin-cli
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

## Sample output

Every operation is self-describing offline (no account needed) — `garmin schema <op>`
returns the args, output shape, and exit codes:

```console
$ garmin schema sleep.get
{
  "args": [
    { "name": "--date", "required": true, "type": "date (YYYY-MM-DD)" }
  ],
  "description": "Fetch raw dailySleepDTO for a wake date.",
  "exit_codes": {
    "0": "success",
    "1": "no confirmed/usable sleep for the date, OR a transient Garmin API/network error (retryable)",
    "2": "auth missing/expired",
    "3": "bad --date format"
  },
  "method": "GET",
  "output": "dailySleepDTO object (Garmin's raw shape). Includes sleepStartTimestampGMT, sleepEndTimestampGMT, sleepWindowConfirmed, and many other fields."
}
```

A data call returns Garmin's raw JSON (illustrative `steps get` response, trimmed):

```console
$ garmin steps get --date 2026-05-11 --bucket 30m --fields startGMT,steps,primaryActivityLevel
[
  { "startGMT": "2026-05-11T06:00:00.0", "steps": 0,   "primaryActivityLevel": "sedentary" },
  { "startGMT": "2026-05-11T06:30:00.0", "steps": 412, "primaryActivityLevel": "active" },
  { "startGMT": "2026-05-11T07:00:00.0", "steps": 1893,"primaryActivityLevel": "highlyActive" }
]
```

On failure, errors go to stderr as JSON with an actionable `hint`, and the process
exits with a typed code (see [Exit codes](#exit-codes)):

```console
$ garmin sleep get --date 2026-05-11
{"error": "no dailySleepDTO returned for 2026-05-11", "hint": "no confirmed sleep for this date; check Garmin Connect web UI"}
# exit code: 1
```

## Agent skills

Bundled, offline agent docs ship inside the package. An agent can read them at
runtime or install them locally — no credentials needed.

```bash
garmin skills list                 # one line per skill (name + description)
garmin skills get garmin-shared    # print a skill's body
garmin skills install              # interactive: ./.claude/skills or ~/.claude/skills
garmin skills install --output-dir ./.claude/skills   # non-interactive
```

Start with `garmin-shared` (the front door), then the per-resource skills
(`garmin-sleep`, `garmin-steps`, `garmin-activities`) and the
`recipe-reconstruct-day` workflow.

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

- **stdout**: JSON (default), NDJSON (`--format ndjson`, one object per line), or one-line text (`--format text`).
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

## License

[MIT](LICENSE).
