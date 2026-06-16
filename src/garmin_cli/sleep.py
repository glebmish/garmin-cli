"""`garmin sleep get --date YYYY-MM-DD` — emits the dailySleepDTO."""
import json
import sys

from garmin_cli import _garmin
from garmin_cli.errors import EXIT_API, EXIT_OK, CliError
from garmin_cli.output import emit_json, emit_ndjson
from garmin_cli.validate import date_param


def get(date_str: str, fmt: str, fields: list[str], dry_run: bool) -> int:
    d = date_param("date", date_str)

    if dry_run:
        sys.stderr.write(
            json.dumps({"would_call": "get_sleep_data", "date": d.isoformat()}) + "\n"
        )
        return EXIT_OK

    raw = _garmin.get_sleep_data(d.isoformat())
    dto = raw.get("dailySleepDTO") if isinstance(raw, dict) else None
    if not dto:
        raise CliError(
            message=f"no dailySleepDTO returned for {d.isoformat()}",
            exit_code=EXIT_API,
            hint="no confirmed sleep for this date; check Garmin Connect web UI",
        )
    if not dto.get("sleepWindowConfirmed"):
        raise CliError(
            message=f"sleep window not confirmed for {d.isoformat()}",
            exit_code=EXIT_API,
            hint="no confirmed sleep for this date; check Garmin Connect web UI",
        )

    if fmt == "text":
        start = dto.get("sleepStartTimestampGMT")
        end = dto.get("sleepEndTimestampGMT")
        print(f"{d.isoformat()}: start_gmt_ms={start} end_gmt_ms={end} confirmed=true")
        return EXIT_OK

    if fmt == "ndjson":
        emit_ndjson(dto, fields)
        return EXIT_OK

    emit_json(dto, fields)
    return EXIT_OK
