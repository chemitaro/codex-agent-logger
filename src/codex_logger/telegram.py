from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import urllib.error
import urllib.request

from codex_logger.atomic import write_text_atomic
from codex_logger import chunking, env, telegram_topics
from codex_logger.console import warn
from codex_logger.payload import parse_json_object_best_effort


@dataclass(frozen=True)
class TelegramConfig:
    bot_token: str
    chat_id: str


class TelegramError(RuntimeError):
    pass


def send_last_message_best_effort(
    raw_payload: str, *, base_cwd: Path, base_dir: Path, event_stem: str
) -> None:
    try:
        _send_last_message_best_effort(raw_payload, base_cwd=base_cwd, base_dir=base_dir, event_stem=event_stem)
    except Exception as exc:
        warn(f"telegram delivery failed: unexpected error: {exc.__class__.__name__}")
        _write_telegram_diagnostics_best_effort(
            base_dir=base_dir,
            event_stem=event_stem,
            outcome="failed",
            reason=f"unexpected error: {exc.__class__.__name__}",
            context={},
            hints=["エラーの内容を確認し、再実行してください。"],
        )


def _send_last_message_best_effort(
    raw_payload: str, *, base_cwd: Path, base_dir: Path, event_stem: str
) -> None:
    payload = parse_json_object_best_effort(raw_payload)
    if payload is None:
        warn("telegram delivery skipped: payload is not valid JSON")
        _write_telegram_diagnostics_best_effort(
            base_dir=base_dir,
            event_stem=event_stem,
            outcome="skipped",
            reason="payload is not valid JSON",
            context={},
            hints=["Codex CLI notify の payload が JSON 文字列として渡されているか確認してください。"],
        )
        return

    thread_id = _required_str(payload, "thread-id", "thread_id")
    turn_id = _optional_str(payload, "turn-id", "turn_id")
    last_message = _required_str(payload, "last-assistant-message", "last_assistant_message")
    if thread_id is None or last_message is None:
        warn("telegram delivery skipped: required payload fields are missing")
        _write_telegram_diagnostics_best_effort(
            base_dir=base_dir,
            event_stem=event_stem,
            outcome="skipped",
            reason="required payload fields are missing",
            context={
                "thread-id": thread_id,
                "turn-id": turn_id,
            },
            hints=["payload に thread-id と last-assistant-message が含まれているか確認してください。"],
        )
        return

    payload_cwd = _optional_str(payload, "cwd")
    resolved_cwd = (
        Path(payload_cwd).resolve(strict=False) if payload_cwd is not None else base_cwd
    )

    config = load_telegram_config(resolved_cwd)
    if config is None:
        warn("telegram delivery skipped: TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID not set")

        values = env.load_env_from_dotenv(resolved_cwd)
        bot_token = os.environ.get("TELEGRAM_BOT_TOKEN") or values.get("TELEGRAM_BOT_TOKEN")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID") or values.get("TELEGRAM_CHAT_ID")
        missing: list[str] = []
        if not bot_token:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not chat_id:
            missing.append("TELEGRAM_CHAT_ID")

        _write_telegram_diagnostics_best_effort(
            base_dir=base_dir,
            event_stem=event_stem,
            outcome="skipped",
            reason=f"env missing ({', '.join(missing)})" if missing else "env missing",
            context={
                "cwd": str(resolved_cwd),
                "thread-id": thread_id,
                "turn-id": turn_id,
            },
            hints=[
                "環境変数または <cwd>/.env に TELEGRAM_BOT_TOKEN と TELEGRAM_CHAT_ID を設定してください。",
                "supergroup で topics（フォーラム）を有効化し、Bot に topic 作成権限があるか確認してください。",
            ],
        )
        return

    try:
        topic_id = ensure_topic(
            config=config, thread_id=thread_id, cwd=resolved_cwd, base_dir=base_dir
        )
    except TelegramError as exc:
        warn(f"telegram delivery failed: {exc}")
        _write_telegram_diagnostics_best_effort(
            base_dir=base_dir,
            event_stem=event_stem,
            outcome="failed",
            reason=str(exc),
            context={
                "cwd": str(resolved_cwd),
                "thread-id": thread_id,
                "turn-id": turn_id,
            },
            hints=[
                "supergroup で topics（フォーラム）を有効化しているか確認してください。",
                "Bot に topic 作成権限があるか確認してください。",
            ],
        )
        return

    chunks = chunking.split_for_telegram(last_message, limit=4096)
    for idx, chunk in enumerate(chunks, start=1):
        try:
            send_message(config, message_thread_id=topic_id, text=chunk)
        except TelegramError as exc:
            warn(f"telegram delivery failed: {exc}")
            _write_telegram_diagnostics_best_effort(
                base_dir=base_dir,
                event_stem=event_stem,
                outcome="failed",
                reason=str(exc),
                context={
                    "cwd": str(resolved_cwd),
                    "thread-id": thread_id,
                    "turn-id": turn_id,
                    "chunk": f"{idx}/{len(chunks)}",
                },
                hints=[
                    "network / rate limit / 権限 / chat_id を確認してください。",
                    "出力が長い場合、分割送信中に失敗している可能性があります。",
                ],
            )
            return


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


def _required_str(payload: dict[str, object], key: str, *alt_keys: str) -> str | None:
    for candidate in (key, *alt_keys):
        value = payload.get(candidate)
        if isinstance(value, str) and value != "":
            return value
    return None


def _optional_str(payload: dict[str, object], key: str, *alt_keys: str) -> str | None:
    for candidate in (key, *alt_keys):
        value = payload.get(candidate)
        if isinstance(value, str) and value != "":
            return value
    return None


def _write_telegram_diagnostics_best_effort(
    *,
    base_dir: Path,
    event_stem: str,
    outcome: str,
    reason: str,
    context: dict[str, str | None],
    hints: list[str],
) -> None:
    path = base_dir / "telegram-errors" / f"{event_stem}.md"
    lines: list[str] = []
    lines.append("# Telegram delivery diagnostics")
    lines.append("")
    lines.append(f"- outcome: {outcome}")
    lines.append(f"- reason: {reason}")
    lines.append(f"- event: {event_stem}")

    cwd = context.get("cwd")
    if cwd:
        lines.append(f"- cwd: {cwd}")

    thread_id = context.get("thread-id")
    if thread_id:
        lines.append(f"- thread-id: {thread_id}")

    turn_id = context.get("turn-id")
    if turn_id:
        lines.append(f"- turn-id: {turn_id}")

    chunk = context.get("chunk")
    if chunk:
        lines.append(f"- chunk: {chunk}")

    if hints:
        lines.append("")
        lines.append("## Hints")
        for hint in hints:
            lines.append(f"- {hint}")

    content = "\n".join(lines) + "\n"

    try:
        write_text_atomic(path, content)
    except (OSError, UnicodeError) as exc:
        warn(f"failed to write telegram diagnostics {path}: {exc}")
