from __future__ import annotations

from collections.abc import Callable
import json
from pathlib import Path

from codex_logger.atomic import write_text_atomic
from codex_logger.console import warn
from codex_logger.locks import file_lock


def ensure_topic_id(
    base_dir: Path, thread_id: str, create_topic: Callable[[], int]
) -> int:
    lock_path = base_dir / "telegram-topics.lock"
    mapping_path = base_dir / "telegram-topics.json"

    with file_lock(lock_path):
        mapping = _load_mapping(mapping_path)
        existing = mapping.get(thread_id)
        if isinstance(existing, int):
            return existing

        message_thread_id = create_topic()
        mapping[thread_id] = message_thread_id
        write_text_atomic(
            mapping_path,
            json.dumps(mapping, ensure_ascii=False, indent=2) + "\n",
        )
        return message_thread_id


def _load_mapping(path: Path) -> dict[str, int]:
    if not path.is_file():
        return {}

    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except Exception as exc:
        warn(f"failed to read telegram topic mapping; starting empty: {exc}")
        return {}

    if not isinstance(data, dict):
        warn("telegram topic mapping is not an object; starting empty")
        return {}

    mapping: dict[str, int] = {}
    for key, value in data.items():
        if isinstance(key, str) and isinstance(value, int):
            mapping[key] = value

    return mapping

