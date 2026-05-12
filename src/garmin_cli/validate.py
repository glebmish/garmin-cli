"""Input hardening. Reject before any HTTP call."""
import re
from datetime import date

from garmin_cli.errors import EXIT_VALIDATION, CliError

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_BUCKET_RE = re.compile(r"^(\d+)\s*(m|min|h|hr|hours?|minutes?)?$", re.IGNORECASE)
_TYPE_RE = re.compile(r"^[a-z_]+$")


def bucket_minutes(value: str) -> int:
    """Parse `--bucket` value to minutes. Accepts 15, 15m, 30min, 1h, 2hr.

    Constraints: multiple of 15, between 15 and 1440.
    """
    m = _BUCKET_RE.match(value.strip())
    if not m:
        raise CliError(
            message=f"invalid --bucket: {value!r}",
            exit_code=EXIT_VALIDATION,
            hint="examples: 15m, 30m, 1h, 90m",
        )
    n = int(m.group(1))
    unit = (m.group(2) or "m").lower()
    minutes = n * 60 if unit.startswith("h") else n
    if minutes < 15 or minutes > 1440 or minutes % 15 != 0:
        raise CliError(
            message=f"invalid --bucket: {value!r} ({minutes} min)",
            exit_code=EXIT_VALIDATION,
            hint="must be a multiple of 15 minutes, between 15m and 1440m (24h)",
        )
    return minutes


def activity_type(value: str) -> str:
    if not _TYPE_RE.match(value):
        raise CliError(
            message=f"invalid --type: {value!r}",
            exit_code=EXIT_VALIDATION,
            hint="lowercase letters and underscores only (e.g. walking, running, cycling)",
        )
    return value


def date_param(name: str, value: str) -> date:
    if not _DATE_RE.match(value):
        raise CliError(
            message=f"invalid {name}: {value!r}",
            exit_code=EXIT_VALIDATION,
            hint="expected YYYY-MM-DD",
        )
    try:
        return date.fromisoformat(value)
    except ValueError as e:
        raise CliError(
            message=f"invalid {name}: {value!r} ({e})",
            exit_code=EXIT_VALIDATION,
            hint="expected YYYY-MM-DD",
        ) from e
