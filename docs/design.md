# garmin design

Design doc per `agent-cli:design-cli`. Records decisions and intentional
deviations so they aren't re-litigated. The CLI itself (`garmin schema`) is the
canonical operation surface; this doc captures the chassis decisions around it.

## Surface
- Shape: `garmin <resource> <action>` (single API surface).
- Resources/actions: `auth login`, `sleep get`, `steps get`, `activities list`,
  `schema --list` / `schema <op>`.
- Action verbs come from the `garminconnect` SDK vocabulary.

## Build identity
- CLI short name: `garmin`
- Source kind: **SDK wrapper** (`garminconnect`), not an HTTP API with a spec —
  so `wrap-api-spec` does not apply, and `--base-url` is N/A (the SDK hardcodes
  Garmin's endpoints; we don't control the HTTP layer).
- Read-only: no write/create/update/delete operations exist.

## Auth
- Scheme: Garmin OAuth tokens, acquired interactively (email + password + MFA)
  and cached by `garminconnect` in a token store directory.
- **Intentional deviation from §6/§15:** there is no `--access-token` flag,
  `GARMIN_*` env var, or `~/.config/garmin/config.yaml`. The SDK owns the OAuth
  token lifecycle; the only knob is the token-store **location**, exposed via the
  library's own `$GARMINTOKENS` env var (default `~/.garminconnect`).
- Precedence in practice: `$GARMINTOKENS` (location) → cached token store →
  interactive `garmin auth login`.
- Headless bootstrap (§15): run `garmin auth login` on a TTY machine, copy the
  token-store dir to the headless host (or point `$GARMINTOKENS` at it). There is
  no pre-minted single-token env var because Garmin's auth is a multi-token OAuth
  bundle, not one opaque key. Documented in README.

## Tenant
- Has tenant scope? **No** — one Garmin account per token store. §2 N/A.

## Output
- Formats: `json` (default), `ndjson` (one object per line; arrays stream,
  a scalar/dict emits a single line), `text` (one-line-per-record human form).
- **Envelope: mixed.** `sleep get` peels Garmin's outer `dailySleepDTO` wrapper
  and emits the inner object (so `--fields sleepStartTimestampGMT`, not
  `dailySleepDTO.sleepStartTimestampGMT`). `steps get` and `activities list`
  return Garmin's arrays as-is. Recorded here and in README per §5.
- `--fields a.b,c.d`: dotted-path mask; arrays descend implicitly.
- `steps` does client-side bucket aggregation: Garmin returns 15-min buckets;
  `--bucket` rolls them up (sum `steps`, most-active `primaryActivityLevel`).

## Pagination
- API paginates? **No** — Garmin returns whole-day payloads; `activities` takes a
  date range the SDK resolves in one call. §10 N/A (no `--page-*` flags).

## Global flags (deviations from §3)
- Present: `--format`, `--fields`, `--dry-run` — defined once in
  `cli._data_io_parent()` and inherited by the data ops via argparse
  `parents=[...]` (no per-subcommand duplication).
- N/A by design: `--yes` / `--json` / `--params` (read-only, no destructive or
  body-carrying ops), `--base-url` (SDK-fixed endpoints), `--<tenant>-id`,
  `--upload`, `--page-*`.

## Exit codes
- Standard 0–5 per §7 (`errors.py`).
- SDK errors raised during data calls are mapped in `_garmin._call`:
  rate-limit / connection / HTTP → `EXIT_API (1)`; auth rejection → `EXIT_AUTH
  (2)`. Without this they would surface as `EXIT_INTERNAL (5)`.

## Error hints
- Every `CliError` carries an agent-oriented `hint` (concrete next step).
- Auth-missing → run `garmin auth login`; rate-limit → wait and retry; no
  confirmed sleep → check Garmin Connect web UI; bad input → expected format.

## Sanitization
- Strategy: strip control chars **and** conversation role-tag patterns
  (`<system>` / `<assistant>` / `<human>` / `<user>`, case-insensitive) from all
  string fields before stdout (`output.sanitize`).
- Risky (user-controlled) fields: `activityName` (users name their own
  activities), and any free-text Garmin echoes back.

## Schema / introspection (§4)
- `garmin schema --list` and `garmin schema <op>`; offline, no credentials.
- Source of truth is the `OPS` registry in `schema.py`. No `<TypeName>` /
  `--resolve-refs` (no spec to resolve against); output shapes described in prose.

## Skills to ship (§11) — SHIPPED
- Bundled under `src/garmin_cli/skills/<name>/SKILL.md` (packaged into the wheel),
  reachable at runtime via `garmin skills list` / `get <name>` and installable
  with `garmin skills install [--output-dir]` (interactive scope/dir prompts when
  no `--output-dir`). All offline, no credentials.
- Skills: `garmin-shared` (front door), `garmin-sleep`, `garmin-steps`,
  `garmin-activities`, and recipe `recipe-reconstruct-day`. README remains the
  human quickstart; the agent reference now lives in the skills (§12).

## MCP (§18)
- Optional; not implemented.

## Open questions / backlog
- Optional MCP surface (§18).
