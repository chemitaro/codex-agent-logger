from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class NotificationEvent:
    event_type: str
    thread_id: str | None
    turn_id: str | None
    cwd: str | None
    message: str | None

    def to_notify_payload_json(self) -> str:
        payload: dict[str, object] = {"type": self.event_type}
        if self.thread_id:
            payload["thread-id"] = self.thread_id
        if self.turn_id:
            payload["turn-id"] = self.turn_id
        if self.cwd:
            payload["cwd"] = self.cwd
        if self.message:
            payload["last-assistant-message"] = self.message
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def from_permission_request(raw_payload: str, *, fallback_cwd: Path | None = None) -> NotificationEvent:
    payload = _json_object(raw_payload)
    session_id = _string_field(payload, "session_id", "session-id", "thread-id", "thread_id")
    turn_id = _string_field(payload, "turn_id", "turn-id")
    cwd = _string_field(payload, "cwd")
    if cwd is None and fallback_cwd is not None:
        cwd = str(fallback_cwd)

    return NotificationEvent(
        event_type="permission-request",
        thread_id=session_id,
        turn_id=turn_id,
        cwd=cwd,
        message=_permission_request_message(payload),
    )


def _permission_request_message(payload: dict[str, object]) -> str:
    tool_name = _string_field(payload, "tool_name", "tool-name") or "<unknown tool>"
    tool_input = payload.get("tool_input") or payload.get("tool-input")
    description = _string_field(payload, "description") or _nested_string_field(
        tool_input, "description"
    )
    command = _nested_string_field(tool_input, "command")
    justification = _nested_string_field(tool_input, "justification")

    lines = ["Codex approval required", "", f"Tool: {tool_name}"]
    if description:
        lines.extend(["", "Description:", description])
    if command:
        lines.extend(["", "Command:", command])
    if justification:
        lines.extend(["", "Justification:", justification])

    return "\n".join(lines)


def _json_object(raw_payload: str) -> dict[str, object]:
    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _string_field(payload: dict[str, object], *keys: str) -> str | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value != "":
            return value
    return None


def _nested_string_field(value: Any, key: str) -> str | None:
    if not isinstance(value, dict):
        return None
    field = value.get(key)
    if isinstance(field, str) and field != "":
        return field
    return None
