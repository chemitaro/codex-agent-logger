from __future__ import annotations

import argparse

from codex_logger import __version__
from codex_logger import log_store, payload
from codex_logger.console import error


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
    args = parse_args(argv)
    meta = payload.parse_best_effort(args.payload_json)

    try:
        log_store.save_raw_payload(
            args.payload_json,
            payload_cwd=meta.cwd,
            thread_id=meta.thread_id,
            turn_id=meta.turn_id,
        )
    except Exception as exc:
        error(f"failed to save raw payload: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

