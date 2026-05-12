from datetime import date

import pytest

from garmin_cli.errors import EXIT_VALIDATION, CliError
from garmin_cli.validate import date_param


def test_date_param_accepts_iso():
    assert date_param("date", "2026-05-11") == date(2026, 5, 11)


@pytest.mark.parametrize("bad", ["2026/05/11", "2026-5-11", "yesterday", "", "2026-13-01", "../etc"])
def test_date_param_rejects_garbage(bad):
    with pytest.raises(CliError) as ei:
        date_param("date", bad)
    assert ei.value.exit_code == EXIT_VALIDATION
    assert ei.value.hint == "expected YYYY-MM-DD"
