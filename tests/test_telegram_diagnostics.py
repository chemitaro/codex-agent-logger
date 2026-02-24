import json
from pathlib import Path
import urllib.request

import pytest

from codex_logger.telegram import send_last_message_best_effort


def _payload(
    cwd: Path,
    *,
    thread_id: str = "thread-1",
    turn_id: str = "turn-1",
    last_message: str = "hello",
) -> str:
    return json.dumps(
        {
            "type": "agent-turn-complete",
            "thread-id": thread_id,
            "turn-id": turn_id,
            "cwd": str(cwd),
            "last-assistant-message": last_message,
        }
    )


def test_writes_diagnostics_when_env_missing_and_does_not_call_api(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    base_cwd = tmp_path / "project"
    base_dir = base_cwd / ".codex-log"
    base_dir.mkdir(parents=True)

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "SECRET_TOKEN")
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    calls: list[urllib.request.Request] = []

    def _urlopen(req: urllib.request.Request, timeout: int = 10) -> object:  # pragma: no cover
        calls.append(req)
        raise AssertionError("urlopen should not be called when env is missing")

    monkeypatch.setattr("codex_logger.telegram.urllib.request.urlopen", _urlopen)

    raw_payload = _payload(base_cwd, last_message="SENSITIVE_OUTPUT")
    send_last_message_best_effort(
        raw_payload, base_cwd=base_cwd, base_dir=base_dir, event_stem="event-1"
    )

    assert calls == []

    diag_path = base_dir / "telegram-errors" / "event-1.md"
    diag = diag_path.read_text(encoding="utf-8")
    assert "outcome" in diag
    assert "skipped" in diag.lower()
    assert "env" in diag.lower()
    assert "SECRET_TOKEN" not in diag
    assert "SENSITIVE_OUTPUT" not in diag


def test_writes_diagnostics_when_api_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    base_cwd = tmp_path / "project"
    base_dir = base_cwd / ".codex-log"
    base_dir.mkdir(parents=True)

    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    (base_cwd / ".env").write_text(
        "TELEGRAM_BOT_TOKEN=SECRET_TOKEN\nTELEGRAM_CHAT_ID=12345\n", encoding="utf-8"
    )

    class _FakeResponse:
        def __init__(self, payload: dict) -> None:
            self._payload = payload

        def read(self) -> bytes:
            return json.dumps(self._payload).encode("utf-8")

        def __enter__(self) -> "_FakeResponse":
            return self

        def __exit__(self, *_exc: object) -> None:
            return None

    calls: list[urllib.request.Request] = []

    def _urlopen(req: urllib.request.Request, timeout: int = 10) -> _FakeResponse:
        calls.append(req)
        if req.full_url.endswith("/createForumTopic"):
            return _FakeResponse({"ok": True, "result": {"message_thread_id": 777}})
        if req.full_url.endswith("/sendMessage"):
            return _FakeResponse({"ok": False, "description": "send failed"})
        raise AssertionError(f"unexpected url: {req.full_url}")

    monkeypatch.setattr("codex_logger.telegram.urllib.request.urlopen", _urlopen)

    raw_payload = _payload(base_cwd, last_message="SENSITIVE_OUTPUT")
    send_last_message_best_effort(
        raw_payload, base_cwd=base_cwd, base_dir=base_dir, event_stem="event-2"
    )

    assert [c.full_url.split("/")[-1] for c in calls] == ["createForumTopic", "sendMessage"]

    diag_path = base_dir / "telegram-errors" / "event-2.md"
    diag = diag_path.read_text(encoding="utf-8")
    assert "failed" in diag.lower()
    assert "sendmessage" in diag.lower()
    assert "1/1" in diag
    assert "SECRET_TOKEN" not in diag
    assert "SENSITIVE_OUTPUT" not in diag


def test_does_not_write_diagnostics_on_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    base_cwd = tmp_path / "project"
    base_dir = base_cwd / ".codex-log"
    base_dir.mkdir(parents=True)

    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    (base_cwd / ".env").write_text(
        "TELEGRAM_BOT_TOKEN=SECRET_TOKEN\nTELEGRAM_CHAT_ID=12345\n", encoding="utf-8"
    )

    class _FakeResponse:
        def __init__(self, payload: dict) -> None:
            self._payload = payload

        def read(self) -> bytes:
            return json.dumps(self._payload).encode("utf-8")

        def __enter__(self) -> "_FakeResponse":
            return self

        def __exit__(self, *_exc: object) -> None:
            return None

    def _urlopen(req: urllib.request.Request, timeout: int = 10) -> _FakeResponse:
        if req.full_url.endswith("/createForumTopic"):
            return _FakeResponse({"ok": True, "result": {"message_thread_id": 777}})
        if req.full_url.endswith("/sendMessage"):
            return _FakeResponse({"ok": True, "result": {"message_id": 1}})
        raise AssertionError(f"unexpected url: {req.full_url}")

    monkeypatch.setattr("codex_logger.telegram.urllib.request.urlopen", _urlopen)

    raw_payload = _payload(base_cwd)
    send_last_message_best_effort(
        raw_payload, base_cwd=base_cwd, base_dir=base_dir, event_stem="event-3"
    )

    assert not (base_dir / "telegram-errors" / "event-3.md").exists()

