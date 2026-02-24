import json
from pathlib import Path
import urllib.request

import pytest

from codex_logger.telegram import send_last_message_best_effort, topic_name


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *_exc: object) -> None:
        return None


def test_create_topic_and_send_updates_mapping(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    base_cwd = tmp_path / "project"
    base_dir = base_cwd / ".codex-log"
    base_dir.mkdir(parents=True)

    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    (base_cwd / ".env").write_text(
        "TELEGRAM_BOT_TOKEN=TEST_TOKEN\nTELEGRAM_CHAT_ID=12345\n", encoding="utf-8"
    )

    thread_id = "thread-1"
    last_message = "hello"
    raw_payload = json.dumps(
        {
            "type": "agent-turn-complete",
            "thread-id": thread_id,
            "turn-id": "turn-1",
            "cwd": str(base_cwd),
            "last-assistant-message": last_message,
        }
    )

    calls: list[urllib.request.Request] = []

    def _urlopen(req: urllib.request.Request, timeout: int = 10) -> _FakeResponse:
        calls.append(req)
        if req.full_url.endswith("/createForumTopic"):
            body = json.loads(req.data.decode("utf-8"))
            assert body["chat_id"] == "12345"
            assert body["name"] == topic_name(base_cwd, thread_id)
            return _FakeResponse({"ok": True, "result": {"message_thread_id": 777}})
        if req.full_url.endswith("/sendMessage"):
            body = json.loads(req.data.decode("utf-8"))
            assert body["chat_id"] == "12345"
            assert body["message_thread_id"] == 777
            assert body["text"] == "(1/1)\\nhello"
            return _FakeResponse({"ok": True, "result": {"message_id": 1}})
        raise AssertionError(f"unexpected url: {req.full_url}")

    monkeypatch.setattr("codex_logger.telegram.urllib.request.urlopen", _urlopen)

    send_last_message_best_effort(raw_payload, base_cwd=base_cwd, base_dir=base_dir)

    mapping_path = base_dir / "telegram-topics.json"
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    assert mapping == {thread_id: 777}

    # 1x createForumTopic + 1x sendMessage
    assert [c.full_url.split("/")[-1] for c in calls] == ["createForumTopic", "sendMessage"]


def test_mapping_reuses_existing_topic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    base_cwd = tmp_path / "project"
    base_dir = base_cwd / ".codex-log"
    (base_dir / "logs").mkdir(parents=True)

    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    (base_cwd / ".env").write_text(
        "TELEGRAM_BOT_TOKEN=TEST_TOKEN\nTELEGRAM_CHAT_ID=12345\n", encoding="utf-8"
    )

    thread_id = "thread-1"
    (base_dir / "telegram-topics.json").write_text(
        json.dumps({thread_id: 777}, indent=2) + "\n",
        encoding="utf-8",
    )

    raw_payload = json.dumps(
        {
            "type": "agent-turn-complete",
            "thread-id": thread_id,
            "turn-id": "turn-1",
            "cwd": str(base_cwd),
            "last-assistant-message": "hello",
        }
    )

    calls: list[urllib.request.Request] = []

    def _urlopen(req: urllib.request.Request, timeout: int = 10) -> _FakeResponse:
        calls.append(req)
        assert req.full_url.endswith("/sendMessage")
        return _FakeResponse({"ok": True, "result": {"message_id": 1}})

    monkeypatch.setattr("codex_logger.telegram.urllib.request.urlopen", _urlopen)

    send_last_message_best_effort(raw_payload, base_cwd=base_cwd, base_dir=base_dir)
    assert len(calls) == 1
