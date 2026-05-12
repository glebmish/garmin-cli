"""`garmin schema` — operation introspection. The CLI is the source of truth."""
import json
import sys

from garmin_cli.errors import EXIT_OK, EXIT_SCHEMA, CliError

OPS: dict[str, dict] = {
    "sleep.get": {
        "method": "GET",
        "description": "Fetch raw dailySleepDTO for a wake date.",
        "args": [
            {"name": "--date", "type": "date (YYYY-MM-DD)", "required": True},
        ],
        "output": "dailySleepDTO object (Garmin's raw shape). Includes sleepStartTimestampGMT, sleepEndTimestampGMT, sleepWindowConfirmed, and many other fields.",
        "exit_codes": {
            "0": "success",
            "1": "no confirmed sleep for date",
            "2": "auth missing/expired",
            "3": "bad --date format",
        },
    },
    "steps.get": {
        "method": "GET",
        "description": "Step buckets for a date. Garmin returns 15-minute buckets; --bucket rolls them up client-side.",
        "args": [
            {"name": "--date", "type": "date (YYYY-MM-DD)", "required": True},
            {"name": "--bucket", "type": "duration (15m, 30m, 1h, ...)", "required": False, "default": "15m", "constraint": "multiple of 15 min, 15m..1440m"},
        ],
        "output": "Array of bucket objects: {startGMT, endGMT, steps, primaryActivityLevel}. primaryActivityLevel is one of: none, sleeping, sedentary, active, highlyActive. When aggregating, the most-active level across constituent 15-min buckets wins.",
        "exit_codes": {
            "0": "success",
            "2": "auth missing/expired",
            "3": "bad --date or --bucket",
        },
    },
    "activities.list": {
        "method": "GET",
        "description": "Garmin-auto-detected activity records (walks, runs, rides) by date or range.",
        "args": [
            {"name": "--date", "type": "date (YYYY-MM-DD)", "required": False, "note": "single-day; mutually exclusive with --start/--end"},
            {"name": "--start", "type": "date (YYYY-MM-DD)", "required": False, "note": "use with --end"},
            {"name": "--end", "type": "date (YYYY-MM-DD)", "required": False, "note": "use with --start"},
            {"name": "--type", "type": "string", "required": False, "note": "filter by typeKey: walking, running, cycling, swimming, hiking, multi_sport, fitness_equipment, other"},
        ],
        "output": "Array of activity records (Garmin's raw shape). Useful keys: startTimeLocal, startTimeGMT, duration (seconds), distance (meters), activityType.typeKey, activityName, activityId.",
        "exit_codes": {
            "0": "success",
            "2": "auth missing/expired",
            "3": "bad date, missing range, or invalid --type",
        },
    },
}


def list_ops() -> int:
    for name in sorted(OPS):
        print(name)
    return EXIT_OK


def describe(op: str) -> int:
    if op not in OPS:
        raise CliError(
            message=f"unknown operation: {op!r}",
            exit_code=EXIT_SCHEMA,
            hint="run `garmin schema --list` to see all operations",
        )
    json.dump(OPS[op], sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return EXIT_OK
