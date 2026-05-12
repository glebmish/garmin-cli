"""Thin wrapper around garminconnect. Isolated so tests can monkeypatch."""
from typing import Any

from garmin_cli.errors import EXIT_AUTH, CliError


def login(email: str, password: str, mfa_callback) -> None:
    """Interactive login. Caches tokens to $GARMINTOKENS or ~/.garminconnect."""
    from garminconnect import Garmin

    client = Garmin(email=email, password=password, prompt_mfa=mfa_callback)
    client.login()


def get_sleep_data(date_iso: str) -> dict[str, Any]:
    """Return the raw garminconnect response. Raises CliError(EXIT_AUTH) on auth failure."""
    from garminconnect import (
        Garmin,
        GarminConnectAuthenticationError,
    )

    client = Garmin()
    try:
        client.login()
    except (GarminConnectAuthenticationError, FileNotFoundError) as e:
        raise CliError(
            message=f"garmin auth failed: {e}",
            exit_code=EXIT_AUTH,
            hint="no cached tokens at $GARMINTOKENS or ~/.garminconnect — run `garmin auth login`",
        ) from e

    return client.get_sleep_data(date_iso) or {}
