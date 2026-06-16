from datetime import date

import pytest

from garmin_cli.errors import EXIT_VALIDATION, CliError
from garmin_cli.validate import activity_type, bucket_minutes, date_param


def test_date_param_accepts_iso():
    assert date_param("date", "2026-05-11") == date(2026, 5, 11)


@pytest.mark.parametrize(
    "bad", ["2026/05/11", "2026-5-11", "yesterday", "", "2026-13-01", "../etc"]
)
def test_date_param_rejects_garbage(bad):
    with pytest.raises(CliError) as ei:
        date_param("date", bad)
    assert ei.value.exit_code == EXIT_VALIDATION
    assert ei.value.hint == "expected YYYY-MM-DD"


@pytest.mark.parametrize("value,expected", [
    ("15m", 15),
    ("30m", 30),
    ("45m", 45),
    ("60", 60),
    ("1h", 60),
    ("2h", 120),
    ("90 min", 90),
    ("1 hour", 60),
])
def test_bucket_minutes_accepts(value, expected):
    assert bucket_minutes(value) == expected


@pytest.mark.parametrize("bad", ["13m", "0m", "1441m", "25h", "foo", "", "-15", "15s"])
def test_bucket_minutes_rejects(bad):
    with pytest.raises(CliError) as ei:
        bucket_minutes(bad)
    assert ei.value.exit_code == EXIT_VALIDATION


@pytest.mark.parametrize("good", ["walking", "running", "cycling", "multi_sport"])
def test_activity_type_accepts(good):
    assert activity_type(good) == good


@pytest.mark.parametrize("bad", ["Walking", "walk!", "walk-ing", " walking", ""])
def test_activity_type_rejects(bad):
    with pytest.raises(CliError):
        activity_type(bad)
