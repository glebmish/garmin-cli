"""JSON output: field filtering and string sanitization."""
import json
import sys
from typing import Any

_SAFE_CONTROL = frozenset({"\t", "\n", "\r"})


def sanitize(value: Any) -> Any:
    """Strip control chars from string values, recursively."""
    if isinstance(value, str):
        return "".join(c for c in value if c >= " " or c in _SAFE_CONTROL)
    if isinstance(value, list):
        return [sanitize(v) for v in value]
    if isinstance(value, dict):
        return {k: sanitize(v) for k, v in value.items()}
    return value


def filter_fields(value: Any, fields: list[str]) -> Any:
    """Keep only the dotted paths in `fields`. Arrays descend implicitly."""
    if not fields:
        return value
    paths = [f.split(".") for f in fields]
    return _walk(value, paths)


def _walk(value: Any, paths: list[list[str]]) -> Any:
    if isinstance(value, list):
        return [_walk(item, paths) for item in value]
    if not isinstance(value, dict):
        return value
    out: dict[str, Any] = {}
    for path in paths:
        head, *rest = path
        if head not in value:
            continue
        if not rest:
            out[head] = value[head]
        else:
            sub = _walk(value[head], [rest])
            if sub != {} or isinstance(value[head], dict) is False:
                out[head] = sub
    return out


def emit_json(value: Any, fields: list[str] | None = None) -> None:
    payload = sanitize(value)
    if fields:
        payload = filter_fields(payload, fields)
    json.dump(payload, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
