import json

from garmin_cli import _garmin
from garmin_cli.cli import main


def test_main_schema_list(capsys):
    rc = main(["schema", "--list"])
    assert rc == 0
    assert "sleep.get" in capsys.readouterr().out


def test_main_sleep_get_validation_error(capsys):
    rc = main(["sleep", "get", "--date", "bogus"])
    assert rc == 3
    err = json.loads(capsys.readouterr().err)
    assert err["hint"] == "expected YYYY-MM-DD"


def test_main_sleep_get_success(monkeypatch, capsys):
    monkeypatch.setattr(
        _garmin,
        "get_sleep_data",
        lambda d: {
            "dailySleepDTO": {
                "sleepStartTimestampGMT": 1,
                "sleepEndTimestampGMT": 2,
                "sleepWindowConfirmed": True,
            }
        },
    )
    rc = main(["sleep", "get", "--date", "2026-05-11"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["sleepWindowConfirmed"] is True
