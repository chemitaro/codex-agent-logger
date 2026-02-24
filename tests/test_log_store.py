import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pytest

from codex_logger.ids import event_id
from codex_logger.log_store import save_raw_payload
from codex_logger.payload import parse_best_effort


def _fixed_now() -> datetime:
    return datetime(2026, 2, 24, 9, 53, 12, 345000, tzinfo=timezone.utc)


def _payload(
    cwd: Path,
    *,
    thread_id: str = "thread-1",
    turn_id: str = "turn-1",
    event_type: str = "agent-turn-complete",
) -> str:
    return json.dumps(
        {
            "type": event_type,
            "cwd": str(cwd),
            "thread-id": thread_id,
            "turn-id": turn_id,
        }
    )


def test_save_raw_payload_creates_file(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    raw_payload = _payload(workspace)

    meta = parse_best_effort(raw_payload)
    saved_path = save_raw_payload(
        raw_payload, meta.cwd, meta.thread_id, meta.turn_id, now_utc=_fixed_now
    )

    assert saved_path.exists()
    assert saved_path.read_bytes() == raw_payload.encode("utf-8")


def test_save_raw_payload_creates_dirs(tmp_path: Path) -> None:
    workspace = tmp_path / "missing" / "workspace"
    raw_payload = _payload(workspace)

    meta = parse_best_effort(raw_payload)
    save_raw_payload(raw_payload, meta.cwd, meta.thread_id, meta.turn_id, now_utc=_fixed_now)

    codex_log_dir = workspace.resolve(strict=False) / ".codex-log"
    logs_dir = codex_log_dir / "logs"
    assert codex_log_dir.is_dir()
    assert logs_dir.is_dir()


def test_event_id_and_filename_pattern(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    raw_payload = _payload(workspace, thread_id="t1", turn_id="u1")

    meta = parse_best_effort(raw_payload)
    saved_path = save_raw_payload(
        raw_payload, meta.cwd, meta.thread_id, meta.turn_id, now_utc=_fixed_now
    )

    expected_event_id = event_id("t1", "u1")
    assert saved_path.name == f"2026-02-24T09-53-12.345Z_{expected_event_id}.json"
    assert re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}\.\d{3}Z_ev-[0-9a-f]{12}\.json",
        saved_path.name,
    )


def test_save_raw_payload_collision_adds_suffix(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    raw_payload_1 = _payload(
        workspace, thread_id="same-thread", turn_id="same-turn", event_type="event-1"
    )
    raw_payload_2 = _payload(
        workspace, thread_id="same-thread", turn_id="same-turn", event_type="event-2"
    )

    meta_1 = parse_best_effort(raw_payload_1)
    meta_2 = parse_best_effort(raw_payload_2)

    first_path = save_raw_payload(
        raw_payload_1, meta_1.cwd, meta_1.thread_id, meta_1.turn_id, now_utc=_fixed_now
    )
    second_path = save_raw_payload(
        raw_payload_2, meta_2.cwd, meta_2.thread_id, meta_2.turn_id, now_utc=_fixed_now
    )

    assert first_path.name.endswith(".json")
    assert second_path.name.endswith("__01.json")
    assert first_path.read_bytes() == raw_payload_1.encode("utf-8")
    assert second_path.read_bytes() == raw_payload_2.encode("utf-8")


def test_missing_fields_warns_and_saves(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    raw_payload = json.dumps({"type": "agent-turn-complete"})

    meta = parse_best_effort(raw_payload)
    saved_path = save_raw_payload(
        raw_payload, meta.cwd, meta.thread_id, meta.turn_id, now_utc=_fixed_now
    )

    expected_logs_dir = tmp_path.resolve(strict=False) / ".codex-log" / "logs"
    assert saved_path.parent == expected_logs_dir

    stderr = capsys.readouterr().err
    assert "warn:" in stderr
    assert "cwd" in stderr
    assert "thread-id" in stderr
    assert "turn-id" in stderr

    expected_event_id = event_id(None, None)
    assert expected_event_id in saved_path.name
    assert saved_path.read_bytes() == raw_payload.encode("utf-8")


def test_invalid_json_warns_and_saves(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    raw_payload = '{"type": "agent-turn-complete"'

    meta = parse_best_effort(raw_payload)
    saved_path = save_raw_payload(
        raw_payload, meta.cwd, meta.thread_id, meta.turn_id, now_utc=_fixed_now
    )

    expected_logs_dir = tmp_path.resolve(strict=False) / ".codex-log" / "logs"
    assert saved_path.parent == expected_logs_dir

    stderr = capsys.readouterr().err
    assert "warn:" in stderr
    assert "valid json" in stderr.lower()

    expected_event_id = event_id(None, None)
    assert expected_event_id in saved_path.name
    assert saved_path.read_bytes() == raw_payload.encode("utf-8")


def test_chmod_failure_warns_but_saves(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    raw_payload = _payload(workspace)

    def _fail_chmod(*_args: object, **_kwargs: object) -> None:
        raise PermissionError("chmod denied")

    monkeypatch.setattr("codex_logger.log_store.os.chmod", _fail_chmod)

    meta = parse_best_effort(raw_payload)
    saved_path = save_raw_payload(
        raw_payload, meta.cwd, meta.thread_id, meta.turn_id, now_utc=_fixed_now
    )

    stderr = capsys.readouterr().err
    assert "warn:" in stderr
    assert "chmod" in stderr.lower()
    assert saved_path.exists()
    assert saved_path.read_bytes() == raw_payload.encode("utf-8")


def test_incomplete_file_is_removed_on_write_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    raw_payload = _payload(workspace, thread_id="t1", turn_id="u1")

    class _FailWriter:
        def __init__(self, fd: int):
            self._fd = fd

        def __enter__(self) -> "_FailWriter":
            return self

        def __exit__(self, *_exc: object) -> None:
            import os

            try:
                os.close(self._fd)
            except OSError:
                pass

        def write(self, _data: bytes) -> int:  # pragma: no cover
            raise OSError("disk full")

    monkeypatch.setattr("codex_logger.log_store.os.fdopen", lambda fd, _mode: _FailWriter(fd))

    meta = parse_best_effort(raw_payload)
    expected_name = f"2026-02-24T09-53-12.345Z_{event_id('t1', 'u1')}.json"
    expected_path = (
        workspace.resolve(strict=False) / ".codex-log" / "logs" / expected_name
    )

    with pytest.raises(OSError):
        save_raw_payload(raw_payload, meta.cwd, meta.thread_id, meta.turn_id, now_utc=_fixed_now)

    assert not expected_path.exists()
