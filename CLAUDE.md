# CLAUDE.md

## Project

Python CLI (`garmin`) wrapping the `garminconnect` library. Agent-first design per `agent-cli:design-cli`. Current scope: sleep, steps (with client-side bucket aggregation), and auto-detected activities.

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
- `src/garmin_cli/steps.py` — `steps get` + client-side bucket aggregation (`aggregate()` is the testable seam).
- `src/garmin_cli/activities.py` — `activities list` with `--date` or `--start/--end`.
- `src/garmin_cli/schema.py` — `schema --list` / `schema <op>` + `OPS` registry.
- `src/garmin_cli/skills_cmd.py` — `skills list` / `get` / `install`; loads bundled skills via `importlib.resources`.
- `src/garmin_cli/skills/<name>/SKILL.md` — bundled agent skills (package data, shipped in the wheel).
- `src/garmin_cli/output.py` — JSON/NDJSON emit, dotted-path `--fields` filter, control-char + role-tag sanitization.
- `src/garmin_cli/validate.py` — input hardening (`date_param`, `bucket_minutes`, `activity_type`).
- `src/garmin_cli/errors.py` — exit codes + `CliError` with `hint`.
- `src/garmin_cli/_garmin.py` — thin wrapper around `garminconnect`; `_call()` maps SDK errors to exit codes. Tests monkeypatch this module.

Design decisions and intentional deviations from `agent-cli:design-cli` are recorded in `docs/design.md`.

## Adding a new operation

1. Implement the subcommand handler in `src/garmin_cli/<resource>.py`.
2. Wire it in `cli.py` (new subparser).
3. Add the entry to `OPS` in `schema.py` (this is the source of truth for `garmin schema`).
4. Add a bundled skill under `src/garmin_cli/skills/garmin-<resource>/SKILL.md` documenting its quirks.
5. Add a test in `tests/`.

Conventions:

- Validate all input in `validate.py` *before* any network call. Raise `CliError(exit_code=EXIT_VALIDATION)`.
- Network calls go through `_garmin.py` so tests can monkeypatch.
- Output goes through `output.emit_json` / `emit_ndjson` (applies `--fields` + sanitize).
- Each `CliError` carries a `hint` aimed at an agent reader — concrete next step, no prose.
