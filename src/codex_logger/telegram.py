from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import urllib.error
import urllib.request

from codex_logger import chunking, env, telegram_topics
from codex_logger.console import warn
from codex_logger.payload import parse_json_object_best_effort


@dataclass(frozen=True)
class TelegramConfig:
    bot_token: str
    chat_id: str


class TelegramError(RuntimeError):
    pass


def send_last_message_best_effort(raw_payload: str, *, base_cwd: Path, base_dir: Path) -> None:
    payload = parse_json_object_best_effort(raw_payload)
    if payload is None:
        warn("telegram delivery skipped: payload is not valid JSON")
        return

    thread_id = _required_str(payload, "thread-id")
    last_message = _required_str(payload, "last-assistant-message")
    if thread_id is None or last_message is None:
        warn("telegram delivery skipped: required payload fields are missing")
        return

    payload_cwd = _optional_str(payload, "cwd")
    resolved_cwd = (
        Path(payload_cwd).resolve(strict=False) if payload_cwd is not None else base_cwd
    )

    config = load_telegram_config(resolved_cwd)
    if config is None:
        warn("telegram delivery skipped: TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID not set")
        return

    try:
        topic_id = ensure_topic(
            config=config, thread_id=thread_id, cwd=resolved_cwd, base_dir=base_dir
        )
        for chunk in chunking.split_for_telegram(last_message, limit=4096):
            send_message(config, message_thread_id=topic_id, text=chunk)
    except TelegramError as exc:
        warn(f"telegram delivery failed: {exc}")


def load_telegram_config(cwd: Path) -> TelegramConfig | None:
    values = env.load_env_from_dotenv(cwd)

    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN") or values.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID") or values.get("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        return None

    return TelegramConfig(bot_token=bot_token, chat_id=chat_id)


def ensure_topic(*, config: TelegramConfig, thread_id: str, cwd: Path, base_dir: Path) -> int:
    name = topic_name(cwd, thread_id)

    def _create() -> int:
        return create_forum_topic(config, name=name)

    return telegram_topics.ensure_topic_id(base_dir, thread_id, _create)


def topic_name(cwd: Path, thread_id: str) -> str:
    prefix = cwd.name or str(cwd)
    full = f"{prefix} ({thread_id})"
    if len(full.encode("utf-8")) <= 128:
        return full

    short = hashlib.sha256(thread_id.encode("utf-8")).hexdigest()[:8]
    suffix = f" ({short})"
    candidate = f"{prefix}{suffix}"
    if len(candidate.encode("utf-8")) <= 128:
        return candidate

    max_prefix_bytes = 128 - len(suffix.encode("utf-8"))
    truncated = _truncate_utf8(prefix, max_prefix_bytes)
    return f"{truncated}{suffix}"


def _truncate_utf8(text: str, max_bytes: int) -> str:
    if max_bytes <= 0:
        return ""
    out: list[str] = []
    used = 0
    for ch in text:
        b = ch.encode("utf-8")
        if used + len(b) > max_bytes:
            break
        out.append(ch)
        used += len(b)
    return "".join(out)


def create_forum_topic(config: TelegramConfig, *, name: str) -> int:
    data = _call_api(
        config.bot_token,
        method="createForumTopic",
        payload={"chat_id": config.chat_id, "name": name},
    )
    result = data.get("result")
    if not isinstance(result, dict):
        raise TelegramError("createForumTopic: invalid result")
    message_thread_id = result.get("message_thread_id")
    if not isinstance(message_thread_id, int):
        raise TelegramError("createForumTopic: missing message_thread_id")
    return message_thread_id


def send_message(config: TelegramConfig, *, message_thread_id: int, text: str) -> None:
    _call_api(
        config.bot_token,
        method="sendMessage",
        payload={
            "chat_id": config.chat_id,
            "message_thread_id": message_thread_id,
            "text": text,
        },
    )


def _call_api(bot_token: str, *, method: str, payload: dict[str, object]) -> dict[str, object]:
    url = f"https://api.telegram.org/bot{bot_token}/{method}"
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8", "replace")
        except Exception:
            detail = ""
        raise TelegramError(f"HTTP {exc.code} calling {method}: {detail[:200]}") from None
    except urllib.error.URLError as exc:
        raise TelegramError(f"network error calling {method}: {exc.reason}") from None
    except Exception as exc:
        raise TelegramError(f"unexpected error calling {method}: {exc.__class__.__name__}") from None

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise TelegramError(f"invalid JSON response from {method}") from None

    if not isinstance(data, dict):
        raise TelegramError(f"invalid response type from {method}") from None

    if data.get("ok") is not True:
        desc = data.get("description")
        if isinstance(desc, str) and desc:
            raise TelegramError(f"{method} failed: {desc}") from None
        raise TelegramError(f"{method} failed") from None

    return data


def _required_str(payload: dict[str, object], key: str) -> str | None:
    value = payload.get(key)
    if isinstance(value, str) and value != "":
        return value
    return None


def _optional_str(payload: dict[str, object], key: str) -> str | None:
    value = payload.get(key)
    if isinstance(value, str) and value != "":
        return value
    return None
