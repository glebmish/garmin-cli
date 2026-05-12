import json

import pytest

from garmin_cli import _garmin, steps
from garmin_cli.errors import EXIT_OK, CliError


def _bucket(start, end, count, level="active"):
    return {
        "startGMT": start,
        "endGMT": end,
        "steps": count,
        "primaryActivityLevel": level,
    }


# The "day" we use in tests: 96 quarter-hour slots, but we'll only synthesize as many
# as a test needs and let aggregation chunk them.
def _make_day(values: list[tuple[int, str]]) -> list[dict]:
    """values: list of (steps, level). 15-min slots starting at midnight."""
    out = []
    for i, (n, lv) in enumerate(values):
        h, m = divmod(i * 15, 60)
        h2, m2 = divmod((i + 1) * 15, 60)
        out.append(_bucket(
            f"2026-05-11T{h:02d}:{m:02d}:00.0",
            f"2026-05-11T{h2:02d}:{m2:02d}:00.0",
            n,
            lv,
        ))
    return out


def test_aggregate_passthrough_at_15m():
    raw = _make_day([(10, "active"), (20, "sedentary")])
    assert steps.aggregate(raw, 15) == raw


def test_aggregate_30m_sums_steps_and_picks_max_level():
    raw = _make_day([
        (10, "sedentary"),
        (40, "active"),
        (5, "sedentary"),
        (3, "sedentary"),
    ])
    rolled = steps.aggregate(raw, 30)
    assert len(rolled) == 2
    assert rolled[0]["steps"] == 50
    assert rolled[0]["primaryActivityLevel"] == "active"  # max-rank
    assert rolled[0]["startGMT"] == raw[0]["startGMT"]
    assert rolled[0]["endGMT"] == raw[1]["endGMT"]
    assert rolled[1]["steps"] == 8
    assert rolled[1]["primaryActivityLevel"] == "sedentary"


def test_aggregate_1h_highly_active_wins():
    raw = _make_day([
        (5, "sedentary"),
        (200, "highlyActive"),
        (100, "active"),
        (10, "sedentary"),
    ])
    rolled = steps.aggregate(raw, 60)
    assert len(rolled) == 1
    assert rolled[0]["steps"] == 315
    assert rolled[0]["primaryActivityLevel"] == "highlyActive"


def test_aggregate_handles_partial_final_group():
    # 5 raw buckets, bucket=30 (group_size=2) → last group has only 1
    raw = _make_day([(n, "active") for n in (1, 2, 3, 4, 5)])
    rolled = steps.aggregate(raw, 30)
    assert len(rolled) == 3
    assert rolled[0]["steps"] == 3
    assert rolled[1]["steps"] == 7
    assert rolled[2]["steps"] == 5


def test_aggregate_unknown_level_ranks_lowest():
    raw = _make_day([(10, "weird"), (20, "sedentary")])
    rolled = steps.aggregate(raw, 30)
    assert rolled[0]["primaryActivityLevel"] == "sedentary"


def test_get_emits_aggregated_json(monkeypatch, capsys):
    raw = _make_day([(10, "sedentary"), (40, "active")])
    monkeypatch.setattr(_garmin, "get_steps_data", lambda d: raw)
    rc = steps.get("2026-05-11", bucket="30m", fmt="json", fields=[], dry_run=False)
    assert rc == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert len(payload) == 1
    assert payload[0]["steps"] == 50
    assert payload[0]["primaryActivityLevel"] == "active"


def test_get_dry_run_does_not_call(monkeypatch, capsys):
    called = []
    monkeypatch.setattr(_garmin, "get_steps_data", lambda d: called.append(d))
    rc = steps.get("2026-05-11", bucket="1h", fmt="json", fields=[], dry_run=True)
    assert rc == EXIT_OK
    assert called == []
    err = json.loads(capsys.readouterr().err)
    assert err["bucket_minutes"] == 60


def test_get_rejects_bad_bucket():
    with pytest.raises(CliError) as ei:
        steps.get("2026-05-11", bucket="13m", fmt="json", fields=[], dry_run=False)
    assert ei.value.exit_code == 3


def test_get_rejects_bad_date():
    with pytest.raises(CliError) as ei:
        steps.get("bogus", bucket="15m", fmt="json", fields=[], dry_run=False)
    assert ei.value.exit_code == 3
