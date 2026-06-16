"""JSON output: field filtering and string sanitization."""
import json
import re
import sys
from typing import Any

_SAFE_CONTROL = frozenset({"\t", "\n", "\r"})

# Strip conversation-role tags that user-controlled fields (e.g. activityName)
# could carry as a prompt-injection payload. Design §13.
_INJECTION_TAG_RE = re.compile(
    r"</?\s*(system|assistant|human|user)\s*>", re.IGNORECASE
)


def sanitize(value: Any) -> Any:
    """Strip control chars and role-tag injection patterns from strings, recursively."""
    if isinstance(value, str):
        stripped = "".join(c for c in value if c >= " " or c in _SAFE_CONTROL)
        return _INJECTION_TAG_RE.sub("", stripped)
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


def emit_ndjson(value: Any, fields: list[str] | None = None) -> None:
    """One JSON object per line. Arrays stream; a scalar/dict emits a single line."""
    payload = sanitize(value)
    if fields:
        payload = filter_fields(payload, fields)
    items = payload if isinstance(payload, list) else [payload]
    for item in items:
        json.dump(item, sys.stdout, sort_keys=True)
        sys.stdout.write("\n")
