from __future__ import annotations

import argparse

from codex_logger import __version__
from codex_logger import log_store, payload, summary, telegram
from codex_logger.console import error, warn

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
        saved_path = log_store.save_raw_payload(
            args.payload_json,
            payload_cwd=meta.cwd,
            thread_id=meta.thread_id,
            turn_id=meta.turn_id,
        )
    except Exception as exc:
        error(f"failed to save raw payload: {exc}")
        return 1

    base_dir = saved_path.parent.parent
    try:
        summary.rebuild_summary(base_dir)
    except Exception as exc:
        error(f"failed to rebuild summary: {exc}")
        return 1

    if args.telegram:
        try:
            telegram.send_last_message_best_effort(
                args.payload_json,
                base_cwd=base_dir.parent,
                base_dir=base_dir,
                event_stem=saved_path.stem,
            )
        except Exception as exc:
            warn(f"telegram delivery failed: {exc.__class__.__name__}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
