import json
import threading
import time
from pathlib import Path

import pytest

from codex_logger.locks import file_lock
from codex_logger.summary import rebuild_summary


def test_rebuild_summary_from_logs(tmp_path: Path) -> None:
    base_dir = tmp_path / ".codex-log"
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(parents=True)

    first_log = logs_dir / "2026-02-24T09-53-12.001Z_ev-a.json"
    second_log = logs_dir / "2026-02-24T09-53-12.002Z_ev-b.json"

    first_log.write_text(
        json.dumps(
            {
                "type": "agent-turn-complete",
                "thread-id": "thread-1",
                "turn-id": "turn-1",
                "input-messages": ["Hello", "Show me code"],
                "last-assistant-message": "Here is **code**",
            }
        ),
        encoding="utf-8",
    )
    second_log.write_text(
        json.dumps(
            {
                "type": "agent-turn-complete",
                "input-messages": ["Need thread id"],
                "last-assistant-message": "Working on it",
            }
        ),
        encoding="utf-8",
    )

    summary_path = rebuild_summary(base_dir)

    content = summary_path.read_text(encoding="utf-8")
    assert content.startswith("# Codex Logger Summary\n")
    assert content.index(f"## {first_log.name}") < content.index(f"## {second_log.name}")
    assert "- type: agent-turn-complete" in content
    assert "- thread-id: thread-1" in content
    assert "- turn-id: turn-1" in content
    assert "- cwd:" not in content
    assert "### User (1/2)" in content
    assert "### User (2/2)" in content
    assert "### Assistant" in content
    assert "> Hello" in content
    assert "> Show me code" in content
    assert "> Here is **code**" in content
    assert "- thread-id: <missing>" in content
    assert "- turn-id: <missing>" in content


def test_multiline_messages_are_blockquoted(tmp_path: Path) -> None:
    base_dir = tmp_path / ".codex-log"
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(parents=True)

    log_path = logs_dir / "2026-02-24T09-53-12.001Z_ev-multiline.json"
    log_path.write_text(
        json.dumps(
            {
                "type": "agent-turn-complete",
                "thread-id": "thread-ml",
                "turn-id": "turn-ml",
                "input-messages": ["line-1\nline-2"],
                "last-assistant-message": "answer-1\n\nanswer-3",
            }
        ),
        encoding="utf-8",
    )

    summary_path = rebuild_summary(base_dir)
    content = summary_path.read_text(encoding="utf-8")

    assert f"## {log_path.name}" in content
    assert "### User (1/1)" in content
    assert "> line-1\n> line-2" in content
    assert "### Assistant" in content
    assert "> answer-1\n> \n> answer-3" in content


def test_missing_or_invalid_messages_are_rendered_best_effort(tmp_path: Path) -> None:
    base_dir = tmp_path / ".codex-log"
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(parents=True)

    missing_log = logs_dir / "2026-02-24T09-53-12.001Z_ev-missing.json"
    empty_log = logs_dir / "2026-02-24T09-53-12.002Z_ev-empty.json"
    invalid_log = logs_dir / "2026-02-24T09-53-12.003Z_ev-invalid.json"
    empty_element_log = logs_dir / "2026-02-24T09-53-12.004Z_ev-empty-element.json"

    missing_log.write_text(
        json.dumps(
            {
                "type": "agent-turn-complete",
                "thread-id": "thread-missing",
                "turn-id": "turn-missing",
            }
        ),
        encoding="utf-8",
    )
    empty_log.write_text(
        json.dumps(
            {
                "type": "agent-turn-complete",
                "input-messages": [],
                "last-assistant-message": "",
            }
        ),
        encoding="utf-8",
    )
    invalid_log.write_text(
        json.dumps(
            {
                "type": "agent-turn-complete",
                "input-messages": "not-a-list",
                "last-assistant-message": ["not-a-string"],
            }
        ),
        encoding="utf-8",
    )
    empty_element_log.write_text(
        json.dumps(
            {
                "type": "agent-turn-complete",
                "input-messages": ["", "next"],
                "last-assistant-message": "ok",
            }
        ),
        encoding="utf-8",
    )

    summary_path = rebuild_summary(base_dir)
    content = summary_path.read_text(encoding="utf-8")

    def _section(log_name: str) -> str:
        marker = f"## {log_name}\n"
        start = content.index(marker) + len(marker)
        end = content.find("\n## ", start)
        return content[start:] if end == -1 else content[start:end]

    missing_section = _section(missing_log.name)
    assert "### User\n> <missing>" in missing_section
    assert "### Assistant\n> <missing>" in missing_section

    empty_section = _section(empty_log.name)
    assert "### User\n> <missing>" in empty_section
    assert "### Assistant\n> <missing>" in empty_section

    invalid_section = _section(invalid_log.name)
    assert "### User\n> <invalid>" in invalid_section
    assert "### Assistant\n> <invalid>" in invalid_section

    empty_element_section = _section(empty_element_log.name)
    assert "### User (1/2)\n> <missing>" in empty_element_section
    assert "### User (2/2)\n> next" in empty_element_section
    assert "### Assistant\n> ok" in empty_element_section


def test_invalid_json_is_recorded(tmp_path: Path) -> None:
    base_dir = tmp_path / ".codex-log"
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(parents=True)

    valid_log = logs_dir / "2026-02-24T09-53-12.001Z_ev-valid.json"
    invalid_log = logs_dir / "2026-02-24T09-53-12.002Z_ev-invalid.json"

    valid_log.write_text(
        json.dumps(
            {
                "type": "agent-turn-complete",
                "thread-id": "thread-2",
                "turn-id": "turn-2",
                "cwd": "/tmp/ok",
            }
        ),
        encoding="utf-8",
    )
    invalid_log.write_text('{"type": "agent-turn-complete"', encoding="utf-8")

    summary_path = rebuild_summary(base_dir)
    content = summary_path.read_text(encoding="utf-8")

    assert f"## {valid_log.name}" in content
    assert f"## {invalid_log.name}" in content
    assert "- parse error:" in content


def test_atomic_replace_keeps_old_on_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    base_dir = tmp_path / ".codex-log"
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(parents=True)

    (logs_dir / "2026-02-24T09-53-12.001Z_ev-a.json").write_text(
        json.dumps(
            {
                "type": "agent-turn-complete",
                "thread-id": "thread-1",
                "turn-id": "turn-1",
                "cwd": "/tmp/work",
            }
        ),
        encoding="utf-8",
    )

    summary_path = base_dir / "summary.md"
    summary_path.write_text("old summary\n", encoding="utf-8")

    def _raise_replace_error(*_args: object, **_kwargs: object) -> None:
        raise OSError("replace failed")

    monkeypatch.setattr("codex_logger.atomic.os.replace", _raise_replace_error)

    with pytest.raises(OSError):
        rebuild_summary(base_dir)

    assert summary_path.read_text(encoding="utf-8") == "old summary\n"


def test_lock_prevents_corruption(tmp_path: Path) -> None:
    lock_path = tmp_path / "summary.lock"
    second_acquired = threading.Event()

    def _acquire_lock() -> None:
        with file_lock(lock_path):
            second_acquired.set()

    with file_lock(lock_path):
        thread = threading.Thread(target=_acquire_lock)
        thread.start()
        time.sleep(0.1)
        assert not second_acquired.is_set()

    thread.join(timeout=1)
    assert second_acquired.is_set()

