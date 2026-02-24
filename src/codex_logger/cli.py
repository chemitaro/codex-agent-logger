from __future__ import annotations

import argparse

from codex_logger import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codex-logger")
    parser.add_argument("--telegram", action="store_true", help="Enable Telegram delivery.")
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show version and exit.",
    )
    parser.add_argument("payload_json", nargs="?", help="Codex notify payload JSON (last arg).")
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.payload_json is None:
        parser.error("the following arguments are required: payload_json")

    return args


def main(argv: list[str] | None = None) -> int:
    parse_args(argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
