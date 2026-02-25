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
    assert content.index("<sub>2026-02-24 09:53:12.001Z</sub>") < content.index(
        "<sub>2026-02-24 09:53:12.002Z</sub>"
    )
    assert first_log.name not in content
    assert second_log.name not in content
    assert "ev-a" not in content
    assert "ev-b" not in content
    assert "- type:" not in content
    assert "- thread-id:" not in content
    assert "- turn-id:" not in content
    assert "- cwd:" not in content
    assert "**User**" in content
    assert "**Assistant (thread-1)**" in content
    assert "**Assistant**" in content
    assert "> Hello" not in content
    assert "> Show me code" in content
    assert "**Assistant (thread-1)**\nHere is **code**" in content
    assert "\n> Here is **code**" not in content
    assert "> Need thread id" in content


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

    assert "<sub>2026-02-24 09:53:12.001Z</sub>" in content
    assert "**User**" in content
    assert "> line-1\n> line-2" in content
    assert "**Assistant (thread-ml)**" in content
    assert "**Assistant (thread-ml)**\nanswer-1\n\nanswer-3" in content
    assert "\n> answer-1\n> \n> answer-3" not in content


def test_missing_or_invalid_messages_are_rendered_best_effort(tmp_path: Path) -> None:
    base_dir = tmp_path / ".codex-log"
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(parents=True)

    missing_log = logs_dir / "2026-02-24T09-53-12.001Z_ev-missing.json"
    empty_log = logs_dir / "2026-02-24T09-53-12.002Z_ev-empty.json"
    invalid_log = logs_dir / "2026-02-24T09-53-12.003Z_ev-invalid.json"
    empty_element_log = logs_dir / "2026-02-24T09-53-12.004Z_ev-empty-element.json"
    last_empty_log = logs_dir / "2026-02-24T09-53-12.005Z_ev-last-empty.json"
    mixed_type_log = logs_dir / "2026-02-24T09-53-12.006Z_ev-mixed-type.json"

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
    last_empty_log.write_text(
        json.dumps(
            {
                "type": "agent-turn-complete",
                "input-messages": ["previous", ""],
                "last-assistant-message": "ok-last",
            }
        ),
        encoding="utf-8",
    )
    mixed_type_log.write_text(
        json.dumps(
            {
                "type": "agent-turn-complete",
                "input-messages": ["ok", 1],
                "last-assistant-message": "assistant-ok",
            }
        ),
        encoding="utf-8",
    )

    summary_path = rebuild_summary(base_dir)
    content = summary_path.read_text(encoding="utf-8")

    def _section(timestamp: str) -> str:
        marker = f"<sub>{timestamp}</sub>\n"
        start = content.index(marker) + len(marker)
        end = content.find("\n<sub>", start)
        return content[start:] if end == -1 else content[start:end]

    missing_section = _section("2026-02-24 09:53:12.001Z")
    assert "**User**\n> <missing>" in missing_section
    assert "**Assistant (thread-missing)**\n<missing>" in missing_section

    empty_section = _section("2026-02-24 09:53:12.002Z")
    assert "**User**\n> <missing>" in empty_section
    assert "**Assistant**\n<missing>" in empty_section

    invalid_section = _section("2026-02-24 09:53:12.003Z")
    assert "**User**\n> <invalid>" in invalid_section
    assert "**Assistant**\n<invalid>" in invalid_section

    empty_element_section = _section("2026-02-24 09:53:12.004Z")
    assert "**User**\n> next" in empty_element_section
    assert "**Assistant**\nok" in empty_element_section

    last_empty_section = _section("2026-02-24 09:53:12.005Z")
    assert "**User**\n> <missing>" in last_empty_section
    assert "**Assistant**\nok-last" in last_empty_section

    mixed_type_section = _section("2026-02-24 09:53:12.006Z")
    assert "**User**\n> <invalid>" in mixed_type_section
    assert "**Assistant**\nassistant-ok" in mixed_type_section


def test_invalid_json_is_recorded(tmp_path: Path) -> None:
    base_dir = tmp_path / ".codex-log"
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(parents=True)

    valid_log = logs_dir / "2026-02-24T09-53-12.001Z_ev-valid.json"
    invalid_log = logs_dir / "2026-02-24T09-53-12.002Z_ev-invalid.json"

    valid_log.write_text(
        json.dumps(
            {
                "thread-id": "thread-2",
                "input-messages": ["valid-input"],
                "last-assistant-message": "valid-answer",
            }
        ),
        encoding="utf-8",
    )
    invalid_log.write_text('{"type": "agent-turn-complete"', encoding="utf-8")

    summary_path = rebuild_summary(base_dir)
    content = summary_path.read_text(encoding="utf-8")

    assert "<sub>2026-02-24 09:53:12.001Z</sub>" in content
    assert "<sub>2026-02-24 09:53:12.002Z</sub>" in content
    assert "**User**\n> valid-input" in content
    assert "**Assistant (thread-2)**\nvalid-answer" in content
    assert "\n> valid-answer" not in content
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
