from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Pattern


@dataclass(frozen=True)
class InternalTurnRule:
    name: str
    input_patterns: tuple[Pattern[str], ...]
    assistant_json_keys: frozenset[str]
    assistant_patterns: tuple[Pattern[str], ...] = ()


@dataclass(frozen=True)
class SkipDecision:
    skip: bool
    rule_name: str | None = None
    reason: str | None = None
    assistant_json_keys: frozenset[str] = frozenset()


INTERNAL_TURN_RULES: tuple[InternalTurnRule, ...] = (
    InternalTurnRule(
        name="desktop-title-generation",
        input_patterns=(
            re.compile(r"Generate a concise UI title", re.IGNORECASE),
            re.compile(r"structured title field", re.IGNORECASE),
        ),
        assistant_json_keys=frozenset({"title"}),
    ),
    InternalTurnRule(
        name="commit-message-generation",
        input_patterns=(
            re.compile(r"single-line git commit message", re.IGNORECASE),
            re.compile(r"structured response field message", re.IGNORECASE),
        ),
        assistant_json_keys=frozenset({"message"}),
    ),
    InternalTurnRule(
        name="suggestions-generation",
        input_patterns=(
            re.compile(r"Generate 0 to 3 hyperpersonalized suggestions", re.IGNORECASE),
            re.compile(r"Return 0 to 3 fresh suggestions", re.IGNORECASE),
        ),
        assistant_json_keys=frozenset({"suggestions"}),
    ),
    InternalTurnRule(
        name="suggestions-exclude-generation",
        input_patterns=(
            re.compile(r"Avoid repeating these previously dismissed suggestions", re.IGNORECASE),
            re.compile(r"dismissed suggestions", re.IGNORECASE),
        ),
        assistant_json_keys=frozenset({"exclude"}),
    ),
    InternalTurnRule(
        name="approval-outcome-generation",
        input_patterns=(
            re.compile(r"approval request", re.IGNORECASE),
            re.compile(r"approv(?:e|al).*request", re.IGNORECASE),
            re.compile(r"outcome field", re.IGNORECASE),
        ),
        assistant_json_keys=frozenset({"outcome"}),
    ),
    InternalTurnRule(
        name="approval-outcome-generation",
        input_patterns=(
            re.compile(r"approval request", re.IGNORECASE),
            re.compile(r"approv(?:e|al).*request", re.IGNORECASE),
            re.compile(r"outcome field", re.IGNORECASE),
        ),
        assistant_json_keys=frozenset(
            {"risk_level", "user_authorization", "outcome", "rationale"}
        ),
    ),
)


def should_skip_telegram(payload: dict[str, object]) -> SkipDecision:
    input_messages = _input_messages(payload)
    assistant_message = _string_field(payload, "last-assistant-message", "last_assistant_message")
    if not input_messages or assistant_message is None:
        return SkipDecision(skip=False)

    assistant_json = _json_object(assistant_message)
    if assistant_json is None:
        return SkipDecision(skip=False)

    assistant_keys = frozenset(assistant_json.keys())
    for rule in INTERNAL_TURN_RULES:
        if assistant_keys != rule.assistant_json_keys:
            continue
        if not _matches_any(input_messages, rule.input_patterns):
            continue
        if rule.assistant_patterns and not _matches_any([assistant_message], rule.assistant_patterns):
            continue
        return SkipDecision(
            skip=True,
            rule_name=rule.name,
            reason="internal Codex helper turn",
            assistant_json_keys=assistant_keys,
        )

    return SkipDecision(skip=False)


def _input_messages(payload: dict[str, object]) -> list[str]:
    value = payload.get("input-messages") or payload.get("input_messages")
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _string_field(payload: dict[str, object], *keys: str) -> str | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value != "":
            return value
    return None


def _json_object(raw_value: str) -> dict[str, object] | None:
    try:
        value = json.loads(raw_value)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def _matches_any(values: list[str], patterns: tuple[Pattern[str], ...]) -> bool:
    return any(pattern.search(value) for value in values for pattern in patterns)
