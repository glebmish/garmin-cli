"""Thin wrapper around garminconnect. Isolated so tests can monkeypatch."""
from typing import Any

from garmin_cli.errors import EXIT_AUTH, CliError


def login(email: str, password: str, mfa_callback) -> None:
    """Interactive login. Caches tokens to $GARMINTOKENS or ~/.garminconnect."""
    from garminconnect import Garmin

    client = Garmin(email=email, password=password, prompt_mfa=mfa_callback)
    client.login()


def _client():
    """Logged-in Garmin client. Raises CliError(EXIT_AUTH) if no cached tokens."""
    from garminconnect import Garmin, GarminConnectAuthenticationError

    client = Garmin()
    try:
        client.login()
    except (GarminConnectAuthenticationError, FileNotFoundError) as e:
        raise CliError(
            message=f"garmin auth failed: {e}",
            exit_code=EXIT_AUTH,
            hint="no cached tokens at $GARMINTOKENS or ~/.garminconnect — run `garmin auth login`",
        ) from e
    return client


def get_sleep_data(date_iso: str) -> dict[str, Any]:
    return _client().get_sleep_data(date_iso) or {}


def get_steps_data(date_iso: str) -> list[dict[str, Any]]:
    """Return Garmin's 15-minute step buckets for the day."""
    return _client().get_steps_data(date_iso) or []


def get_activities_by_date(
    start_iso: str,
    end_iso: str,
    activity_type: str | None = None,
) -> list[dict[str, Any]]:
    return _client().get_activities_by_date(start_iso, end_iso, activity_type) or []
