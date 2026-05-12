import json

import pytest

from garmin_cli.errors import EXIT_OK, EXIT_SCHEMA, CliError
from garmin_cli.schema import describe, list_ops, OPS


def test_list_ops_prints_sleep_get(capsys):
    assert list_ops() == EXIT_OK
    out = capsys.readouterr().out
    assert "sleep.get" in out.splitlines()


def test_describe_known_op(capsys):
    assert describe("sleep.get") == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["method"] == "GET"
    assert any(a["name"] == "--date" for a in payload["args"])


def test_describe_unknown_op_raises():
    with pytest.raises(CliError) as ei:
        describe("does.not.exist")
    assert ei.value.exit_code == EXIT_SCHEMA


def test_ops_registry_nonempty():
    assert "sleep.get" in OPS
