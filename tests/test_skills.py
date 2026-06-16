"""`garmin skills` list / get / install — offline, no credentials."""

import json

import pytest

from garmin_cli import skills_cmd
from garmin_cli.errors import EXIT_OK, EXIT_SCHEMA, EXIT_VALIDATION, CliError

EXPECTED = {
    "garmin-shared",
    "garmin-sleep",
    "garmin-steps",
    "garmin-activities",
    "recipe-reconstruct-day",
}


def test_list_text_has_every_skill(capsys):
    rc = skills_cmd.list_("text")
    assert rc == EXIT_OK
    out = capsys.readouterr().out
    for name in EXPECTED:
        assert name in out


def test_list_json_is_array_with_name_and_description(capsys):
    rc = skills_cmd.list_("json")
    assert rc == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    names = {s["name"] for s in payload}
    assert names == EXPECTED
    for s in payload:
        assert s["description"].startswith("Use when")


def test_get_text_prints_body_without_frontmatter(capsys):
    rc = skills_cmd.get("garmin-shared", "text")
    assert rc == EXIT_OK
    out = capsys.readouterr().out
    assert out.startswith("# garmin-shared")
    assert "description:" not in out.splitlines()[0]


def test_get_json_envelope(capsys):
    rc = skills_cmd.get("garmin-sleep", "json")
    assert rc == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["name"] == "garmin-sleep"
    assert "SKILL.md" in payload["files"]
    assert payload["description"].startswith("Use when")


def test_get_unknown_skill_is_discovery_error():
    with pytest.raises(CliError) as ei:
        skills_cmd.get("garmin-nope", "text")
    assert ei.value.exit_code == EXIT_SCHEMA


def test_install_to_output_dir_copies_all(tmp_path, capsys):
    rc = skills_cmd.install(str(tmp_path / "skills"))
    assert rc == EXIT_OK
    for name in EXPECTED:
        assert (tmp_path / "skills" / name / "SKILL.md").is_file()
    assert "installed 5 skills" in capsys.readouterr().out


def test_install_non_interactive_without_output_dir_errors(monkeypatch):
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    with pytest.raises(CliError) as ei:
        skills_cmd.install(None)
    assert ei.value.exit_code == EXIT_VALIDATION
