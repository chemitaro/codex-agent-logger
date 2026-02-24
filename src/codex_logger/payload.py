from __future__ import annotations

from dataclasses import dataclass
import json

from codex_logger.console import warn


@dataclass(frozen=True)
class PayloadMeta:
    cwd: str | None
    thread_id: str | None
    turn_id: str | None


def parse_json_object_best_effort(raw_payload: str) -> dict[str, object] | None:
    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError:
        warn("payload is not valid JSON; fallback metadata will be used")
        return None

    if not isinstance(payload, dict):
        warn("payload JSON is not an object; fallback metadata will be used")
        return None

    return payload


def parse_best_effort(raw_payload: str) -> PayloadMeta:
    payload = parse_json_object_best_effort(raw_payload)
    if payload is None:
        return PayloadMeta(cwd=None, thread_id=None, turn_id=None)

    cwd = _payload_string_field(payload, "cwd")
    thread_id = _payload_string_field(payload, "thread-id")
    turn_id = _payload_string_field(payload, "turn-id")
    return PayloadMeta(cwd=cwd, thread_id=thread_id, turn_id=turn_id)


def _payload_string_field(payload: dict[str, object], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        warn(f"payload field missing: {key}")
        return None
    if not isinstance(value, str):
        warn(f"payload field is not a string: {key}")
        return None
    if value == "":
        warn(f"payload field is empty: {key}")
        return None
    return value
