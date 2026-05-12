"""Exit codes and structured CLI errors. See design doc §7-§8."""
import json
import sys
from dataclasses import dataclass

EXIT_OK = 0
EXIT_API = 1
EXIT_AUTH = 2
EXIT_VALIDATION = 3
EXIT_SCHEMA = 4
EXIT_INTERNAL = 5


@dataclass(frozen=True)
class CliError(Exception):
    message: str
    exit_code: int
    hint: str | None = None

    def __str__(self) -> str:
        return self.message


def emit(err: CliError) -> int:
    payload: dict[str, str] = {"error": err.message}
    if err.hint:
        payload["hint"] = err.hint
    sys.stderr.write(json.dumps(payload) + "\n")
    return err.exit_code
