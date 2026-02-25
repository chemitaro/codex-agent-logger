from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from codex_logger.atomic import write_text_atomic
from codex_logger.locks import file_lock


@dataclass(frozen=True)
class SummaryEntry:
    timestamp: str
    thread_id: str | None
    user_message: str | None
    user_message_state: str
    assistant_message: str | None
    assistant_message_state: str
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
        lines.append(f"<sub>{entry.timestamp}</sub>")
        if entry.parse_error is not None:
            lines.append(f"- parse error: {entry.parse_error}")
            lines.append("")
            continue

        _append_user_messages(lines, entry)
        _append_assistant_message(lines, entry)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _append_user_messages(lines: list[str], entry: SummaryEntry) -> None:
    if entry.user_message_state == "invalid":
        message = "<invalid>"
    elif entry.user_message_state == "missing":
        message = "<missing>"
    else:
        message = _display_message(entry.user_message or "")

    lines.append("**User**")
    lines.extend(_blockquote_lines(message))
    lines.append("")


def _append_assistant_message(lines: list[str], entry: SummaryEntry) -> None:
    if entry.assistant_message_state == "invalid":
        message = "<invalid>"
    elif entry.assistant_message_state == "missing":
        message = "<missing>"
    else:
        message = _display_message(entry.assistant_message or "")

    if entry.thread_id is None:
        label = "**Assistant**"
    else:
        label = f"**Assistant ({entry.thread_id})**"

    lines.append(label)
    lines.extend(_blockquote_lines(message))


def _blockquote_lines(text: str) -> list[str]:
    return [f"> {line}" for line in text.split("\n")]


def _display_message(message: str) -> str:
    return message if message != "" else "<missing>"


def _format_timestamp(raw: str) -> str:
    if "T" not in raw:
        return raw

    date_part, time_part = raw.split("T", 1)
    if not time_part.endswith("Z"):
        return raw

    clock = time_part[:-1]
    parts = clock.split("-")
    if len(parts) != 3:
        return raw

    hour, minute, second = parts
    return f"{date_part} {hour}:{minute}:{second}Z"


def _load_summary_entry(log_path: Path) -> SummaryEntry:
    raw_timestamp = log_path.stem.split("_", 1)[0]
    timestamp = _format_timestamp(raw_timestamp)

    try:
        payload = json.loads(log_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise TypeError("payload JSON is not an object")
    except Exception as exc:
        return SummaryEntry(
            timestamp=timestamp,
            thread_id=None,
            user_message=None,
            user_message_state="missing",
            assistant_message=None,
            assistant_message_state="missing",
            parse_error=str(exc),
        )

    user_message, user_message_state = _extract_input_messages(payload)
    assistant_message, assistant_message_state = _extract_last_assistant_message(payload)

    return SummaryEntry(
        timestamp=timestamp,
        thread_id=_string_or_none(payload, "thread-id"),
        user_message=user_message,
        user_message_state=user_message_state,
        assistant_message=assistant_message,
        assistant_message_state=assistant_message_state,
    )


def _string_or_none(payload: dict[str, object], key: str) -> str | None:
    value = payload.get(key)
    if isinstance(value, str) and value != "":
        return value
    return None


def _extract_input_messages(payload: dict[str, object]) -> tuple[str | None, str]:
    if "input-messages" not in payload:
        return None, "missing"

    value = payload.get("input-messages")
    if not isinstance(value, list):
        return None, "invalid"
    if not value:
        return None, "missing"

    for item in value:
        if not isinstance(item, str):
            return None, "invalid"

    last_message = value[-1]
    if last_message == "":
        return None, "missing"

    return last_message, "present"


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

