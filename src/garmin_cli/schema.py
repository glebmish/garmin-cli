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
