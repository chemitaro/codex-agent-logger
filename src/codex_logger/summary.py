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
    cwd: str | None
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
        lines.append(f"- cwd: {_display_field(entry.cwd)}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


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
            cwd=None,
            parse_error=str(exc),
        )

    return SummaryEntry(
        filename=log_path.name,
        type_value=_string_or_none(payload, "type"),
        thread_id=_string_or_none(payload, "thread-id"),
        turn_id=_string_or_none(payload, "turn-id"),
        cwd=_string_or_none(payload, "cwd"),
    )


def _string_or_none(payload: dict[str, object], key: str) -> str | None:
    value = payload.get(key)
    if isinstance(value, str):
        return value
    return None


def _display_field(value: str | None) -> str:
    return value if value is not None else "<missing>"

