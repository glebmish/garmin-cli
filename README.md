# garmin-cli

Agent-first CLI for [Garmin Connect](https://connect.garmin.com). Wraps the [`garminconnect`](https://github.com/cyberjunky/python-garminconnect) Python library so it can be driven from a shell or by an AI agent.

**Scope (v0):** sleep reading only. Designed to grow.

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

# Just the timestamps
garmin sleep get --date 2026-05-11 \
  --fields sleepStartTimestampGMT,sleepEndTimestampGMT,sleepWindowConfirmed

# What operations exist?
garmin schema --list

# What does sleep.get accept and return?
garmin schema sleep.get
```

## Output contract

- **stdout**: JSON (default) or one-line text (`--format text`).
- **stderr**: errors as JSON `{"error": ..., "hint": ...}`.
- **`--fields a.b,c.d`**: dotted-path filter, comma-separated. Arrays descend implicitly.
- **Envelope**: `garmin sleep get` peels Garmin's outer `dailySleepDTO` wrapper; you consume the inner object directly. So `--fields sleepStartTimestampGMT` (not `dailySleepDTO.sleepStartTimestampGMT`).

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
