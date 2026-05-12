"""argparse root + dispatch."""
import argparse
import sys

from garmin_cli import auth, schema, sleep
from garmin_cli.errors import EXIT_INTERNAL, CliError, emit


def _split_fields(value: str | None) -> list[str]:
    if not value:
        return []
    return [p.strip() for p in value.split(",") if p.strip()]


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="garmin",
        description="Agent-first CLI for Garmin Connect.",
    )
    sub = p.add_subparsers(dest="resource", required=True)

    # auth
    p_auth = sub.add_parser("auth", help="Authentication.")
    sub_auth = p_auth.add_subparsers(dest="action", required=True)
    sub_auth.add_parser("login", help="Interactive login; caches tokens.")

    # sleep
    p_sleep = sub.add_parser("sleep", help="Sleep data.")
    sub_sleep = p_sleep.add_subparsers(dest="action", required=True)
    p_sleep_get = sub_sleep.add_parser("get", help="Fetch dailySleepDTO for a date.")
    p_sleep_get.add_argument("--date", required=True, help="Wake date (YYYY-MM-DD).")
    p_sleep_get.add_argument("--format", choices=["json", "text"], default="json")
    p_sleep_get.add_argument("--fields", default="", help="Dotted-path filter, comma-separated.")
    p_sleep_get.add_argument("--dry-run", action="store_true")

    # schema
    p_schema = sub.add_parser("schema", help="Operation introspection.")
    g = p_schema.add_mutually_exclusive_group(required=True)
    g.add_argument("--list", action="store_true", dest="list_ops")
    g.add_argument("op", nargs="?", help="Operation name (e.g. sleep.get).")

    return p


def dispatch(args: argparse.Namespace) -> int:
    if args.resource == "auth" and args.action == "login":
        return auth.login()
    if args.resource == "sleep" and args.action == "get":
        return sleep.get(
            date_str=args.date,
            fmt=args.format,
            fields=_split_fields(args.fields),
            dry_run=args.dry_run,
        )
    if args.resource == "schema":
        if args.list_ops:
            return schema.list_ops()
        return schema.describe(args.op)
    raise CliError(message=f"unknown command: {args}", exit_code=EXIT_INTERNAL)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return dispatch(args)
    except CliError as e:
        return emit(e)
    except KeyboardInterrupt:
        return 130
    except Exception as e:
        return emit(CliError(message=f"internal error: {e}", exit_code=EXIT_INTERNAL))


if __name__ == "__main__":
    sys.exit(main())
