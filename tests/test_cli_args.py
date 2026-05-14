from pathlib import Path
from io import StringIO
import json

import pytest

from codex_logger.cli import main, parse_args


def test_help_exits_zero() -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["--help"])
    assert excinfo.value.code == 0


def test_version_exits_zero_without_payload() -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])
    assert excinfo.value.code == 0


def test_telegram_and_version_exits_zero_without_payload() -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["--telegram", "--version"])
    assert excinfo.value.code == 0


def test_normal_run_without_payload_is_usage_error(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main([])
    assert excinfo.value.code != 0

    stderr = capsys.readouterr().err
    assert "usage:" in stderr


def test_notify_subcommand_accepts_payload_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    saved_path = Path("/tmp/workspace/.codex-log/logs/raw-payload.json")
    monkeypatch.setattr(
        "codex_logger.cli.log_store.save_raw_payload",
        lambda *_args, **_kwargs: saved_path,
    )
    monkeypatch.setattr(
        "codex_logger.cli.summary.rebuild_summary",
        lambda *_args, **_kwargs: saved_path.parent.parent / "summary.md",
    )
    telegram_payloads: list[str] = []
    monkeypatch.setattr(
        "codex_logger.cli.telegram.send_last_message_best_effort",
        lambda raw_payload, **_kwargs: telegram_payloads.append(raw_payload),
    )

    raw_payload = (
        '{"type":"agent-turn-complete","thread-id":"thread-1",'
        '"last-assistant-message":"done"}'
    )
    args = parse_args(["notify", "--telegram", raw_payload])

    assert args.command == "notify"
    assert args.payload_json == raw_payload
    assert args.telegram is True

    assert main(["notify", "--telegram", raw_payload]) == 0
    assert telegram_payloads == [raw_payload]


def test_permission_request_subcommand_reads_stdin_as_notification_event(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    saved_path = Path("/tmp/workspace/.codex-log/logs/raw-payload.json")
    saved_payloads: list[str] = []

    def _save_raw_payload(raw_payload: str, *_args: object, **_kwargs: object) -> Path:
        saved_payloads.append(raw_payload)
        return saved_path

    monkeypatch.setattr("codex_logger.cli.log_store.save_raw_payload", _save_raw_payload)
    monkeypatch.setattr(
        "codex_logger.cli.summary.rebuild_summary",
        lambda *_args, **_kwargs: saved_path.parent.parent / "summary.md",
    )
    telegram_payloads: list[str] = []
    monkeypatch.setattr(
        "codex_logger.cli.telegram.send_last_message_best_effort",
        lambda raw_payload, **_kwargs: telegram_payloads.append(raw_payload),
    )

    stdin_payload = (
        '{"session_id":"thread-1","turn_id":"turn-1","cwd":"/tmp/workspace",'
        '"tool_name":"Bash","tool_input":{"command":"git status"}}'
    )

    assert main(
        ["permission-request", "--telegram"],
        stdin=StringIO(stdin_payload),
    ) == 0

    assert len(saved_payloads) == 1
    assert saved_payloads == telegram_payloads
    assert '"type":"permission-request"' in saved_payloads[0]
    assert '"thread-id":"thread-1"' in saved_payloads[0]
    assert '"turn-id":"turn-1"' in saved_payloads[0]
    assert "Codex approval required" in saved_payloads[0]
    assert "git status" in saved_payloads[0]


def test_notify_subcommand_skips_internal_title_telegram_but_saves_log(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    saved_path = tmp_path / ".codex-log" / "logs" / "raw-payload.json"
    saved_payloads: list[str] = []

    def _save_raw_payload(raw_payload: str, *_args: object, **_kwargs: object) -> Path:
        saved_payloads.append(raw_payload)
        return saved_path

    rebuilt_dirs: list[Path] = []

    def _rebuild_summary(base_dir: Path) -> Path:
        rebuilt_dirs.append(base_dir)
        return base_dir / "summary.md"

    monkeypatch.setattr("codex_logger.cli.log_store.save_raw_payload", _save_raw_payload)
    monkeypatch.setattr("codex_logger.cli.summary.rebuild_summary", _rebuild_summary)
    telegram_payloads: list[str] = []
    monkeypatch.setattr(
        "codex_logger.cli.telegram.send_last_message_best_effort",
        lambda raw_payload, **_kwargs: telegram_payloads.append(raw_payload),
    )

    raw_payload = json.dumps(
        {
            "type": "agent-turn-complete",
            "thread-id": "thread-1",
            "turn-id": "turn-1",
            "cwd": "/tmp/workspace",
            "input-messages": [
                "Generate a concise UI title for this task. Fill the structured title field."
            ],
            "last-assistant-message": json.dumps({"title": "defaultサブエージェント確認"}),
        }
    )

    assert main(["notify", "--telegram", raw_payload]) == 0

    stderr = capsys.readouterr().err
    assert "telegram delivery skipped: internal turn (desktop-title-generation)" in stderr
    assert saved_payloads == [raw_payload]
    assert rebuilt_dirs == [saved_path.parent.parent]
    assert telegram_payloads == []

    diagnostics = saved_path.parent.parent / "telegram-errors" / "raw-payload.md"
    assert diagnostics.read_text() == (
        "# Telegram delivery diagnostics\n"
        "\n"
        "- outcome: skipped\n"
        "- reason: internal Codex helper turn\n"
        "- event: raw-payload\n"
        "- thread-id: thread-1\n"
        "- turn-id: turn-1\n"
        "- rule: desktop-title-generation\n"
        "- assistant-json-keys: title\n"
        "\n"
        "## Hints\n"
        "- Codex Desktop の内部 helper turn と判定されたため Telegram 送信を抑止しました。\n"
        "- raw payload は .codex-log/logs/ に保存されています。\n"
    )


def test_notify_subcommand_sends_normal_json_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    saved_path = Path("/tmp/workspace/.codex-log/logs/raw-payload.json")
    monkeypatch.setattr(
        "codex_logger.cli.log_store.save_raw_payload",
        lambda *_args, **_kwargs: saved_path,
    )
    monkeypatch.setattr(
        "codex_logger.cli.summary.rebuild_summary",
        lambda *_args, **_kwargs: saved_path.parent.parent / "summary.md",
    )
    telegram_payloads: list[str] = []
    monkeypatch.setattr(
        "codex_logger.cli.telegram.send_last_message_best_effort",
        lambda raw_payload, **_kwargs: telegram_payloads.append(raw_payload),
    )

    raw_payload = json.dumps(
        {
            "type": "agent-turn-complete",
            "thread-id": "thread-1",
            "input-messages": ["Return the response as JSON."],
            "last-assistant-message": json.dumps({"title": "User requested title"}),
        }
    )

    assert main(["notify", "--telegram", raw_payload]) == 0
    assert telegram_payloads == [raw_payload]


def test_permission_request_subcommand_bypasses_internal_turn_filter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    saved_path = Path("/tmp/workspace/.codex-log/logs/raw-payload.json")
    monkeypatch.setattr(
        "codex_logger.cli.log_store.save_raw_payload",
        lambda *_args, **_kwargs: saved_path,
    )
    monkeypatch.setattr(
        "codex_logger.cli.summary.rebuild_summary",
        lambda *_args, **_kwargs: saved_path.parent.parent / "summary.md",
    )
    telegram_payloads: list[str] = []
    monkeypatch.setattr(
        "codex_logger.cli.telegram.send_last_message_best_effort",
        lambda raw_payload, **_kwargs: telegram_payloads.append(raw_payload),
    )

    stdin_payload = json.dumps(
        {
            "session_id": "thread-1",
            "turn_id": "turn-1",
            "cwd": "/tmp/workspace",
            "tool_name": "Bash",
            "tool_input": {
                "command": "echo ok",
                "description": "Generate a concise UI title for this task.",
            },
        }
    )

    assert main(["permission-request", "--telegram"], stdin=StringIO(stdin_payload)) == 0
    assert len(telegram_payloads) == 1


@pytest.mark.parametrize(
    "argv",
    [
        ['{"type":"agent-turn-complete"}'],
        ["--telegram", '{"type":"agent-turn-complete"}'],
    ],
)
def test_payload_json_with_or_without_telegram(
    argv: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    saved_path = Path("/tmp/workspace/.codex-log/logs/raw-payload.json")
    monkeypatch.setattr(
        "codex_logger.cli.log_store.save_raw_payload",
        lambda *_args, **_kwargs: saved_path,
    )
    rebuilt: list[Path] = []
    monkeypatch.setattr(
        "codex_logger.cli.summary.rebuild_summary",
        lambda base_dir: rebuilt.append(base_dir),
    )
    telegram_calls: list[bool] = []
    monkeypatch.setattr(
        "codex_logger.cli.telegram.send_last_message_best_effort",
        lambda *_args, **_kwargs: telegram_calls.append(True),
    )

    args = parse_args(argv)
    assert args.payload_json == '{"type":"agent-turn-complete"}'
    assert args.telegram == ("--telegram" in argv)

    assert main(argv) == 0
    assert rebuilt == [saved_path.parent.parent]
    assert telegram_calls == ([True] if "--telegram" in argv else [])


@pytest.mark.parametrize(
    "argv",
    [
        ["--unknown"],
        ['{"type":"agent-turn-complete"}', "extra"],
    ],
)
def test_unknown_or_extra_args_are_usage_error(
    argv: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(argv)
    assert excinfo.value.code != 0

    stderr = capsys.readouterr().err
    assert "usage:" in stderr
