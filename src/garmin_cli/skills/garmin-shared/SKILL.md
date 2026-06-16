---
name: garmin-shared
description: Use when driving the `garmin` CLI for any Garmin Connect data — the front door covering surface, global flags, output contract, exit codes, and error hints.
---

# garmin-shared

`garmin` is an agent-first, read-only CLI wrapping Garmin Connect (the
`garminconnect` library). One Garmin account per machine. Start here, then read
the per-resource skills (`garmin-sleep`, `garmin-steps`, `garmin-activities`).

## Discover the surface

The CLI is the source of truth — not docs.

```bash
garmin schema --list          # every operation, one per line
garmin schema sleep.get       # args, output shape, exit codes for one op
```

## Command surface

```
garmin auth login                       # one-time interactive login (TTY only)
garmin sleep get --date YYYY-MM-DD
garmin steps get --date YYYY-MM-DD [--bucket 30m]
garmin activities list (--date D | --start D --end D) [--type walking]
garmin schema --list | garmin schema <op>
garmin skills list | garmin skills get <name> | garmin skills install
```

## Global flags (on the data ops)

- `--format json|ndjson|text` — default `json`. `ndjson` streams one object per
  line (good for piping array results to `jq -c` / line tools).
- `--fields a.b,c.d` — dotted-path field mask, comma-separated. Arrays descend
  implicitly. Use it to protect context: pull only the keys you need.
- `--dry-run` — print the call that *would* be made (to stderr) and exit 0
  without touching the network.

## Output contract

- **stdout**: JSON (default), NDJSON, or one-line text.
- **stderr**: errors as JSON `{"error": ..., "hint": ...}`. Never mixed with
  success output.
- **Envelope is mixed**: `sleep get` peels Garmin's `dailySleepDTO` wrapper —
  use `--fields sleepStartTimestampGMT`, *not* `dailySleepDTO.sleep...`.
  `steps get` and `activities list` return arrays as-is.

## Exit codes

| Code | Meaning | Agent action |
|------|---------|--------------|
| 0 | success | — |
| 1 | API error (no confirmed sleep, Garmin 5xx, rate limit) | read `hint`; maybe retry |
| 2 | auth error (no/expired tokens) | run `garmin auth login` |
| 3 | validation error (bad `--date`/`--bucket`/`--type`) | fix the flag value |
| 4 | discovery error (unknown `schema <op>` / `skills get <name>`) | run the matching `--list`/`list` |
| 5 | internal error | report a bug |

Branch on the exit code, not on parsing the message.

## Error hints

Every error carries a `hint` aimed at you — the concrete next step. Examples:
no cached tokens → `run garmin auth login`; rate limited → `wait 10-30 min`;
bad date → `expected YYYY-MM-DD`.

## Patterns

```bash
# Inspect a call without making it
garmin steps get --date 2026-05-11 --bucket 30m --dry-run

# Minimise tokens with a field mask
garmin activities list --date 2026-05-11 --fields startTimeLocal,duration,distance

# Stream a big array to jq line-by-line
garmin activities list --start 2026-05-01 --end 2026-05-31 --format ndjson | jq -c .
```
