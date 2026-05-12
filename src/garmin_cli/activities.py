"""`garmin activities list` — Garmin's auto-detected activity records."""
import json
import sys

from garmin_cli import _garmin
from garmin_cli.errors import EXIT_OK, EXIT_VALIDATION, CliError
from garmin_cli.output import emit_json
from garmin_cli.validate import activity_type, date_param


def list_(
    date_str: str | None,
    start_str: str | None,
    end_str: str | None,
    activity_type_str: str | None,
    fmt: str,
    fields: list[str],
    dry_run: bool,
) -> int:
    if date_str and (start_str or end_str):
        raise CliError(
            message="--date is mutually exclusive with --start/--end",
            exit_code=EXIT_VALIDATION,
            hint="pass either --date YYYY-MM-DD or --start/--end",
        )
    if (start_str and not end_str) or (end_str and not start_str):
        raise CliError(
            message="--start and --end must be passed together",
            exit_code=EXIT_VALIDATION,
        )
    if not date_str and not start_str:
        raise CliError(
            message="missing date range",
            exit_code=EXIT_VALIDATION,
            hint="pass --date YYYY-MM-DD or --start/--end",
        )

    if date_str:
        d = date_param("date", date_str)
        start, end = d, d
    else:
        start = date_param("start", start_str)  # type: ignore[arg-type]
        end = date_param("end", end_str)  # type: ignore[arg-type]
        if end < start:
            raise CliError(
                message=f"--end {end_str!r} is before --start {start_str!r}",
                exit_code=EXIT_VALIDATION,
            )

    type_arg = activity_type(activity_type_str) if activity_type_str else None

    if dry_run:
        sys.stderr.write(json.dumps({
            "would_call": "get_activities_by_date",
            "start": start.isoformat(),
            "end": end.isoformat(),
            "type": type_arg,
        }) + "\n")
        return EXIT_OK

    activities = _garmin.get_activities_by_date(start.isoformat(), end.isoformat(), type_arg)

    if fmt == "text":
        for a in activities:
            print(
                f"{a.get('startTimeLocal')} {a.get('activityType', {}).get('typeKey')}: "
                f"{a.get('activityName')} ({a.get('duration')}s, {a.get('distance')}m)"
            )
        return EXIT_OK

    emit_json(activities, fields)
    return EXIT_OK
