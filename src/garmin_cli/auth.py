"""`garmin auth login` — interactive login that caches tokens."""

import getpass
import sys

from garmin_cli import _garmin
from garmin_cli.errors import EXIT_AUTH, EXIT_OK, CliError


def login() -> int:
    if not sys.stdin.isatty():
        raise CliError(
            message="auth login requires an interactive TTY (email + password + MFA)",
            exit_code=EXIT_AUTH,
            hint="run this command on a machine with a terminal, then copy "
            "~/.garminconnect to the headless host",
        )

    email = input("Garmin email: ").strip()
    password = getpass.getpass("Garmin password: ")

    def mfa() -> str:
        return input("MFA code: ").strip()

    try:
        path = _garmin.login(email, password, mfa)
    except Exception as e:
        msg = str(e)
        hint = "retry login; if MFA SMS not arriving, check Garmin Connect web UI"
        if "429" in msg or "rate limit" in msg.lower():
            hint = (
                "Garmin is rate-limiting your IP — wait 10–30 minutes and try "
                "again, or try from a different network"
            )
        elif "no token file was written" in msg:
            hint = (
                "login appeared to succeed but no token file was written — "
                "likely silent rate-limit; wait and retry"
            )
        # Don't interpolate the raw exception: garminconnect/requests error text
        # can embed the submitted email or request URL. Keep a generic message;
        # the hint carries the actionable guidance.
        raise CliError(
            message="login failed",
            exit_code=EXIT_AUTH,
            hint=hint,
        ) from e

    print(f"auth ok — tokens cached at {path}")
    return EXIT_OK
