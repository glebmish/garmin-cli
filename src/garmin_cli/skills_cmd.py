"""`garmin skills` — bundled agent skills: list / get / install.

Offline, no credentials. Skills ship as package data under `skills/<name>/SKILL.md`
so agents can reach them whether or not they were installed to disk (design §11).
"""

import json
import sys
from importlib.resources import files
from pathlib import Path

from garmin_cli.errors import EXIT_OK, EXIT_SCHEMA, EXIT_VALIDATION, CliError


def _root():
    return files("garmin_cli") / "skills"


def _skill_dirs():
    return sorted(
        (p for p in _root().iterdir() if (p / "SKILL.md").is_file()),
        key=lambda p: p.name,
    )


def _split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                meta: dict[str, str] = {}
                for ln in lines[1:i]:
                    if ":" in ln and not ln.startswith((" ", "\t")):
                        k, _, v = ln.partition(":")
                        meta[k.strip()] = v.strip()
                body = "\n".join(lines[i + 1 :]).strip() + "\n"
                return meta, body
    return {}, text


def _parse(skill_dir) -> dict:
    meta, body = _split_frontmatter((skill_dir / "SKILL.md").read_text(encoding="utf-8"))
    return {
        "dir": skill_dir,
        "name": meta.get("name", skill_dir.name),
        "description": meta.get("description", ""),
        "frontmatter": meta,
        "body": body,
    }


def list_(fmt: str) -> int:
    skills = [_parse(d) for d in _skill_dirs()]
    if fmt == "json":
        payload = [
            s["frontmatter"] or {"name": s["name"], "description": s["description"]} for s in skills
        ]
        json.dump(payload, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        for s in skills:
            print(f"{s['name']}  {s['description']}")
    return EXIT_OK


def get(name: str, fmt: str) -> int:
    for d in _skill_dirs():
        s = _parse(d)
        if s["name"] == name:
            if fmt == "json":
                file_names = sorted(f.name for f in d.iterdir())
                json.dump(
                    {
                        "name": s["name"],
                        "description": s["description"],
                        "files": file_names,
                    },
                    sys.stdout,
                    indent=2,
                    sort_keys=True,
                )
                sys.stdout.write("\n")
            else:
                sys.stdout.write(s["body"])
                if not s["body"].endswith("\n"):
                    sys.stdout.write("\n")
            return EXIT_OK
    raise CliError(
        message=f"unknown skill: {name!r}",
        exit_code=EXIT_SCHEMA,
        hint="run `garmin skills list` to see bundled skills",
    )


def _interactive_target() -> Path:
    if not sys.stdin.isatty():
        raise CliError(
            message="skills install needs --output-dir in a non-interactive shell",
            exit_code=EXIT_VALIDATION,
            hint="pass --output-dir <path> (e.g. ./.claude/skills)",
        )
    scope = input("Scope — [p]roject (./) or [u]ser (~/)? ").strip().lower()
    home = scope.startswith("u")
    base = Path.home() if home else Path(".")
    sub = input("Dir — [1] .claude/skills or [2] .agents/skills? ").strip()
    leaf = ".agents" if sub == "2" else ".claude"
    return base / leaf / "skills"


def _copy_tree(src, dest: Path) -> None:
    """Recursively copy a packaged skill dir to disk as bytes.

    Uses the importlib.resources Traversable API (iterdir/is_dir/read_bytes) so
    nested directories and binary assets copy cleanly — a flat text-only copy
    would crash on either.
    """
    dest.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        out = dest / item.name
        if item.is_dir():
            _copy_tree(item, out)
        else:
            out.write_bytes(item.read_bytes())


def install(output_dir: str | None) -> int:
    target = Path(output_dir).expanduser() if output_dir else _interactive_target()
    target.mkdir(parents=True, exist_ok=True)

    count = 0
    for d in _skill_dirs():
        _copy_tree(d, target / d.name)
        count += 1

    print(f"installed {count} skills to {target}")
    return EXIT_OK
