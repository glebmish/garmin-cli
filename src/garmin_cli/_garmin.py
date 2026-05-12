"""Thin wrapper around garminconnect. Isolated so tests can monkeypatch."""
import os
from pathlib import Path
from typing import Any

from garmin_cli.errors import EXIT_AUTH, CliError


def token_dir() -> Path:
    return Path(os.environ.get("GARMINTOKENS") or "~/.garminconnect").expanduser()


def has_cached_tokens() -> bool:
    """The lib writes `garmin_tokens.json` inside the dir (or a .json file directly)."""
    p = token_dir()
    if p.is_file() and p.name.endswith(".json"):
        return True
    return p.is_dir() and any(p.glob("*.json"))


def login(email: str, password: str, mfa_callback) -> Path:
    """Interactive login. Persists tokens. Returns the directory they live in."""
    from garminconnect import Garmin

    path = token_dir()
    path.mkdir(parents=True, exist_ok=True)

    client = Garmin(email=email, password=password, prompt_mfa=mfa_callback)
    client.login(tokenstore=str(path))

    if not has_cached_tokens():
        raise RuntimeError(
            f"login completed but no token file was written under {path}"
        )
    return path


def _client():
    """Logged-in Garmin client. Raises CliError(EXIT_AUTH) if no cached tokens."""
    from garminconnect import Garmin, GarminConnectAuthenticationError

    path = token_dir()
    if not has_cached_tokens():
        raise CliError(
            message=f"no cached tokens at {path}",
            exit_code=EXIT_AUTH,
            hint="run `garmin auth login` (override location with $GARMINTOKENS)",
        )

    client = Garmin()
    try:
        client.login(tokenstore=str(path))
    except (GarminConnectAuthenticationError, FileNotFoundError) as e:
        raise CliError(
            message=f"garmin auth failed: {e}",
            exit_code=EXIT_AUTH,
            hint="tokens may be expired — re-run `garmin auth login`",
        ) from e
    return client


def get_sleep_data(date_iso: str) -> dict[str, Any]:
    return _client().get_sleep_data(date_iso) or {}


def get_steps_data(date_iso: str) -> list[dict[str, Any]]:
    return _client().get_steps_data(date_iso) or []


def get_activities_by_date(
    start_iso: str,
    end_iso: str,
    activity_type: str | None = None,
) -> list[dict[str, Any]]:
    return _client().get_activities_by_date(start_iso, end_iso, activity_type) or []
