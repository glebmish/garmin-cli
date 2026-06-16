"""Thin wrapper around garminconnect. Isolated so tests can monkeypatch."""

import os
from pathlib import Path
from typing import Any

from garmin_cli.errors import EXIT_API, EXIT_AUTH, CliError


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
    # `has_cached_tokens` supports GARMINTOKENS pointing at a .json file; in that
    # case create the parent dir, otherwise the token-store dir itself. Tokens
    # grant account access — keep the directory private (0o700).
    if path.suffix == ".json":
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    else:
        path.mkdir(parents=True, exist_ok=True, mode=0o700)

    client = Garmin(email=email, password=password, prompt_mfa=mfa_callback)
    client.login(tokenstore=str(path))

    if not has_cached_tokens():
        raise RuntimeError(f"login completed but no token file was written under {path}")
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


def _call(label: str, fn, *args):
    """Run an SDK call, mapping garminconnect errors to CliError exit codes.

    Without this, network/API errors fall through to the top-level
    `except Exception` and surface as EXIT_INTERNAL (5) instead of
    EXIT_API (1) / EXIT_AUTH (2). See design §7/§8.
    """
    from garminconnect import (
        GarminConnectAuthenticationError,
        GarminConnectConnectionError,
        GarminConnectTooManyRequestsError,
        HTTPError,
    )

    try:
        return fn(*args)
    except GarminConnectTooManyRequestsError as e:
        raise CliError(
            message=f"{label}: rate limited by Garmin: {e}",
            exit_code=EXIT_API,
            hint="rate limited; wait 10-30 min and retry, or narrow the date range",
        ) from e
    except GarminConnectAuthenticationError as e:
        raise CliError(
            message=f"{label}: Garmin rejected the session: {e}",
            exit_code=EXIT_AUTH,
            hint="tokens may be expired — re-run `garmin auth login`",
        ) from e
    except (GarminConnectConnectionError, HTTPError) as e:
        raise CliError(
            message=f"{label}: Garmin API/connection error: {e}",
            exit_code=EXIT_API,
            hint="transient Garmin API/network error; retry with backoff",
        ) from e


def get_sleep_data(date_iso: str) -> dict[str, Any]:
    return _call("sleep.get", _client().get_sleep_data, date_iso) or {}


def get_steps_data(date_iso: str) -> list[dict[str, Any]]:
    return _call("steps.get", _client().get_steps_data, date_iso) or []


def get_activities_by_date(
    start_iso: str,
    end_iso: str,
    activity_type: str | None = None,
) -> list[dict[str, Any]]:
    return (
        _call(
            "activities.list",
            _client().get_activities_by_date,
            start_iso,
            end_iso,
            activity_type,
        )
        or []
    )
