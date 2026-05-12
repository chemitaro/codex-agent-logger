import json
from pathlib import Path

from codex_logger.notification_event import from_permission_request


def test_permission_request_event_uses_session_as_thread_key() -> None:
    raw_payload = json.dumps(
        {
            "session_id": "session-1",
            "turn_id": "turn-1",
            "cwd": "/tmp/project",
            "tool_name": "Bash",
            "tool_input": {
                "command": "git status",
                "description": "Need escalated execution",
                "justification": "Check repository state",
            },
        }
    )

    notify_payload = json.loads(from_permission_request(raw_payload).to_notify_payload_json())

    assert notify_payload["type"] == "permission-request"
    assert notify_payload["thread-id"] == "session-1"
    assert notify_payload["turn-id"] == "turn-1"
    assert notify_payload["cwd"] == "/tmp/project"
    assert "Codex approval required" in notify_payload["last-assistant-message"]
    assert "Need escalated execution" in notify_payload["last-assistant-message"]
    assert "git status" in notify_payload["last-assistant-message"]
    assert "Check repository state" in notify_payload["last-assistant-message"]


def test_permission_request_event_falls_back_to_process_cwd() -> None:
    notify_payload = json.loads(
        from_permission_request("{}", fallback_cwd=Path("/tmp/fallback")).to_notify_payload_json()
    )

    assert notify_payload["type"] == "permission-request"
    assert notify_payload["cwd"] == "/tmp/fallback"
    assert notify_payload["last-assistant-message"].startswith("Codex approval required")
