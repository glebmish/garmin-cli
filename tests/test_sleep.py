import json

import pytest

from garmin_cli import _garmin, sleep
from garmin_cli.errors import EXIT_API, EXIT_OK, CliError


def _set_response(monkeypatch, response):
    monkeypatch.setattr(_garmin, "get_sleep_data", lambda d: response)


def test_get_emits_dailysleepdto(monkeypatch, capsys):
    _set_response(
        monkeypatch,
        {
            "dailySleepDTO": {
                "sleepStartTimestampGMT": 1715450100000,
                "sleepEndTimestampGMT": 1715477700000,
                "sleepWindowConfirmed": True,
                "calendarDate": "2026-05-11",
            },
            "sleepLevels": [],
        },
    )
    rc = sleep.get("2026-05-11", fmt="json", fields=[], dry_run=False)
    assert rc == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["sleepWindowConfirmed"] is True
    assert payload["sleepStartTimestampGMT"] == 1715450100000
    # envelope was unwrapped — no top-level dailySleepDTO key
    assert "dailySleepDTO" not in payload
    # sibling keys like sleepLevels are dropped
    assert "sleepLevels" not in payload


def test_get_fields_filter(monkeypatch, capsys):
    _set_response(
        monkeypatch,
        {
            "dailySleepDTO": {
                "sleepStartTimestampGMT": 1,
                "sleepEndTimestampGMT": 2,
                "sleepWindowConfirmed": True,
                "junk": "drop me",
            }
        },
    )
    rc = sleep.get(
        "2026-05-11",
        fmt="json",
        fields=["sleepStartTimestampGMT", "sleepEndTimestampGMT"],
        dry_run=False,
    )
    assert rc == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload == {"sleepStartTimestampGMT": 1, "sleepEndTimestampGMT": 2}


def test_get_no_dto_raises_api_error(monkeypatch):
    _set_response(monkeypatch, {})
    with pytest.raises(CliError) as ei:
        sleep.get("2026-05-11", fmt="json", fields=[], dry_run=False)
    assert ei.value.exit_code == EXIT_API


def test_get_unconfirmed_window_raises(monkeypatch):
    _set_response(monkeypatch, {"dailySleepDTO": {"sleepWindowConfirmed": False}})
    with pytest.raises(CliError) as ei:
        sleep.get("2026-05-11", fmt="json", fields=[], dry_run=False)
    assert ei.value.exit_code == EXIT_API


def test_get_confirmed_without_timestamps_raises(monkeypatch):
    # a confirmed window with no start/end is not usable data — fail, don't
    # emit a misleading exit-0 record with null timestamps
    _set_response(monkeypatch, {"dailySleepDTO": {"sleepWindowConfirmed": True}})
    with pytest.raises(CliError) as ei:
        sleep.get("2026-05-11", fmt="json", fields=[], dry_run=False)
    assert ei.value.exit_code == EXIT_API


def test_get_dry_run_emits_plan(monkeypatch, capsys):
    called = []
    monkeypatch.setattr(_garmin, "get_sleep_data", lambda d: called.append(d))
    rc = sleep.get("2026-05-11", fmt="json", fields=[], dry_run=True)
    assert rc == EXIT_OK
    assert called == []  # network call NOT made
    err = json.loads(capsys.readouterr().err)
    assert err["would_call"] == "get_sleep_data"
    assert err["date"] == "2026-05-11"


def test_get_text_format(monkeypatch, capsys):
    _set_response(
        monkeypatch,
        {
            "dailySleepDTO": {
                "sleepStartTimestampGMT": 1715450100000,
                "sleepEndTimestampGMT": 1715477700000,
                "sleepWindowConfirmed": True,
            }
        },
    )
    rc = sleep.get("2026-05-11", fmt="text", fields=[], dry_run=False)
    assert rc == EXIT_OK
    out = capsys.readouterr().out
    assert "2026-05-11" in out
    assert "1715450100000" in out


def test_get_rejects_bad_date():
    with pytest.raises(CliError) as ei:
        sleep.get("not-a-date", fmt="json", fields=[], dry_run=False)
    assert ei.value.hint == "expected YYYY-MM-DD"
