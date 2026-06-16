"""SDK errors from data calls map to the right exit codes (design §7/§8)."""

import pytest

from garmin_cli import _garmin
from garmin_cli.errors import EXIT_API, EXIT_AUTH, CliError


class _FakeClient:
    def __init__(self, exc):
        self._exc = exc

    def _raise(self, *_args, **_kwargs):
        raise self._exc

    get_sleep_data = _raise
    get_steps_data = _raise
    get_activities_by_date = _raise


def _install(monkeypatch, exc):
    monkeypatch.setattr(_garmin, "_client", lambda: _FakeClient(exc))


def test_rate_limit_maps_to_api_error(monkeypatch):
    from garminconnect import GarminConnectTooManyRequestsError

    _install(monkeypatch, GarminConnectTooManyRequestsError("429"))
    with pytest.raises(CliError) as ei:
        _garmin.get_sleep_data("2026-05-11")
    assert ei.value.exit_code == EXIT_API
    assert "rate" in (ei.value.hint or "").lower()


def test_connection_error_maps_to_api_error(monkeypatch):
    from garminconnect import GarminConnectConnectionError

    _install(monkeypatch, GarminConnectConnectionError("boom"))
    with pytest.raises(CliError) as ei:
        _garmin.get_steps_data("2026-05-11")
    assert ei.value.exit_code == EXIT_API


def test_http_error_maps_to_api_error(monkeypatch):
    from garminconnect import HTTPError

    _install(monkeypatch, HTTPError("500 Server Error"))
    with pytest.raises(CliError) as ei:
        _garmin.get_activities_by_date("2026-05-11", "2026-05-11", None)
    assert ei.value.exit_code == EXIT_API


def test_auth_error_during_call_maps_to_auth(monkeypatch):
    from garminconnect import GarminConnectAuthenticationError

    _install(monkeypatch, GarminConnectAuthenticationError("token rejected"))
    with pytest.raises(CliError) as ei:
        _garmin.get_sleep_data("2026-05-11")
    assert ei.value.exit_code == EXIT_AUTH
