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
            hint="run this command on a machine with a terminal, then copy ~/.garminconnect to the headless host",
        )

    email = input("Garmin email: ").strip()
    password = getpass.getpass("Garmin password: ")

    def mfa() -> str:
        return input("MFA code: ").strip()

    try:
        _garmin.login(email, password, mfa)
    except Exception as e:
        raise CliError(
            message=f"login failed: {e}",
            exit_code=EXIT_AUTH,
            hint="retry login; if MFA SMS not arriving, check Garmin Connect web UI",
        ) from e

    print("auth ok — tokens cached at $GARMINTOKENS or ~/.garminconnect")
    return EXIT_OK
