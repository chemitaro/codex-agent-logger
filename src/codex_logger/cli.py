from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import TextIO

from codex_logger import __version__
from codex_logger import internal_turn_filter, log_store, notification_event, payload, summary, telegram
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


def build_notify_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codex-logger notify")
    parser.add_argument("--telegram", action="store_true", help="Enable Telegram delivery.")
    parser.add_argument("payload_json", help="Codex notify payload JSON.")
    return parser


def build_permission_request_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codex-logger permission-request")
    parser.add_argument("--telegram", action="store_true", help="Enable Telegram delivery.")
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    if argv is None:
        argv = sys.argv[1:]

    command = _first_non_option(argv)
    if command == "notify":
        command_index = argv.index("notify")
        args = build_notify_parser().parse_args(argv[command_index + 1 :])
        args.command = "notify"
        return args

    if command == "permission-request":
        command_index = argv.index("permission-request")
        args = build_permission_request_parser().parse_args(argv[command_index + 1 :])
        args.command = "permission-request"
        args.payload_json = None
        return args

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.payload_json is None:
        parser.error("the following arguments are required: payload_json")

    args.command = "legacy"
    return args


def main(argv: list[str] | None = None, *, stdin: TextIO | None = None) -> int:
    args = parse_args(argv)
    raw_payload = args.payload_json
    if args.command == "permission-request":
        raw_payload = notification_event.from_permission_request(
            (stdin or sys.stdin).read(),
            fallback_cwd=Path.cwd().resolve(strict=False),
        ).to_notify_payload_json()

    filter_internal_turns = args.command in {"legacy", "notify"}
    return _handle_payload(
        raw_payload,
        telegram_enabled=args.telegram,
        filter_internal_turns=filter_internal_turns,
    )


def _handle_payload(raw_payload: str, *, telegram_enabled: bool, filter_internal_turns: bool) -> int:
    meta = payload.parse_best_effort(raw_payload)

    try:
        saved_path = log_store.save_raw_payload(
            raw_payload,
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

    if telegram_enabled:
        if filter_internal_turns:
            parsed_payload = payload.parse_json_object_best_effort(raw_payload)
            if parsed_payload is not None:
                decision = internal_turn_filter.should_skip_telegram(parsed_payload)
                if decision.skip:
                    warn(f"telegram delivery skipped: internal turn ({decision.rule_name})")
                    telegram.write_delivery_diagnostics_best_effort(
                        base_dir=base_dir,
                        event_stem=saved_path.stem,
                        outcome="skipped",
                        reason=decision.reason or "internal Codex helper turn",
                        context={
                            "thread-id": meta.thread_id,
                            "turn-id": meta.turn_id,
                            "rule": decision.rule_name,
                            "assistant-json-keys": ",".join(sorted(decision.assistant_json_keys)),
                        },
                        hints=[
                            "Codex Desktop の内部 helper turn と判定されたため Telegram 送信を抑止しました。",
                            "raw payload は .codex-log/logs/ に保存されています。",
                        ],
                    )
                    return 0
        try:
            telegram.send_last_message_best_effort(
                raw_payload,
                base_cwd=base_dir.parent,
                base_dir=base_dir,
                event_stem=saved_path.stem,
            )
        except Exception as exc:
            warn(f"telegram delivery failed: {exc.__class__.__name__}")

    return 0


def _first_non_option(argv: list[str]) -> str | None:
    for arg in argv:
        if arg == "--":
            return None
        if not arg.startswith("-"):
            return arg
    return None


if __name__ == "__main__":
    raise SystemExit(main())
