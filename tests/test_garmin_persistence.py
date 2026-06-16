"""Verify _garmin.login persists tokens and detects silent failures."""

import pytest

from garmin_cli import _garmin


class FakeGarmin:
    """Stand-in for garminconnect.Garmin. login() can be made to write tokens or not."""

    last_tokenstore: str | None = None

    def __init__(self, email=None, password=None, prompt_mfa=None):
        self.email = email
        self.password = password
        self.prompt_mfa = prompt_mfa
        FakeGarmin.last_tokenstore = None

    def login(self, tokenstore=None):
        FakeGarmin.last_tokenstore = tokenstore
        # Simulate the lib's behaviour: write tokens file if tokenstore given.
        from pathlib import Path

        if tokenstore and getattr(FakeGarmin, "_should_write", True):
            p = Path(tokenstore)
            p.mkdir(parents=True, exist_ok=True)
            (p / "garmin_tokens.json").write_text('{"di_token": "fake"}')


def _install_fake(monkeypatch, *, write: bool):
    FakeGarmin._should_write = write  # type: ignore[attr-defined]
    import garminconnect

    monkeypatch.setattr(garminconnect, "Garmin", FakeGarmin)


def test_login_persists_tokens(monkeypatch, tmp_path):
    monkeypatch.setenv("GARMINTOKENS", str(tmp_path / "tokens"))
    _install_fake(monkeypatch, write=True)

    path = _garmin.login("u@example.com", "pw", lambda: "000000")

    assert path == tmp_path / "tokens"
    assert (path / "garmin_tokens.json").exists()
    assert FakeGarmin.last_tokenstore == str(path)


def test_login_detects_silent_failure(monkeypatch, tmp_path):
    """If lib's login() returns but writes nothing, we must raise."""
    monkeypatch.setenv("GARMINTOKENS", str(tmp_path / "tokens"))
    _install_fake(monkeypatch, write=False)

    with pytest.raises(RuntimeError, match="no token file was written"):
        _garmin.login("u@example.com", "pw", lambda: "000000")


def test_has_cached_tokens(monkeypatch, tmp_path):
    d = tmp_path / "tokens"
    monkeypatch.setenv("GARMINTOKENS", str(d))
    assert not _garmin.has_cached_tokens()
    d.mkdir()
    assert not _garmin.has_cached_tokens()
    (d / "garmin_tokens.json").write_text("{}")
    assert _garmin.has_cached_tokens()


def test_has_cached_tokens_accepts_json_file_path(monkeypatch, tmp_path):
    f = tmp_path / "my.json"
    monkeypatch.setenv("GARMINTOKENS", str(f))
    assert not _garmin.has_cached_tokens()
    f.write_text("{}")
    assert _garmin.has_cached_tokens()


def test_default_token_dir(monkeypatch):
    monkeypatch.delenv("GARMINTOKENS", raising=False)
    assert _garmin.token_dir().name == ".garminconnect"
