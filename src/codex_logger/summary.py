from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from codex_logger.atomic import write_text_atomic
from codex_logger.locks import file_lock


@dataclass(frozen=True)
class SummaryEntry:
    filename: str
    type_value: str | None
    thread_id: str | None
    turn_id: str | None
    input_messages: list[str] | None
    input_messages_state: str
    last_assistant_message: str | None
    last_assistant_message_state: str
    parse_error: str | None = None


def rebuild_summary(base_dir: Path) -> Path:
    logs_dir = base_dir / "logs"
    summary_path = base_dir / "summary.md"
    lock_path = base_dir / "summary.lock"

    with file_lock(lock_path):
        log_paths = (
            sorted(logs_dir.glob("*.json"), key=lambda item: item.name)
            if logs_dir.is_dir()
            else []
        )
        entries = [_load_summary_entry(log_path) for log_path in log_paths]
        write_text_atomic(summary_path, render_summary(entries))

    return summary_path


def render_summary(entries: list[SummaryEntry]) -> str:
    lines = ["# Codex Logger Summary", ""]

    for entry in entries:
        lines.append(f"## {entry.filename}")
        if entry.parse_error is not None:
            lines.append(f"- parse error: {entry.parse_error}")
            lines.append("")
            continue

        lines.append(f"- type: {_display_field(entry.type_value)}")
        lines.append(f"- thread-id: {_display_field(entry.thread_id)}")
        lines.append(f"- turn-id: {_display_field(entry.turn_id)}")
        lines.append("")

        _append_user_messages(lines, entry)
        _append_assistant_message(lines, entry)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _append_user_messages(lines: list[str], entry: SummaryEntry) -> None:
    if entry.input_messages_state == "invalid":
        lines.append("### User")
        lines.extend(_blockquote_lines("<invalid>"))
        lines.append("")
        return

    if entry.input_messages_state == "missing" or not entry.input_messages:
        lines.append("### User")
        lines.extend(_blockquote_lines("<missing>"))
        lines.append("")
        return

    total = len(entry.input_messages)
    for index, message in enumerate(entry.input_messages, start=1):
        lines.append(f"### User ({index}/{total})")
        lines.extend(_blockquote_lines(_display_message(message)))
        lines.append("")


def _append_assistant_message(lines: list[str], entry: SummaryEntry) -> None:
    if entry.last_assistant_message_state == "invalid":
        message = "<invalid>"
    elif entry.last_assistant_message_state == "missing":
        message = "<missing>"
    else:
        message = _display_message(entry.last_assistant_message or "")

    lines.append("### Assistant")
    lines.extend(_blockquote_lines(message))


def _blockquote_lines(text: str) -> list[str]:
    return [f"> {line}" for line in text.split("\n")]


def _display_message(message: str) -> str:
    return message if message != "" else "<missing>"


def _load_summary_entry(log_path: Path) -> SummaryEntry:
    try:
        payload = json.loads(log_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise TypeError("payload JSON is not an object")
    except Exception as exc:
        return SummaryEntry(
            filename=log_path.name,
            type_value=None,
            thread_id=None,
            turn_id=None,
            input_messages=None,
            input_messages_state="missing",
            last_assistant_message=None,
            last_assistant_message_state="missing",
            parse_error=str(exc),
        )

    input_messages, input_messages_state = _extract_input_messages(payload)
    last_assistant_message, last_assistant_message_state = _extract_last_assistant_message(
        payload
    )

    return SummaryEntry(
        filename=log_path.name,
        type_value=_string_or_none(payload, "type"),
        thread_id=_string_or_none(payload, "thread-id"),
        turn_id=_string_or_none(payload, "turn-id"),
        input_messages=input_messages,
        input_messages_state=input_messages_state,
        last_assistant_message=last_assistant_message,
        last_assistant_message_state=last_assistant_message_state,
    )


def _string_or_none(payload: dict[str, object], key: str) -> str | None:
    value = payload.get(key)
    if isinstance(value, str):
        return value
    return None


def _extract_input_messages(payload: dict[str, object]) -> tuple[list[str] | None, str]:
    if "input-messages" not in payload:
        return None, "missing"

    value = payload.get("input-messages")
    if not isinstance(value, list):
        return None, "invalid"
    if not value:
        return None, "missing"

    messages: list[str] = []
    for item in value:
        if not isinstance(item, str):
            return None, "invalid"
        messages.append(item)

    return messages, "present"


def _extract_last_assistant_message(payload: dict[str, object]) -> tuple[str | None, str]:
    if "last-assistant-message" not in payload:
        return None, "missing"

    value = payload.get("last-assistant-message")
    if not isinstance(value, str):
        return None, "invalid"
    if value == "":
        return None, "missing"

    return value, "present"


def _display_field(value: str | None) -> str:
    return value if value is not None else "<missing>"

