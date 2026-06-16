"""`garmin steps get --date YYYY-MM-DD [--bucket 30m]` — step buckets."""

import json
import sys
from typing import Any

from garmin_cli import _garmin
from garmin_cli.errors import EXIT_OK
from garmin_cli.output import emit_json, emit_ndjson, sanitize
from garmin_cli.validate import bucket_minutes, date_param

# Most-active level wins when aggregating.
_LEVEL_RANK: dict[str, int] = {
    "none": 0,
    "sleeping": 1,
    "sedentary": 2,
    "active": 3,
    "highlyActive": 4,
}


def _max_level(levels: list[str]) -> str:
    if not levels:
        return "none"
    return max(levels, key=lambda lv: _LEVEL_RANK.get(lv, 0))


def aggregate(raw: list[dict[str, Any]], bucket_min: int) -> list[dict[str, Any]]:
    """Roll up 15-min Garmin buckets into `bucket_min`-minute groups."""
    group_size = bucket_min // 15
    if group_size <= 1:
        return raw
    out: list[dict[str, Any]] = []
    for i in range(0, len(raw), group_size):
        chunk = raw[i : i + group_size]
        if not chunk:
            continue
        out.append(
            {
                "startGMT": chunk[0].get("startGMT"),
                "endGMT": chunk[-1].get("endGMT"),
                "steps": sum(int(b.get("steps") or 0) for b in chunk),
                "primaryActivityLevel": _max_level(
                    [b.get("primaryActivityLevel") or "none" for b in chunk]
                ),
            }
        )
    return out


def get(date_str: str, bucket: str, fmt: str, fields: list[str], dry_run: bool) -> int:
    d = date_param("date", date_str)
    minutes = bucket_minutes(bucket)

    if dry_run:
        sys.stderr.write(
            json.dumps(
                {
                    "would_call": "get_steps_data",
                    "date": d.isoformat(),
                    "bucket_minutes": minutes,
                }
            )
            + "\n"
        )
        return EXIT_OK

    raw = _garmin.get_steps_data(d.isoformat())
    buckets = aggregate(raw, minutes)

    if fmt == "text":
        for b in sanitize(buckets):
            print(
                f"{b.get('startGMT')} → {b.get('endGMT')}: "
                f"steps={b.get('steps')} level={b.get('primaryActivityLevel')}"
            )
        return EXIT_OK

    if fmt == "ndjson":
        emit_ndjson(buckets, fields)
        return EXIT_OK

    emit_json(buckets, fields)
    return EXIT_OK
