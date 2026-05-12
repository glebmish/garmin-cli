# CLAUDE.md

## Project

Python CLI (`garmin`) wrapping the `garminconnect` library. Agent-first design per `agent-cli:design-cli`. v0 scope: sleep reading only.

## Build & test

```bash
uv sync
uv run pytest -v
uv tool install --reinstall --from . garmin-cli   # rebuild the `garmin` binary on PATH
```

## Architecture

- `src/garmin_cli/cli.py` — argparse root, subcommand dispatch, top-level error handler.
- `src/garmin_cli/auth.py` — `auth login` (interactive).
- `src/garmin_cli/sleep.py` — `sleep get`.
- `src/garmin_cli/schema.py` — `schema --list` / `schema <op>` + `OPS` registry.
- `src/garmin_cli/output.py` — JSON emit, dotted-path `--fields` filter, control-char sanitization.
- `src/garmin_cli/validate.py` — input hardening (`date_param`).
- `src/garmin_cli/errors.py` — exit codes + `CliError` with `hint`.
- `src/garmin_cli/_garmin.py` — thin wrapper around `garminconnect`. Tests monkeypatch this module.

## Adding a new operation

1. Implement the subcommand handler in `src/garmin_cli/<resource>.py`.
2. Wire it in `cli.py` (new subparser).
3. Add the entry to `OPS` in `schema.py` (this is the source of truth for `garmin schema`).
4. Add a test in `tests/`.

Conventions:

- Validate all input in `validate.py` *before* any network call. Raise `CliError(exit_code=EXIT_VALIDATION)`.
- Network calls go through `_garmin.py` so tests can monkeypatch.
- Output goes through `output.emit_json` (applies `--fields` + sanitize).
- Each `CliError` carries a `hint` aimed at an agent reader — concrete next step, no prose.
