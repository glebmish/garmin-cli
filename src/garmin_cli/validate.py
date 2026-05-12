"""Input hardening. Reject before any HTTP call."""
import re
from datetime import date

from garmin_cli.errors import EXIT_VALIDATION, CliError

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


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
